"""
Краткосрочная память для агентов
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from backend.services.redis_service import redis_service
import json
import logging

logger = logging.getLogger(__name__)


class ShortTermMemory:
    """Краткосрочная память для хранения контекста сессии"""
    
    def __init__(self, session_id: str, ttl: int = 3600):
        """
        Args:
            session_id: ID сессии
            ttl: Время жизни памяти в секундах (по умолчанию 1 час)
        """
        self.session_id = session_id
        self.ttl = ttl
        self.cache_key = f"session_memory:{session_id}"
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Добавление сообщения в историю диалога"""
        try:
            history = self.get_history()
            
            message = {
                "role": role,  # "user" или "assistant"
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            history.append(message)
            
            # Сжатие истории если она слишком длинная
            if len(history) > 50:
                history = self._compress_history(history)
            
            # Сохранение в Redis
            redis_service.set(self.cache_key, history, ex=self.ttl)
            
        except Exception as e:
            logger.error(f"Failed to add message to short-term memory: {e}")
    
    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Получение истории диалога"""
        try:
            history = redis_service.get(self.cache_key) or []
            
            if limit:
                return history[-limit:]
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get history from short-term memory: {e}")
            return []
    
    def get_context(self, max_tokens: int = 2000) -> str:
        """
        Получение контекста для промпта
        
        Args:
            max_tokens: Максимальное количество токенов в контексте
        """
        history = self.get_history()
        
        # Простое сжатие: берем последние N сообщений
        context_messages = []
        total_length = 0
        
        for message in reversed(history):
            content = message.get("content", "")
            length = len(content.split())
            
            if total_length + length > max_tokens:
                break
            
            context_messages.insert(0, message)
            total_length += length
        
        # Форматирование контекста
        context = ""
        for msg in context_messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            context += f"{role}: {content}\n\n"
        
        return context.strip()
    
    def _compress_history(self, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Сжатие истории диалога
        
        Стратегия: оставляем первые и последние сообщения, сжимаем средние
        """
        if len(history) <= 30:
            return history
        
        # Оставляем первые 5 и последние 25 сообщений
        compressed = history[:5] + history[-25:]
        
        # Добавляем сообщение о сжатии
        compressed.insert(5, {
            "role": "system",
            "content": "[История диалога была сжата для экономии памяти]",
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {"compressed": True}
        })
        
        return compressed
    
    def clear(self):
        """Очистка памяти"""
        try:
            redis_service.delete(self.cache_key)
        except Exception as e:
            logger.error(f"Failed to clear short-term memory: {e}")
    
    def extend_ttl(self, additional_seconds: int = 3600):
        """Продление времени жизни памяти"""
        try:
            redis_service.expire(self.cache_key, self.ttl + additional_seconds)
        except Exception as e:
            logger.error(f"Failed to extend TTL: {e}")

