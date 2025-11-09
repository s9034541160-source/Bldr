"""
Базовый класс для агентов
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from backend.core.model_manager import model_manager
import logging

logger = logging.getLogger(__name__)


class Agent(ABC):
    """Базовый класс для всех агентов"""
    
    def __init__(self, agent_id: str, name: str, description: str):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.tools: List[Any] = []
    
    def register_tool(self, tool: Any):
        """Регистрация инструмента для агента"""
        self.tools.append(tool)
        logger.info(f"Tool {tool.__class__.__name__} registered for agent {self.agent_id}")
    
    @abstractmethod
    def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполнение задачи
        
        Args:
            task: Описание задачи
            context: Контекст выполнения
            
        Returns:
            Результат выполнения
        """
        pass
    
    def generate_prompt(self, task: str, context: Dict[str, Any]) -> str:
        """Генерация промпта для LLM"""
        prompt = f"Задача: {task}\n\n"
        
        if context:
            prompt += "Контекст:\n"
            for key, value in context.items():
                prompt += f"- {key}: {value}\n"
        
        if self.tools:
            prompt += "\nДоступные инструменты:\n"
            for tool in self.tools:
                prompt += f"- {tool.__class__.__name__}: {tool.description}\n"
        
        return prompt
    
    def call_llm(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> Optional[str]:
        """Вызов LLM для генерации ответа"""
        return model_manager.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )


class BaseAgent(Agent):
    """Базовый агент с простой реализацией"""
    
    def __init__(self, agent_id: str, name: str, description: str):
        super().__init__(agent_id, name, description)
    
    def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Простая реализация выполнения задачи"""
        prompt = self.generate_prompt(task, context)
        response = self.call_llm(prompt)
        
        return {
            "task": task,
            "response": response,
            "context": context
        }

