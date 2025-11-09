"""
Сервис для работы с Redis
"""

import redis
from backend.config.settings import settings
import json
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)


class RedisService:
    """Сервис для работы с Redis"""
    
    def __init__(self):
        self.client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
    
    def ping(self) -> bool:
        """Проверка соединения"""
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False
    
    def set(self, key: str, value: Any, ex: Optional[int] = None):
        """Установка значения с опциональным TTL"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        return self.client.set(key, value, ex=ex)
    
    def get(self, key: str) -> Optional[str]:
        """Получение значения"""
        value = self.client.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    def delete(self, key: str):
        """Удаление ключа"""
        return self.client.delete(key)
    
    def exists(self, key: str) -> bool:
        """Проверка существования ключа"""
        return bool(self.client.exists(key))
    
    def expire(self, key: str, seconds: int):
        """Установка TTL для ключа"""
        return self.client.expire(key, seconds)
    
    def incr(self, key: str):
        """Увеличение значения на 1"""
        return self.client.incr(key)
    
    def decr(self, key: str):
        """Уменьшение значения на 1"""
        return self.client.decr(key)
    
    def hset(self, name: str, key: str, value: Any):
        """Установка значения в hash"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        return self.client.hset(name, key, value)
    
    def hget(self, name: str, key: str) -> Optional[Any]:
        """Получение значения из hash"""
        value = self.client.hget(name, key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    def hgetall(self, name: str) -> dict:
        """Получение всех значений из hash"""
        return self.client.hgetall(name)


# Глобальный экземпляр сервиса
redis_service = RedisService()

