"""
Оптимизированный Enterprise RAG Trainer с batch upload, int8 quantization и Redis cache
"""
import os
import sys
import time
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import asyncio

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import numpy as np
import pandas as pd
from tqdm import tqdm
import redis
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, QuantizationConfig, ScalarQuantization
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModel

# Импорты для оптимизации
from .redis_cache import RedisCache
from .quantizer import Int8Quantizer

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DocumentChunk:
    """Структура чанка документа"""
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None
    quantized_embedding: Optional[np.ndarray] = None

class OptimizedEnterpriseRAGTrainer:
    """Оптимизированный Enterprise RAG Trainer"""
    
    def __init__(self, 
                 qdrant_url: str = "http://localhost:6333",
                 redis_url: str = "redis://localhost:6379",
                 batch_size: int = 64,
                 parallel_workers: int = 4,
                 use_quantization: bool = True,
                 cache_ttl: int = 3600):
        """
        Инициализация оптимизированного RAG trainer
        
        Args:
            qdrant_url: URL Qdrant сервера
            redis_url: URL Redis сервера
            batch_size: Размер батча для загрузки
            parallel_workers: Количество параллельных воркеров
            use_quantization: Использовать int8 quantization
            cache_ttl: TTL для кеша в секундах
        """
        self.qdrant_url = qdrant_url
        self.redis_url = redis_url
        self.batch_size = batch_size
        self.parallel_workers = parallel_workers
        self.use_quantization = use_quantization
        self.cache_ttl = cache_ttl
        
        # Инициализация компонентов
        self.qdrant_client = QdrantClient(url=qdrant_url)
        self.redis_cache = RedisCache(redis_url, cache_ttl)
        self.quantizer = Int8Quantizer() if use_quantization else None
        
        # Модель для эмбеддингов
        self.embedding_model = None
        self.tokenizer = None
        
        # Статистика
        self.stats = {
            "total_documents": 0,
            "total_chunks": 0,
            "upload_time": 0,
            "memory_peak": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    def load_embedding_model(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        """Загрузка модели для эмбеддингов"""
        try:
            logger.info(f"Загружаем модель эмбеддингов: {model_name}")
            self.embedding_model = SentenceTransformer(model_name)
            logger.info("✅ Модель эмбеддингов загружена")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки модели: {e}")
            raise
    
    def create_embeddings_batch(self, texts: List[str]) -> np.ndarray:
        """Создание эмбеддингов для батча текстов"""
        try:
            if not self.embedding_model:
                raise ValueError("Модель эмбеддингов не загружена")
            
            # Создаем эмбеддинги
            embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
            
            # Применяем quantization если включена
            if self.use_quantization and self.quantizer:
                embeddings = self.quantizer.quantize(embeddings)
            
            return embeddings
        except Exception as e:
            logger.error(f"❌ Ошибка создания эмбеддингов: {e}")
            raise
    
    def create_collection(self, collection_name: str, vector_size: int = 384):
        """Создание коллекции в Qdrant с оптимизированными параметрами"""
        try:
            # Параметры векторов
            vector_params = VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
            
            # Конфигурация quantization если включена
            quantization_config = None
            if self.use_quantization:
                quantization_config = QuantizationConfig(
                    scalar=ScalarQuantization(
                        type="int8",
                        quantile=0.99,
                        always_ram=True
                    )
                )
            
            # Создаем коллекцию
            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=vector_params,
                quantization_config=quantization_config
            )
            
            logger.info(f"✅ Коллекция {collection_name} создана с quantization={self.use_quantization}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания коллекции: {e}")
            raise
    
    def upload_chunks_batch(self, 
                           collection_name: str, 
                           chunks: List[DocumentChunk],
                           show_progress: bool = True) -> Dict[str, Any]:
        """Оптимизированная загрузка чанков батчами"""
        try:
            start_time = time.time()
            total_chunks = len(chunks)
            
            logger.info(f"🚀 Начинаем загрузку {total_chunks} чанков батчами по {self.batch_size}")
            
            # Разбиваем на батчи
            batches = [chunks[i:i + self.batch_size] for i in range(0, total_chunks, self.batch_size)]
            
            # Создаем progress bar
            progress_bar = tqdm(
                total=total_chunks,
                desc="Загрузка в Qdrant",
                unit="chunks",
                ncols=100
            ) if show_progress else None
            
            uploaded_count = 0
            memory_peak = 0
            
            # Загружаем батчи параллельно
            with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
                futures = []
                
                for batch_idx, batch in enumerate(batches):
                    future = executor.submit(self._upload_single_batch, collection_name, batch, batch_idx)
                    futures.append(future)
                
                # Обрабатываем результаты
                for future in as_completed(futures):
                    try:
                        batch_result = future.result()
                        uploaded_count += batch_result['uploaded']
                        memory_peak = max(memory_peak, batch_result['memory_peak'])
                        
                        if progress_bar:
                            progress_bar.update(batch_result['uploaded'])
                            progress_bar.set_postfix({
                                'Speed': f"{batch_result['speed']:.1f} docs/sec",
                                'Memory': f"{memory_peak:.1f} MB"
                            })
                            
                    except Exception as e:
                        logger.error(f"❌ Ошибка загрузки батча: {e}")
            
            if progress_bar:
                progress_bar.close()
            
            upload_time = time.time() - start_time
            speed = total_chunks / upload_time if upload_time > 0 else 0
            
            # Обновляем статистику
            self.stats.update({
                "total_chunks": total_chunks,
                "upload_time": upload_time,
                "memory_peak": memory_peak,
                "upload_speed": speed
            })
            
            logger.info(f"✅ Загрузка завершена: {uploaded_count} чанков за {upload_time:.2f}с ({speed:.1f} docs/sec)")
            
            return {
                "uploaded": uploaded_count,
                "time": upload_time,
                "speed": speed,
                "memory_peak": memory_peak
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки чанков: {e}")
            raise
    
    def _upload_single_batch(self, 
                           collection_name: str, 
                           batch: List[DocumentChunk], 
                           batch_idx: int) -> Dict[str, Any]:
        """Загрузка одного батча"""
        try:
            batch_start = time.time()
            
            # Создаем эмбеддинги для батча
            texts = [chunk.content for chunk in batch]
            embeddings = self.create_embeddings_batch(texts)
            
            # Создаем точки для Qdrant
            points = []
            for i, (chunk, embedding) in enumerate(zip(batch, embeddings)):
                point = PointStruct(
                    id=batch_idx * self.batch_size + i,
                    vector=embedding.tolist(),
                    payload={
                        "content": chunk.content,
                        "metadata": chunk.metadata
                    }
                )
                points.append(point)
            
            # Загружаем в Qdrant
            self.qdrant_client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            batch_time = time.time() - batch_start
            speed = len(batch) / batch_time if batch_time > 0 else 0
            
            # Оценка использования памяти
            memory_usage = self._estimate_memory_usage(embeddings)
            
            return {
                "uploaded": len(batch),
                "speed": speed,
                "memory_peak": memory_usage,
                "batch_time": batch_time
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки батча {batch_idx}: {e}")
            raise
    
    def _estimate_memory_usage(self, embeddings: np.ndarray) -> float:
        """Оценка использования памяти в MB"""
        try:
            # Размер массива в байтах
            array_size = embeddings.nbytes
            # Конвертируем в MB
            memory_mb = array_size / (1024 * 1024)
            return memory_mb
        except Exception:
            return 0.0
    
    def search_with_cache(self, 
                         collection_name: str, 
                         query: str, 
                         limit: int = 3) -> List[Dict[str, Any]]:
        """Поиск с использованием Redis кеша"""
        try:
            # Создаем ключ кеша
            cache_key = hashlib.md5(query.encode()).hexdigest()
            
            # Проверяем кеш
            cached_result = self.redis_cache.get(cache_key)
            if cached_result:
                self.stats["cache_hits"] += 1
                logger.info(f"✅ Cache hit для запроса: {query[:50]}...")
                return cached_result
            
            # Кеш промах - выполняем поиск
            self.stats["cache_misses"] += 1
            logger.info(f"🔍 Cache miss для запроса: {query[:50]}...")
            
            # Создаем эмбеддинг запроса
            query_embedding = self.create_embeddings_batch([query])[0]
            
            # Поиск в Qdrant
            search_result = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_embedding.tolist(),
                limit=limit
            )
            
            # Форматируем результат
            results = []
            for hit in search_result:
                results.append({
                    "content": hit.payload.get("content", ""),
                    "metadata": hit.payload.get("metadata", {}),
                    "score": hit.score
                })
            
            # Сохраняем в кеш
            self.redis_cache.set(cache_key, results)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Ошибка поиска с кешем: {e}")
            return []
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Получение статистики кеша"""
        try:
            total_requests = self.stats["cache_hits"] + self.stats["cache_misses"]
            hit_rate = (self.stats["cache_hits"] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "cache_hits": self.stats["cache_hits"],
                "cache_misses": self.stats["cache_misses"],
                "hit_rate": hit_rate,
                "total_requests": total_requests
            }
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики кеша: {e}")
            return {}
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Получение статистики производительности"""
        return {
            "total_documents": self.stats["total_documents"],
            "total_chunks": self.stats["total_chunks"],
            "upload_time": self.stats["upload_time"],
            "upload_speed": self.stats.get("upload_speed", 0),
            "memory_peak": self.stats["memory_peak"],
            "cache_stats": self.get_cache_stats()
        }
    
    def cleanup(self):
        """Очистка ресурсов"""
        try:
            if hasattr(self, 'redis_cache'):
                self.redis_cache.close()
            logger.info("✅ Ресурсы очищены")
        except Exception as e:
            logger.error(f"❌ Ошибка очистки: {e}")


# Функция для демонстрации оптимизации
def demonstrate_optimization():
    """Демонстрация оптимизации RAG системы"""
    print("=== ДЕМОНСТРАЦИЯ ОПТИМИЗАЦИИ RAG ===")
    
    # Создаем оптимизированный trainer
    trainer = OptimizedEnterpriseRAGTrainer(
        batch_size=64,
        parallel_workers=4,
        use_quantization=True
    )
    
    try:
        # Загружаем модель
        trainer.load_embedding_model()
        
        # Создаем коллекцию
        trainer.create_collection("optimized_test", vector_size=384)
        
        # Создаем тестовые чанки
        test_chunks = []
        for i in range(1000):
            chunk = DocumentChunk(
                content=f"Тестовый чанк номер {i} с содержимым для демонстрации оптимизации",
                metadata={"source": f"test_doc_{i}", "chunk_id": i}
            )
            test_chunks.append(chunk)
        
        # Загружаем чанки
        result = trainer.upload_chunks_batch("optimized_test", test_chunks)
        
        print(f"✅ Загрузка завершена:")
        print(f"  • Загружено: {result['uploaded']} чанков")
        print(f"  • Время: {result['time']:.2f}с")
        print(f"  • Скорость: {result['speed']:.1f} docs/sec")
        print(f"  • Память: {result['memory_peak']:.1f} MB")
        
        # Тестируем поиск с кешем
        query = "тестовый чанк"
        results = trainer.search_with_cache("optimized_test", query, limit=3)
        
        print(f"✅ Поиск завершен: найдено {len(results)} результатов")
        
        # Статистика
        stats = trainer.get_performance_stats()
        print(f"📊 Статистика:")
        print(f"  • Cache hit rate: {stats['cache_stats']['hit_rate']:.1f}%")
        print(f"  • Общая скорость: {stats['upload_speed']:.1f} docs/sec")
        
    finally:
        trainer.cleanup()


if __name__ == "__main__":
    demonstrate_optimization()
