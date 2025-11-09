"""
Базовый класс для агентов
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from backend.core.model_manager import model_manager
from backend.core.memory.memory_manager import get_memory_manager
import logging

logger = logging.getLogger(__name__)


class Agent(ABC):
    """Базовый класс для всех агентов"""
    
    def __init__(self, agent_id: str, name: str, description: str, session_id: Optional[str] = None):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.tools: List[Any] = []
        self.session_id = session_id
        self.memory = get_memory_manager(session_id or agent_id) if session_id or agent_id else None
    
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
        
        # Добавление контекста из краткосрочной памяти
        if self.memory:
            memory_context = self.memory.get_context(max_tokens=500)
            if memory_context:
                prompt += f"Контекст предыдущего диалога:\n{memory_context}\n\n"
            
            # Добавление релевантных фактов из долгосрочной памяти
            relevant_facts = self.memory.get_relevant_facts(task, limit=3)
            if relevant_facts:
                prompt += "Релевантные факты:\n"
                for fact in relevant_facts:
                    prompt += f"- {fact}\n"
                prompt += "\n"
        
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
        
        # Сохранение взаимодействия в память
        if self.memory:
            self.memory.add_interaction(
                user_message=task,
                assistant_response=response or "",
                metadata={"agent_id": self.agent_id, "context": context}
            )
        
        return {
            "task": task,
            "response": response,
            "context": context
        }

