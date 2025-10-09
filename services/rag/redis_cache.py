"""
Redis cache для оптимизации RAG запросов
"""
import json
import time
import hashlib
import logging
from typing import Any, Dict, List, Optional, Union
import redis
from redis.exceptions import ConnectionError, TimeoutError

logger = logging.getLogger(__name__)

class RedisCache:
    """Redis кеш для RAG запросов"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", ttl: int = 3600):
        """
        Инициализация Redis кеша
        
        Args:
            redis_url: URL Redis сервера
            ttl: Время жизни кеша в секундах
        """
        self.redis_url = redis_url
        self.ttl = ttl
        self.client = None
        self.use_memory_fallback = False
        self.memory_cache = {}
        
        # Подключаемся к Redis
        self._connect()
    
    def _connect(self):
        """Подключение к Redis"""
        try:
            self.client = redis.from_url(self.redis_url, decode_responses=True)
            # Проверяем подключение
            self.client.ping()
            logger.info("✅ Подключение к Redis установлено")
        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"⚠️ Не удалось подключиться к Redis: {e}")
            logger.info("🔄 Переключаемся на in-memory кеш")
            self.use_memory_fallback = True
            self.memory_cache = {}
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка подключения к Redis: {e}")
            self.use_memory_fallback = True
            self.memory_cache = {}
    
    def _generate_key(self, query: str) -> str:
        """Генерация ключа кеша"""
        return f"rag_cache:{hashlib.md5(query.encode()).hexdigest()}"
    
    def get(self, key: str) -> Optional[List[Dict[str, Any]]]:
        """
        Получение данных из кеша
        
        Args:
            key: Ключ кеша
            
        Returns:
            Кешированные данные или None
        """
        try:
            if self.use_memory_fallback:
                return self._get_from_memory(key)
            else:
                return self._get_from_redis(key)
        except Exception as e:
            logger.error(f"❌ Ошибка получения из кеша: {e}")
            return None
    
    def _get_from_redis(self, key: str) -> Optional[List[Dict[str, Any]]]:
        """Получение из Redis"""
        try:
            cached_data = self.client.get(key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка получения из Redis: {e}")
            return None
    
    def _get_from_memory(self, key: str) -> Optional[List[Dict[str, Any]]]:
        """Получение из памяти"""
        try:
            if key in self.memory_cache:
                data, timestamp = self.memory_cache[key]
                # Проверяем TTL
                if time.time() - timestamp < self.ttl:
                    return data
                else:
                    # Удаляем истекший кеш
                    del self.memory_cache[key]
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка получения из памяти: {e}")
            return None
    
    def set(self, key: str, value: List[Dict[str, Any]]) -> bool:
        """
        Сохранение данных в кеш
        
        Args:
            key: Ключ кеша
            value: Данные для кеширования
            
        Returns:
            True если успешно сохранено
        """
        try:
            if self.use_memory_fallback:
                return self._set_to_memory(key, value)
            else:
                return self._set_to_redis(key, value)
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения в кеш: {e}")
            return False
    
    def _set_to_redis(self, key: str, value: List[Dict[str, Any]]) -> bool:
        """Сохранение в Redis"""
        try:
            serialized_data = json.dumps(value, ensure_ascii=False)
            self.client.setex(key, self.ttl, serialized_data)
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения в Redis: {e}")
            return False
    
    def _set_to_memory(self, key: str, value: List[Dict[str, Any]]) -> bool:
        """Сохранение в память"""
        try:
            self.memory_cache[key] = (value, time.time())
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения в память: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Удаление из кеша
        
        Args:
            key: Ключ для удаления
            
        Returns:
            True если успешно удалено
        """
        try:
            if self.use_memory_fallback:
                if key in self.memory_cache:
                    del self.memory_cache[key]
                return True
            else:
                return self.client.delete(key) > 0
        except Exception as e:
            logger.error(f"❌ Ошибка удаления из кеша: {e}")
            return False
    
    def clear(self) -> bool:
        """
        Очистка всего кеша
        
        Returns:
            True если успешно очищено
        """
        try:
            if self.use_memory_fallback:
                self.memory_cache.clear()
                return True
            else:
                # Удаляем все ключи с префиксом rag_cache:
                keys = self.client.keys("rag_cache:*")
                if keys:
                    return self.client.delete(*keys) > 0
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка очистки кеша: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Получение статистики кеша
        
        Returns:
            Статистика кеша
        """
        try:
            if self.use_memory_fallback:
                return {
                    "type": "memory",
                    "keys_count": len(self.memory_cache),
                    "memory_usage": self._estimate_memory_usage()
                }
            else:
                # Получаем статистику Redis
                info = self.client.info()
                keys_count = len(self.client.keys("rag_cache:*"))
                
                return {
                    "type": "redis",
                    "keys_count": keys_count,
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory": info.get("used_memory_human", "unknown"),
                    "keyspace": info.get("db0", {}).get("keys", 0)
                }
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {"type": "error", "error": str(e)}
    
    def _estimate_memory_usage(self) -> str:
        """Оценка использования памяти для in-memory кеша"""
        try:
            total_size = 0
            for key, (value, _) in self.memory_cache.items():
                total_size += len(key.encode('utf-8'))
                total_size += len(json.dumps(value, ensure_ascii=False).encode('utf-8'))
            
            if total_size < 1024:
                return f"{total_size} B"
            elif total_size < 1024 * 1024:
                return f"{total_size / 1024:.1f} KB"
            else:
                return f"{total_size / (1024 * 1024):.1f} MB"
        except Exception:
            return "unknown"
    
    def health_check(self) -> Dict[str, Any]:
        """
        Проверка состояния кеша
        
        Returns:
            Состояние кеша
        """
        try:
            if self.use_memory_fallback:
                return {
                    "status": "healthy",
                    "type": "memory",
                    "keys_count": len(self.memory_cache)
                }
            else:
                # Проверяем подключение к Redis
                self.client.ping()
                return {
                    "status": "healthy",
                    "type": "redis",
                    "keys_count": len(self.client.keys("rag_cache:*"))
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def close(self):
        """Закрытие соединения"""
        try:
            if self.client and not self.use_memory_fallback:
                self.client.close()
            logger.info("✅ Соединение с кешем закрыто")
        except Exception as e:
            logger.error(f"❌ Ошибка закрытия соединения: {e}")


# Функция для демонстрации кеша
def demonstrate_cache():
    """Демонстрация работы кеша"""
    print("=== ДЕМОНСТРАЦИЯ REDIS CACHE ===")
    
    # Создаем кеш
    cache = RedisCache(ttl=60)  # 1 минута TTL для демо
    
    # Тестовые данные
    test_query = "поиск в документах"
    test_results = [
        {"content": "Результат 1", "score": 0.95},
        {"content": "Результат 2", "score": 0.87},
        {"content": "Результат 3", "score": 0.82}
    ]
    
    # Сохраняем в кеш
    print("💾 Сохраняем в кеш...")
    cache.set(test_query, test_results)
    
    # Получаем из кеша
    print("📖 Получаем из кеша...")
    cached_results = cache.get(test_query)
    
    if cached_results:
        print(f"✅ Cache hit: найдено {len(cached_results)} результатов")
        for i, result in enumerate(cached_results, 1):
            print(f"  {i}. {result['content']} (score: {result['score']})")
    else:
        print("❌ Cache miss")
    
    # Статистика
    stats = cache.get_stats()
    print(f"📊 Статистика кеша:")
    print(f"  • Тип: {stats['type']}")
    print(f"  • Ключей: {stats['keys_count']}")
    if 'memory_usage' in stats:
        print(f"  • Память: {stats['memory_usage']}")
    
    # Проверка здоровья
    health = cache.health_check()
    print(f"🏥 Состояние: {health['status']}")
    
    # Закрываем
    cache.close()
    print("✅ Демонстрация завершена")


if __name__ == "__main__":
    demonstrate_cache()
