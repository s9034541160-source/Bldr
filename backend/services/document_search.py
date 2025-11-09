"""
Сервис для полнотекстового и семантического поиска документов
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from backend.models.document import Document, DocumentMetadata
from backend.services.rag_service import rag_service
import logging

logger = logging.getLogger(__name__)


class DocumentSearchService:
    """Сервис для поиска документов"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def fulltext_search(
        self,
        query: str,
        document_type: Optional[str] = None,
        project_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Document]:
        """
        Полнотекстовый поиск документов
        
        Args:
            query: Поисковый запрос
            document_type: Фильтр по типу документа
            project_id: Фильтр по проекту
            limit: Максимальное количество результатов
            
        Returns:
            Список найденных документов
        """
        # Базовый запрос
        q = self.db.query(Document).filter(
            Document.is_active == True
        )
        
        # Фильтры
        if document_type:
            q = q.filter(Document.document_type == document_type)
        
        if project_id:
            q = q.filter(Document.project_id == project_id)
        
        # Поиск по названию и описанию
        search_terms = query.split()
        conditions = []
        for term in search_terms:
            conditions.append(Document.title.ilike(f"%{term}%"))
            conditions.append(Document.description.ilike(f"%{term}%"))
        
        if conditions:
            q = q.filter(or_(*conditions))
        
        # Поиск по метаданным
        metadata_conditions = []
        for term in search_terms:
            metadata_conditions.append(
                Document.metadata.cast(str).ilike(f"%{term}%")
            )
        
        if metadata_conditions:
            q = q.filter(or_(*metadata_conditions))
        
        return q.order_by(Document.created_at.desc()).limit(limit).all()
    
    def semantic_search(
        self,
        query: str,
        document_type: Optional[str] = None,
        project_id: Optional[int] = None,
        limit: int = 10,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Семантический поиск документов через RAG
        
        Args:
            query: Поисковый запрос
            document_type: Фильтр по типу документа
            project_id: Фильтр по проекту
            limit: Максимальное количество результатов
            score_threshold: Порог релевантности
            
        Returns:
            Список документов с оценкой релевантности
        """
        try:
            # Поиск через RAG
            rag_results = rag_service.search(
                query=query,
                limit=limit * 2,  # Берем больше для фильтрации
                score_threshold=score_threshold
            )
            
            # Извлечение ID документов из результатов RAG
            document_ids = []
            for result in rag_results:
                doc_id = result.get("document_id")
                if doc_id:
                    document_ids.append(doc_id)
            
            if not document_ids:
                return []
            
            # Получение документов из БД
            q = self.db.query(Document).filter(
                Document.id.in_(document_ids),
                Document.is_active == True
            )
            
            if document_type:
                q = q.filter(Document.document_type == document_type)
            
            if project_id:
                q = q.filter(Document.project_id == project_id)
            
            documents = q.all()
            
            # Создание результата с оценками релевантности
            results = []
            for doc in documents:
                # Находим соответствующую оценку из RAG результатов
                score = 0.0
                for rag_result in rag_results:
                    if rag_result.get("document_id") == doc.id:
                        score = rag_result.get("score", 0.0)
                        break
                
                results.append({
                    "document": doc,
                    "relevance_score": score,
                    "matched_text": rag_result.get("text", "")[:200] if rag_result else ""
                })
            
            # Сортировка по релевантности
            results.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return []
    
    def hybrid_search(
        self,
        query: str,
        document_type: Optional[str] = None,
        project_id: Optional[int] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Гибридный поиск: полнотекстовый + семантический
        
        Args:
            query: Поисковый запрос
            document_type: Фильтр по типу документа
            project_id: Фильтр по проекту
            limit: Максимальное количество результатов
            
        Returns:
            Список документов с комбинированной оценкой
        """
        # Полнотекстовый поиск
        fulltext_results = self.fulltext_search(
            query=query,
            document_type=document_type,
            project_id=project_id,
            limit=limit
        )
        
        # Семантический поиск
        semantic_results = self.semantic_search(
            query=query,
            document_type=document_type,
            project_id=project_id,
            limit=limit
        )
        
        # Объединение результатов
        document_scores = {}
        
        # Добавление результатов полнотекстового поиска
        for doc in fulltext_results:
            document_scores[doc.id] = {
                "document": doc,
                "fulltext_score": 1.0,
                "semantic_score": 0.0,
                "combined_score": 0.5
            }
        
        # Добавление результатов семантического поиска
        for result in semantic_results:
            doc_id = result["document"].id
            if doc_id in document_scores:
                document_scores[doc_id]["semantic_score"] = result["relevance_score"]
                document_scores[doc_id]["combined_score"] = (
                    document_scores[doc_id]["fulltext_score"] * 0.3 +
                    result["relevance_score"] * 0.7
                )
            else:
                document_scores[doc_id] = {
                    "document": result["document"],
                    "fulltext_score": 0.0,
                    "semantic_score": result["relevance_score"],
                    "combined_score": result["relevance_score"] * 0.7
                }
        
        # Сортировка по комбинированной оценке
        results = list(document_scores.values())
        results.sort(key=lambda x: x["combined_score"], reverse=True)
        
        return results[:limit]

