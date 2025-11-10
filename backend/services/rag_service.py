"""
Сервис RAG (Retrieval-Augmented Generation)
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterable
import logging
import hashlib

from sentence_transformers import SentenceTransformer
from qdrant_client.models import PointStruct

from backend.config.settings import settings
from backend.services.qdrant_service import qdrant_service
from backend.core.model_manager import model_manager
from backend.services.document_parser import get_document_parser, DocumentChunk

logger = logging.getLogger(__name__)


class RAGService:
    """Сервис для RAG - поиск релевантных документов и генерация ответов"""
    
    def __init__(self):
        self.embedding_model = None
        self._load_embedding_model()
        self.document_parser = get_document_parser()
        self.batch_size = settings.RAG_BATCH_SIZE
        self.parallel_workers = settings.RAG_PARALLEL_WORKERS
    
    def _load_embedding_model(self):
        """Загрузка модели для эмбеддингов"""
        try:
            model_name = settings.RAG_EMBEDDING_MODEL
            logger.info(f"Loading embedding model: {model_name}")
            self.embedding_model = SentenceTransformer(model_name)
            vector_size = self.embedding_model.get_sentence_embedding_dimension()
            qdrant_service.init_collection(vector_size=vector_size)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def create_embedding(self, text: str) -> List[float]:
        """Создание эмбеддинга для текста"""
        if not self.embedding_model:
            raise RuntimeError("Embedding model not loaded")
        
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def _build_point(
        self,
        document_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PointStruct:
        embedding = self.create_embedding(text)
        payload = {
            "text": text,
            "document_id": document_id,
        }
        if metadata:
            payload.update(metadata)

        return PointStruct(
            id=document_id,
            vector=embedding,
            payload=payload,
        )

    def index_document(
        self,
        document_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Индексация документа
        
        Args:
            document_id: Уникальный ID документа
            text: Текст документа
            metadata: Метаданные документа
        """
        try:
            # Создание эмбеддинга
            point = self._build_point(
                document_id=document_id,
                text=text,
                metadata=metadata,
            )

            # Добавление в Qdrant
            qdrant_service.add_documents_batch([point])
            
            logger.info(f"Document {document_id} indexed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to index document {document_id}: {e}")
            return False

    def index_document_chunks(
        self,
        document_id: str,
        chunks: List[DocumentChunk],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Индексация документа по чанкам."""
        success = True
        batch: List[PointStruct] = []
        for idx, chunk in enumerate(chunks):
            chunk_id = f"{document_id}::chunk::{idx}"
            chunk_metadata = {
                "chunk_index": idx,
                "document_id": document_id,
                "title": chunk.title,
                "level": chunk.level,
                "hierarchy": chunk.hierarchy,
            }
            if metadata:
                chunk_metadata.update(metadata)
            chunk_metadata.update(chunk.metadata)
            try:
                point = self._build_point(
                    document_id=chunk_id,
                    text=chunk.text,
                    metadata=chunk_metadata,
                )
                batch.append(point)
                if len(batch) >= self.batch_size:
                    qdrant_service.add_documents_batch(batch)
                    batch = []
            except Exception as exc:
                logger.error("Failed to build chunk %s: %s", chunk_id, exc)
                success = False
        if batch:
            qdrant_service.add_documents_batch(batch)
        return success

    def index_file(
        self,
        document_id: str,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None,
        chunk: bool = True,
    ) -> bool:
        """Извлечение текста из файла и индексация."""
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            if chunk:
                document_chunks = self.document_parser.extract_chunks_from_file(str(path))
                return self.index_document_chunks(
                    document_id=document_id,
                    chunks=document_chunks,
                    metadata=metadata,
                )
            text = self.document_parser.extract_plain_text(str(path))
            return self.index_document(
                document_id=document_id,
                text=text,
                metadata=metadata,
            )
        except Exception as exc:
            logger.error("Failed to index file %s: %s", file_path, exc)
            return False

    def index_files_parallel(
        self,
        items: Iterable[Dict[str, Any]],
        chunk: bool = True,
    ) -> Dict[str, Any]:
        """Параллельная индексация файлов."""
        items = list(items)
        if not items:
            return {"processed": 0, "succeeded": 0, "failed": []}

        results = {
            "processed": len(items),
            "succeeded": 0,
            "failed": [],
        }

        def _process(item: Dict[str, Any]) -> bool:
            return self.index_file(
                document_id=item["document_id"],
                file_path=item["file_path"],
                metadata=item.get("metadata"),
                chunk=chunk,
            )

        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            future_to_item = {executor.submit(_process, item): item for item in items}
            for future in as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    if future.result():
                        results["succeeded"] += 1
                    else:
                        results["failed"].append(item["document_id"])
                except Exception as exc:
                    logger.error("Parallel indexing failed for %s: %s", item, exc)
                    results["failed"].append(item["document_id"])
        return results
    
    def search(
        self,
        query: str,
        limit: int = 5,
        score_threshold: float = 0.7,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Поиск релевантных документов
        
        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов
            score_threshold: Минимальный порог релевантности
            filter_dict: Фильтры для поиска
            
        Returns:
            Список найденных документов с метаданными
        """
        try:
            # Создание эмбеддинга для запроса
            query_embedding = self.create_embedding(query)
            
            # Поиск в Qdrant
            results = qdrant_service.search(
                query_vector=query_embedding,
                limit=limit,
                filter_dict=filter_dict
            )
            
            # Фильтрация по порогу и форматирование результатов
            formatted_results = []
            for result in results:
                score = result.score
                if score >= score_threshold:
                    formatted_results.append({
                        "document_id": result.payload.get("document_id"),
                        "text": result.payload.get("text"),
                        "score": score,
                        "metadata": {k: v for k, v in result.payload.items() 
                                   if k not in ["document_id", "text"]}
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def generate_answer(
        self,
        query: str,
        context_documents: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 512,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Генерация ответа на основе найденных документов
        
        Args:
            query: Вопрос пользователя
            context_documents: Контекстные документы (если None, выполняется поиск)
            max_tokens: Максимальное количество токенов
            temperature: Температура генерации
            
        Returns:
            Ответ с источниками
        """
        # Если документы не предоставлены, выполняем поиск
        if context_documents is None:
            context_documents = self.search(query, limit=5)
        
        # Формирование промпта с контекстом
        context_text = "\n\n".join([
            f"Документ {i+1}:\n{doc['text']}"
            for i, doc in enumerate(context_documents)
        ])
        
        prompt = f"""Используй следующие документы для ответа на вопрос.

Контекст:
{context_text}

Вопрос: {query}

Ответ (опирайся только на предоставленный контекст):"""
        
        # Генерация ответа через LLM
        answer = model_manager.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return {
            "answer": answer,
            "sources": [
                {
                    "document_id": doc.get("document_id"),
                    "score": doc.get("score"),
                    "metadata": doc.get("metadata", {})
                }
                for doc in context_documents
            ],
            "query": query
        }
    
    def rag_query(
        self,
        query: str,
        limit: int = 5,
        score_threshold: float = 0.7,
        max_tokens: int = 512,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Полный цикл RAG: поиск + генерация
        
        Args:
            query: Вопрос пользователя
            limit: Количество документов для поиска
            score_threshold: Минимальный порог релевантности
            max_tokens: Максимальное количество токенов
            temperature: Температура генерации
            
        Returns:
            Ответ с источниками
        """
        # Поиск релевантных документов
        documents = self.search(
            query=query,
            limit=limit,
            score_threshold=score_threshold
        )
        
        if not documents:
            return {
                "answer": "Не найдено релевантных документов для ответа на вопрос.",
                "sources": [],
                "query": query
            }
        
        # Генерация ответа
        return self.generate_answer(
            query=query,
            context_documents=documents,
            max_tokens=max_tokens,
            temperature=temperature
        )
    
    def delete_document(self, document_id: str) -> bool:
        """Удаление документа из индекса"""
        try:
            qdrant_service.delete_document(document_id)
            logger.info(f"Document {document_id} deleted from index")
            return True
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False


# Глобальный экземпляр RAG сервиса
rag_service = RAGService()

