"""
Базовый класс для инструментов агентов
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class Tool(ABC):
    """Базовый класс для всех инструментов"""
    
    def __init__(self, tool_id: str, name: str, description: str):
        self.tool_id = tool_id
        self.name = name
        self.description = description
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Выполнение инструмента
        
        Args:
            **kwargs: Параметры инструмента
            
        Returns:
            Результат выполнения
        """
        pass
    
    def validate_params(self, **kwargs) -> bool:
        """
        Валидация параметров
        
        Args:
            **kwargs: Параметры для валидации
            
        Returns:
            True если параметры валидны
        """
        return True
    
    def get_schema(self) -> Dict[str, Any]:
        """Получение схемы инструмента для LLM"""
        return {
            "tool_id": self.tool_id,
            "name": self.name,
            "description": self.description,
            "parameters": self._get_parameters_schema()
        }
    
    @abstractmethod
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Схема параметров инструмента"""
        pass

