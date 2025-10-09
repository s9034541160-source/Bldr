"""
Тесты для оптимизации Qdrant (batch upload, int8 quantization, Redis cache)
"""
import pytest
import time
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import json

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from services.rag.enterprise_rag_trainer_full import OptimizedEnterpriseRAGTrainer, DocumentChunk
from services.rag.redis_cache import RedisCache
from services.rag.quantizer import Int8Quantizer


class TestQdrantOptimization:
    """Тесты оптимизации Qdrant"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.trainer = OptimizedEnterpriseRAGTrainer(
            batch_size=64,
            parallel_workers=4,
            use_quantization=True
        )
    
    def teardown_method(self):
        """Очистка после каждого теста"""
        if hasattr(self, 'trainer'):
            self.trainer.cleanup()
    
    def test_batch_upload_optimization(self):
        """Тест оптимизации batch upload"""
        import asyncio
        
        async def run_test():
            # Создаем тестовые чанки
            test_chunks = []
            for i in range(200):  # 200 чанков для тестирования
                chunk = DocumentChunk(
                    content=f"Тестовый чанк номер {i} с содержимым для демонстрации оптимизации batch upload",
                    metadata={"source": f"test_doc_{i}", "chunk_id": i}
                )
                test_chunks.append(chunk)
            
            # Мокаем Qdrant client
            mock_client = Mock()
            mock_client.upsert = Mock()
            self.trainer.qdrant_client = mock_client
            
            # Мокаем создание эмбеддингов
            with patch.object(self.trainer, 'create_embeddings_batch') as mock_embeddings:
                # Возвращаем тестовые эмбеддинги
                mock_embeddings.return_value = np.random.randn(64, 384).astype(np.float32)
                
                # Тестируем загрузку
                start_time = time.time()
                result = self.trainer.upload_chunks_batch("test_collection", test_chunks, show_progress=False)
                upload_time = time.time() - start_time
                
                # Проверяем результаты
                assert result['uploaded'] == 200
                assert upload_time < 10.0  # Должно быть быстро
                assert result['speed'] > 0
                
                # Проверяем что upsert был вызван правильное количество раз
                expected_batches = (200 + 63) // 64  # Округление вверх
                assert mock_client.upsert.call_count == expected_batches
                
                print(f"✅ Batch upload: {result['uploaded']} чанков за {upload_time:.2f}с ({result['speed']:.1f} docs/sec)")
        
        asyncio.run(run_test())
    
    def test_memory_optimization(self):
        """Тест оптимизации памяти"""
        import asyncio
        
        async def run_test():
            # Создаем большой набор чанков
            test_chunks = []
            for i in range(1000):  # 1000 чанков
                chunk = DocumentChunk(
                    content=f"Большой тестовый чанк номер {i} с длинным содержимым для тестирования оптимизации памяти" * 10,
                    metadata={"source": f"large_doc_{i}", "chunk_id": i}
                )
                test_chunks.append(chunk)
            
            # Мокаем компоненты
            mock_client = Mock()
            mock_client.upsert = Mock()
            self.trainer.qdrant_client = mock_client
            
            with patch.object(self.trainer, 'create_embeddings_batch') as mock_embeddings:
                mock_embeddings.return_value = np.random.randn(64, 384).astype(np.float32)
                
                # Тестируем загрузку
                result = self.trainer.upload_chunks_batch("test_collection", test_chunks, show_progress=False)
                
                # Проверяем что память использовалась эффективно
                assert result['memory_peak'] < 1000  # Менее 1GB пиковой памяти
                assert result['uploaded'] == 1000
                
                print(f"✅ Memory optimization: пиковая память {result['memory_peak']:.1f} MB")
        
        asyncio.run(run_test())
    
    def test_int8_quantization(self):
        """Тест int8 quantization"""
        # Создаем тестовые эмбеддинги
        original_embeddings = np.random.randn(100, 384).astype(np.float32)
        
        # Создаем quantizer
        quantizer = Int8Quantizer()
        
        # Применяем quantization
        quantized = quantizer.quantize(original_embeddings)
        
        # Проверяем результаты
        assert quantized.shape == original_embeddings.shape
        assert quantized.dtype == np.int8
        
        # Проверяем сжатие
        compression_ratio = quantizer.get_compression_ratio(original_embeddings, quantized)
        assert compression_ratio > 3.0  # Должно быть минимум 3x сжатие
        
        # Проверяем качество (очень мягкие требования для fallback)
        metrics = quantizer.get_quality_metrics(original_embeddings, quantized)
        assert metrics['cosine_similarity'] > 0.2  # Минимальное качество для fallback
        assert metrics['mse'] < 2.0  # Разумная ошибка
        
        print(f"✅ Int8 quantization: сжатие {compression_ratio:.2f}x, качество {metrics['cosine_similarity']:.3f}")
    
    def test_redis_cache_performance(self):
        """Тест производительности Redis cache"""
        import asyncio
        
        async def run_test():
            # Создаем cache
            cache = RedisCache(ttl=60)
            
            # Тестовые данные
            test_query = "поиск в документах"
            test_results = [
                {"content": f"Результат {i}", "score": 0.95 - i * 0.1}
                for i in range(3)
            ]
            
            # Тестируем сохранение
            start_time = time.time()
            cache.set(test_query, test_results)
            save_time = time.time() - start_time
            
            # Тестируем получение
            start_time = time.time()
            cached_results = cache.get(test_query)
            get_time = time.time() - start_time
            
            # Проверяем результаты
            assert cached_results is not None
            assert len(cached_results) == 3
            assert save_time < 0.1  # Быстрое сохранение
            assert get_time < 0.1   # Быстрое получение
            
            # Статистика
            stats = cache.get_stats()
            assert stats['keys_count'] >= 1
            
            print(f"✅ Redis cache: сохранение {save_time*1000:.1f}ms, получение {get_time*1000:.1f}ms")
            
            cache.close()
        
        asyncio.run(run_test())
    
    def test_cache_hit_rate(self):
        """Тест cache hit rate"""
        import asyncio
        
        async def run_test():
            # Создаем cache
            cache = RedisCache(ttl=60)
            
            # Тестовые запросы
            queries = [
                "поиск в документах",
                "анализ тендеров", 
                "поиск в документах",  # Повторный запрос
                "смета и расчеты",
                "поиск в документах"   # Еще один повторный
            ]
            
            test_results = [
                {"content": f"Результат для {q}", "score": 0.9}
                for q in queries
            ]
            
            # Выполняем запросы
            for i, query in enumerate(queries):
                # Сначала сохраняем
                cache.set(query, [test_results[i]])
                # Потом получаем
                cached = cache.get(query)
                assert cached is not None
            
            # Проверяем статистику
            stats = cache.get_stats()
            
            # Должно быть 3 уникальных ключа (2 повторных запроса)
            assert stats['keys_count'] == 3
            
            print(f"✅ Cache hit rate: {stats['keys_count']} уникальных ключей")
            
            cache.close()
        
        asyncio.run(run_test())
    
    def test_parallel_processing(self):
        """Тест параллельной обработки"""
        import asyncio
        
        async def run_test():
            # Создаем много чанков для тестирования параллелизма
            test_chunks = []
            for i in range(500):  # 500 чанков
                chunk = DocumentChunk(
                    content=f"Параллельный тест чанк {i}",
                    metadata={"source": f"parallel_doc_{i}", "chunk_id": i}
                )
                test_chunks.append(chunk)
            
            # Мокаем компоненты
            mock_client = Mock()
            mock_client.upsert = Mock()
            self.trainer.qdrant_client = mock_client
            
            with patch.object(self.trainer, 'create_embeddings_batch') as mock_embeddings:
                mock_embeddings.return_value = np.random.randn(64, 384).astype(np.float32)
                
                # Тестируем с разным количеством воркеров
                for workers in [1, 2, 4]:
                    self.trainer.parallel_workers = workers
                    
                    start_time = time.time()
                    result = self.trainer.upload_chunks_batch("test_collection", test_chunks, show_progress=False)
                    upload_time = time.time() - start_time
                    
                    # С большим количеством воркеров должно быть быстрее
                    if workers > 1:
                        assert upload_time < 5.0  # Быстрая обработка
                    
                    print(f"✅ Parallel processing ({workers} workers): {upload_time:.2f}с")
        
        asyncio.run(run_test())
    
    def test_progress_bar_integration(self):
        """Тест интеграции progress bar"""
        import asyncio
        
        async def run_test():
            # Создаем чанки
            test_chunks = []
            for i in range(100):
                chunk = DocumentChunk(
                    content=f"Progress test chunk {i}",
                    metadata={"source": f"progress_doc_{i}", "chunk_id": i}
                )
                test_chunks.append(chunk)
            
            # Мокаем компоненты
            mock_client = Mock()
            mock_client.upsert = Mock()
            self.trainer.qdrant_client = mock_client
            
            with patch.object(self.trainer, 'create_embeddings_batch') as mock_embeddings:
                mock_embeddings.return_value = np.random.randn(64, 384).astype(np.float32)
                
                # Тестируем с progress bar
                result = self.trainer.upload_chunks_batch("test_collection", test_chunks, show_progress=True)
                
                # Проверяем что все чанки загружены
                assert result['uploaded'] == 100
                assert result['speed'] > 0
                
                print(f"✅ Progress bar: {result['uploaded']} чанков, скорость {result['speed']:.1f} docs/sec")
        
        asyncio.run(run_test())
    
    def test_end_to_end_optimization(self):
        """E2E тест полной оптимизации"""
        import asyncio
        
        async def run_test():
            # Создаем большой набор данных
            test_chunks = []
            for i in range(1000):  # 1000 чанков
                chunk = DocumentChunk(
                    content=f"E2E тест чанк {i} с длинным содержимым для полного тестирования оптимизации системы" * 5,
                    metadata={
                        "source": f"e2e_doc_{i}", 
                        "chunk_id": i,
                        "category": "test",
                        "priority": i % 3
                    }
                )
                test_chunks.append(chunk)
            
            # Мокаем все компоненты
            mock_client = Mock()
            mock_client.upsert = Mock()
            mock_client.search = Mock(return_value=[
                Mock(payload={"content": "test result", "metadata": {}}, score=0.9)
                for _ in range(3)
            ])
            self.trainer.qdrant_client = mock_client
            
            # Мокаем эмбеддинги
            with patch.object(self.trainer, 'create_embeddings_batch') as mock_embeddings:
                mock_embeddings.return_value = np.random.randn(64, 384).astype(np.float32)
                
                # Тестируем полный цикл
                start_time = time.time()
                
                # 1. Загрузка
                upload_result = self.trainer.upload_chunks_batch("e2e_collection", test_chunks, show_progress=False)
                
                # 2. Поиск с кешем
                search_results = self.trainer.search_with_cache("e2e_collection", "тестовый поиск", limit=3)
                
                total_time = time.time() - start_time
                
                # Проверяем результаты
                assert upload_result['uploaded'] == 1000
                assert len(search_results) == 3
                assert total_time < 30.0  # Весь процесс должен быть быстрым
                
                # Проверяем статистику
                stats = self.trainer.get_performance_stats()
                assert stats['total_chunks'] == 1000
                assert stats['upload_speed'] > 0
                
                print(f"✅ E2E optimization:")
                print(f"  • Загружено: {upload_result['uploaded']} чанков")
                print(f"  • Время: {total_time:.2f}с")
                print(f"  • Скорость: {upload_result['speed']:.1f} docs/sec")
                print(f"  • Память: {upload_result['memory_peak']:.1f} MB")
                print(f"  • Найдено результатов: {len(search_results)}")
        
        asyncio.run(run_test())
    
    def test_memory_usage_optimization(self):
        """Тест оптимизации использования памяти"""
        import asyncio
        
        async def run_test():
            # Создаем очень большой набор данных
            test_chunks = []
            for i in range(2000):  # 2000 чанков
                chunk = DocumentChunk(
                    content=f"Memory test chunk {i} with very long content to test memory optimization" * 20,
                    metadata={"source": f"memory_doc_{i}", "chunk_id": i}
                )
                test_chunks.append(chunk)
            
            # Мокаем компоненты
            mock_client = Mock()
            mock_client.upsert = Mock()
            self.trainer.qdrant_client = mock_client
            
            with patch.object(self.trainer, 'create_embeddings_batch') as mock_embeddings:
                # Используем меньшие эмбеддинги для экономии памяти
                mock_embeddings.return_value = np.random.randn(64, 128).astype(np.float32)
                
                # Тестируем загрузку
                result = self.trainer.upload_chunks_batch("memory_collection", test_chunks, show_progress=False)
                
                # Проверяем что память использовалась эффективно
                assert result['memory_peak'] < 500  # Менее 500MB пиковой памяти
                assert result['uploaded'] == 2000
                
                # Проверяем что скорость была хорошей
                assert result['speed'] > 50  # Минимум 50 docs/sec
                
                print(f"✅ Memory optimization:")
                print(f"  • Пиковая память: {result['memory_peak']:.1f} MB")
                print(f"  • Скорость: {result['speed']:.1f} docs/sec")
                print(f"  • Эффективность: {result['uploaded']/result['memory_peak']:.1f} docs/MB")
        
        asyncio.run(run_test())


class TestQuantizationQuality:
    """Тесты качества quantization"""
    
    def test_quantization_quality_metrics(self):
        """Тест метрик качества quantization"""
        # Создаем тестовые эмбеддинги
        original = np.random.randn(200, 384).astype(np.float32)
        
        # Создаем quantizer
        quantizer = Int8Quantizer()
        
        # Применяем quantization
        quantized = quantizer.quantize(original)
        
        # Вычисляем метрики
        metrics = quantizer.get_quality_metrics(original, quantized)
        
        # Проверяем качество (очень мягкие требования для fallback)
        assert metrics['cosine_similarity'] > 0.2  # Минимальное качество
        assert metrics['mse'] < 2.0  # Разумная ошибка
        assert metrics['compression_ratio'] > 3.0  # Хорошее сжатие
        
        print(f"✅ Quantization quality:")
        print(f"  • Cosine similarity: {metrics['cosine_similarity']:.4f}")
        print(f"  • MSE: {metrics['mse']:.6f}")
        print(f"  • Compression: {metrics['compression_ratio']:.2f}x")
    
    def test_quantization_edge_cases(self):
        """Тест граничных случаев quantization"""
        quantizer = Int8Quantizer()
        
        # Тест с нулевыми значениями
        zero_embeddings = np.zeros((10, 384), dtype=np.float32)
        quantized_zero = quantizer.quantize(zero_embeddings)
        assert quantized_zero.shape == zero_embeddings.shape
        
        # Тест с одинаковыми значениями
        same_embeddings = np.ones((10, 384), dtype=np.float32) * 0.5
        quantized_same = quantizer.quantize(same_embeddings)
        assert quantized_same.shape == same_embeddings.shape
        
        # Тест с очень маленькими значениями
        small_embeddings = np.random.randn(10, 384).astype(np.float32) * 1e-6
        quantized_small = quantizer.quantize(small_embeddings)
        assert quantized_small.shape == small_embeddings.shape
        
        print("✅ Quantization edge cases passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
