"""
Базовый класс для агентов
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from backend.core.model_manager import model_manager
from backend.core.memory.memory_manager import get_memory_manager
from backend.core.logging import AgentLogger
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
        self.activity_logger = AgentLogger(agent_id)
    
    def register_tool(self, tool: Any):
        """Регистрация инструмента для агента"""
        self.tools.append(tool)
        metadata = {"tool": tool.__class__.__name__}
        logger.info(f"Tool {tool.__class__.__name__} registered for agent {self.agent_id}")
        self.log_action("register_tool", metadata=metadata)
    
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
        self.log_action(
            "call_llm",
            metadata={
                "prompt_preview": prompt[:200],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
        )
        return model_manager.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )

    def remember_fact(
        self,
        fact_type: str,
        subject: str,
        predicate: str,
        object_value: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Сохранение важного факта в долгосрочную память"""
        if not self.memory:
            logger.warning("Memory manager not initialized for agent %s", self.agent_id)
            return False
        success = self.memory.store_important_fact(
            fact_type=fact_type,
            subject=subject,
            predicate=predicate,
            object_value=object_value,
            metadata=metadata
        )
        self.log_action(
            "remember_fact",
            status="success" if success else "error",
            metadata={
                "fact_type": fact_type,
                "subject": subject,
                "predicate": predicate,
                "object_value": object_value
            }
        )
        return success

    def get_recent_context(self, max_tokens: int = 500) -> str:
        """Получить недавний контекст из краткосрочной памяти"""
        if not self.memory:
            return ""
        context = self.memory.get_context(max_tokens=max_tokens)
        self.log_action("get_recent_context", metadata={"max_tokens": max_tokens})
        return context

    def get_relevant_facts(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Получение релевантных фактов из долгосрочной памяти"""
        if not self.memory:
            return []
        facts = self.memory.get_relevant_facts(query=query, limit=limit)
        self.log_action("get_relevant_facts", metadata={"query": query, "limit": limit, "results": len(facts)})
        return facts

    def clear_short_term_memory(self) -> None:
        """Очистка краткосрочной памяти"""
        if self.memory:
            self.memory.short_term.clear()
            self.log_action("clear_short_term_memory")

    def log_action(
        self,
        action: str,
        status: str = "success",
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Логирование действия агента"""
        self.activity_logger.log(action, status=status, message=message, metadata=metadata)


class BaseAgent(Agent):
    """Базовый агент с простой реализацией"""
    
    def __init__(self, agent_id: str, name: str, description: str):
        super().__init__(agent_id, name, description)
    
    def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Простая реализация выполнения задачи"""
        self.log_action("execute_start", metadata={"task": task, "context": context})
        prompt = self.generate_prompt(task, context)
        try:
            response = self.call_llm(prompt)
            status = "success"
        except Exception as exc:
            response = None
            status = "error"
            self.log_action("execute_error", status="error", message=str(exc), metadata={"task": task})
            raise
        finally:
            # Сохранение взаимодействия в память
            if self.memory:
                self.memory.add_interaction(
                    user_message=task,
                    assistant_response=response or "",
                    metadata={"agent_id": self.agent_id, "context": context}
                )

        self.log_action(
            "execute_end",
            status=status,
            metadata={"task": task, "has_response": bool(response)}
        )
        
        return {
            "task": task,
            "response": response,
            "context": context
        }

