#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DUAL MEMORY SYSTEM FOR Bldr Empire
==================================

Система двойной памяти (краткосрочная/долгосрочная) на основе паттернов
из agents-towards-production.
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import hashlib
import redis
from abc import ABC, abstractmethod

from core.exceptions import RAGIndexError, DatabaseException
from core.structured_logging import get_logger

logger = get_logger("dual_memory")

@dataclass
class MemoryEntry:
    """Запись в памяти"""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    importance_score: float = 0.0
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь"""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "access_count": self.access_count,
            "importance_score": self.importance_score,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        """Создание из словаря"""
        entry = cls(
            id=data["id"],
            content=data["content"],
            metadata=data.get("metadata", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            access_count=data.get("access_count", 0),
            importance_score=data.get("importance_score", 0.0),
            tags=data.get("tags", [])
        )
        return entry

class MemoryBackend(ABC):
    """Базовый класс для бэкендов памяти"""
    
    @abstractmethod
    async def store(self, entry: MemoryEntry) -> bool:
        """Сохранение записи"""
        pass
    
    @abstractmethod
    async def retrieve(self, query: str, limit: int = 10) -> List[MemoryEntry]:
        """Поиск записей"""
        pass
    
    @abstractmethod
    async def update(self, entry: MemoryEntry) -> bool:
        """Обновление записи"""
        pass
    
    @abstractmethod
    async def delete(self, entry_id: str) -> bool:
        """Удаление записи"""
        pass

class RedisMemoryBackend(MemoryBackend):
    """Redis бэкенд для памяти"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.logger = get_logger("redis_memory")
    
    async def store(self, entry: MemoryEntry) -> bool:
        """Сохранение в Redis"""
        try:
            key = f"memory:{entry.id}"
            data = json.dumps(entry.to_dict(), ensure_ascii=False)
            self.redis_client.set(key, data)
            
            # Индексируем по тегам
            for tag in entry.tags:
                tag_key = f"tag:{tag}"
                self.redis_client.sadd(tag_key, entry.id)
            
            self.logger.log_agent_activity(
                agent_name="redis_memory",
                action="entry_stored",
                query=entry.content[:100],
                result_status="success",
                context={"entry_id": entry.id, "tags": entry.tags}
            )
            
            return True
        except Exception as e:
            self.logger.log_error(e, {"entry_id": entry.id})
            return False
    
    async def retrieve(self, query: str, limit: int = 10) -> List[MemoryEntry]:
        """Поиск в Redis"""
        try:
            # Простой поиск по содержимому (в реальности нужен semantic search)
            keys = self.redis_client.keys("memory:*")
            results = []
            
            for key in keys[:limit]:
                data = self.redis_client.get(key)
                if data:
                    entry_data = json.loads(data)
                    if query.lower() in entry_data["content"].lower():
                        entry = MemoryEntry.from_dict(entry_data)
                        results.append(entry)
            
            return results[:limit]
        except Exception as e:
            self.logger.log_error(e, {"query": query})
            return []
    
    async def update(self, entry: MemoryEntry) -> bool:
        """Обновление в Redis"""
        return await self.store(entry)
    
    async def delete(self, entry_id: str) -> bool:
        """Удаление из Redis"""
        try:
            key = f"memory:{entry_id}"
            self.redis_client.delete(key)
            return True
        except Exception as e:
            self.logger.log_error(e, {"entry_id": entry_id})
            return False

class InMemoryBackend(MemoryBackend):
    """In-memory бэкенд для тестирования"""
    
    def __init__(self):
        self.storage: Dict[str, MemoryEntry] = {}
        self.logger = get_logger("in_memory")
    
    async def store(self, entry: MemoryEntry) -> bool:
        """Сохранение в памяти"""
        self.storage[entry.id] = entry
        return True
    
    async def retrieve(self, query: str, limit: int = 10) -> List[MemoryEntry]:
        """Поиск в памяти"""
        results = []
        for entry in self.storage.values():
            if query.lower() in entry.content.lower():
                results.append(entry)
        return results[:limit]
    
    async def update(self, entry: MemoryEntry) -> bool:
        """Обновление в памяти"""
        if entry.id in self.storage:
            self.storage[entry.id] = entry
            return True
        return False
    
    async def delete(self, entry_id: str) -> bool:
        """Удаление из памяти"""
        if entry_id in self.storage:
            del self.storage[entry_id]
            return True
        return False

class DualMemorySystem:
    """
    🚀 СИСТЕМА ДВОЙНОЙ ПАМЯТИ
    
    Управляет краткосрочной и долгосрочной памятью:
    - Short-term: Быстрый доступ, ограниченный объем
    - Long-term: Постоянное хранение, семантический поиск
    """
    
    def __init__(self, short_term_backend: Optional[MemoryBackend] = None,
                 long_term_backend: Optional[MemoryBackend] = None):
        self.short_term_backend = short_term_backend or InMemoryBackend()
        self.long_term_backend = long_term_backend or InMemoryBackend()
        self.logger = get_logger("dual_memory")
        
        # Настройки краткосрочной памяти
        self.short_term_max_size = 1000
        self.short_term_ttl_hours = 24
        
        # Настройки долгосрочной памяти
        self.long_term_importance_threshold = 0.7
    
    async def store_memory(self, content: str, metadata: Dict[str, Any] = None,
                          tags: List[str] = None, importance_score: float = 0.5) -> str:
        """
        🎯 СОХРАНЕНИЕ В ПАМЯТЬ
        
        Args:
            content: Содержимое для сохранения
            metadata: Метаданные
            tags: Теги для категоризации
            importance_score: Оценка важности (0-1)
        
        Returns:
            ID сохраненной записи
        """
        # Генерируем уникальный ID
        entry_id = hashlib.md5(f"{content}{datetime.now()}".encode()).hexdigest()[:16]
        
        # Создаем запись
        entry = MemoryEntry(
            id=entry_id,
            content=content,
            metadata=metadata or {},
            tags=tags or [],
            importance_score=importance_score
        )
        
        # Сохраняем в краткосрочную память
        await self.short_term_backend.store(entry)
        
        # Если важность высокая, сохраняем в долгосрочную
        if importance_score >= self.long_term_importance_threshold:
            await self.long_term_backend.store(entry)
            self.logger.log_agent_activity(
                agent_name="dual_memory",
                action="stored_long_term",
                query=content[:100],
                result_status="success",
                context={"entry_id": entry_id, "importance": importance_score}
            )
        else:
            self.logger.log_agent_activity(
                agent_name="dual_memory",
                action="stored_short_term",
                query=content[:100],
                result_status="success",
                context={"entry_id": entry_id, "importance": importance_score}
            )
        
        return entry_id
    
    async def retrieve_memory(self, query: str, limit: int = 10,
                             include_long_term: bool = True) -> List[MemoryEntry]:
        """
        🎯 ПОИСК В ПАМЯТИ
        
        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов
            include_long_term: Включать долгосрочную память
        
        Returns:
            Список найденных записей
        """
        results = []
        
        # Поиск в краткосрочной памяти
        short_term_results = await self.short_term_backend.retrieve(query, limit)
        results.extend(short_term_results)
        
        # Поиск в долгосрочной памяти
        if include_long_term:
            long_term_results = await self.long_term_backend.retrieve(query, limit)
            results.extend(long_term_results)
        
        # Убираем дубликаты и сортируем по важности
        unique_results = {}
        for entry in results:
            if entry.id not in unique_results:
                unique_results[entry.id] = entry
            else:
                # Обновляем счетчик доступа
                unique_results[entry.id].access_count += 1
        
        # Сортируем по важности и времени
        sorted_results = sorted(
            unique_results.values(),
            key=lambda x: (x.importance_score, x.timestamp),
            reverse=True
        )
        
        self.logger.log_agent_activity(
            agent_name="dual_memory",
            action="memory_retrieved",
            query=query,
            result_status="success",
            context={
                "query": query,
                "results_count": len(sorted_results),
                "short_term_count": len(short_term_results),
                "long_term_count": len(long_term_results) if include_long_term else 0
            }
        )
        
        return sorted_results[:limit]
    
    async def update_memory(self, entry_id: str, content: str = None,
                           metadata: Dict[str, Any] = None,
                           importance_score: float = None) -> bool:
        """Обновление записи в памяти"""
        # Получаем существующую запись
        existing_entries = await self.short_term_backend.retrieve(entry_id, 1)
        if not existing_entries:
            return False
        
        entry = existing_entries[0]
        
        # Обновляем поля
        if content is not None:
            entry.content = content
        if metadata is not None:
            entry.metadata.update(metadata)
        if importance_score is not None:
            entry.importance_score = importance_score
        
        # Сохраняем обновления
        await self.short_term_backend.update(entry)
        
        # Если важность изменилась, обновляем долгосрочную память
        if importance_score is not None:
            if importance_score >= self.long_term_importance_threshold:
                await self.long_term_backend.store(entry)
            else:
                await self.long_term_backend.delete(entry_id)
        
        return True
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Получение статистики памяти"""
        # Это упрощенная версия - в реальности нужны более сложные запросы
        return {
            "short_term_backend": "InMemoryBackend",
            "long_term_backend": "InMemoryBackend",
            "short_term_max_size": self.short_term_max_size,
            "long_term_threshold": self.long_term_importance_threshold
        }

# Глобальная система памяти
_global_memory_system: Optional[DualMemorySystem] = None

def get_memory_system() -> DualMemorySystem:
    """Получение глобальной системы памяти"""
    global _global_memory_system
    if _global_memory_system is None:
        _global_memory_system = DualMemorySystem()
    return _global_memory_system
