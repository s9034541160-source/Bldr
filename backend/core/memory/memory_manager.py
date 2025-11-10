"""
Менеджер памяти для управления краткосрочной и долгосрочной памятью
"""

from typing import Dict, Any, Optional, List
from backend.core.memory.short_term import ShortTermMemory
from backend.core.memory.long_term import LongTermMemory
import logging

logger = logging.getLogger(__name__)


class MemoryManager:
    """Менеджер для управления памятью агентов"""
    
    def __init__(self, session_id: str, user_id: Optional[str] = None):
        """
        Args:
            session_id: ID сессии
            user_id: ID пользователя (опционально)
        """
        self.session_id = session_id
        self.user_id = user_id
        self.short_term = ShortTermMemory(session_id)
        self.long_term = LongTermMemory(user_id)
    
    def add_interaction(
        self,
        user_message: str,
        assistant_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Добавление взаимодействия в память"""
        # Краткосрочная память
        self.short_term.add_message("user", user_message, metadata)
        self.short_term.add_message("assistant", assistant_response, metadata)
        
        # Периодическое извлечение знаний в долгосрочную память
        # (каждые 10 сообщений)
        history = self.short_term.get_history()
        if len(history) % 10 == 0:
            self.long_term.extract_knowledge_from_dialogue(history, self.user_id)
    
    def get_context(self, max_tokens: int = 2000) -> str:
        """Получение контекста из краткосрочной памяти"""
        return self.short_term.get_context(max_tokens)
    
    def get_relevant_facts(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Получение релевантных фактов из долгосрочной памяти"""
        return self.long_term.search_memory(query, limit)
    
    def store_important_fact(
        self,
        fact_type: str,
        subject: str,
        predicate: str,
        object_value: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Сохранение важного факта в долгосрочную память"""
        return self.long_term.store_fact(
            fact_type=fact_type,
            subject=subject,
            predicate=predicate,
            object_value=object_value,
            metadata=metadata
        )


# Глобальный реестр менеджеров памяти
_memory_managers: Dict[str, MemoryManager] = {}


def get_memory_manager(session_id: str, user_id: Optional[str] = None) -> MemoryManager:
    """Получение или создание менеджера памяти для сессии"""
    if session_id not in _memory_managers:
        _memory_managers[session_id] = MemoryManager(session_id, user_id)
    
    return _memory_managers[session_id]

