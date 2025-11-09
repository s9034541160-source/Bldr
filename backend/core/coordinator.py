"""
Координатор для управления агентами и инструментами
"""

from typing import Dict, List, Any, Optional
from backend.core.model_manager import model_manager
import logging

logger = logging.getLogger(__name__)


class Coordinator:
    """Координатор для управления выполнением задач через агентов"""
    
    def __init__(self):
        self.agents: Dict[str, Any] = {}
        self.tools: Dict[str, Any] = {}
    
    def register_agent(self, agent_id: str, agent: Any):
        """Регистрация агента"""
        self.agents[agent_id] = agent
        logger.info(f"Agent {agent_id} registered")
    
    def register_tool(self, tool_id: str, tool: Any):
        """Регистрация инструмента"""
        self.tools[tool_id] = tool
        logger.info(f"Tool {tool_id} registered")
    
    def execute_task(
        self,
        task: str,
        agent_id: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Выполнение задачи
        
        Args:
            task: Описание задачи
            agent_id: ID агента (если None, выбирается автоматически)
            context: Контекст выполнения
        """
        # Если агент не указан, выбираем подходящего
        if not agent_id:
            agent_id = self._select_agent(task)
        
        if agent_id not in self.agents:
            return {
                "success": False,
                "error": f"Agent {agent_id} not found"
            }
        
        agent = self.agents[agent_id]
        
        try:
            result = agent.execute(task, context or {})
            return {
                "success": True,
                "agent_id": agent_id,
                "result": result
            }
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _select_agent(self, task: str) -> str:
        """Автоматический выбор агента на основе задачи"""
        # Простая эвристика - в будущем можно использовать LLM для выбора
        task_lower = task.lower()
        
        if "document" in task_lower or "документ" in task_lower:
            return "document_agent"
        elif "project" in task_lower or "проект" in task_lower:
            return "project_agent"
        elif "process" in task_lower or "процесс" in task_lower:
            return "process_agent"
        else:
            # Возвращаем первый доступный агент или default
            return list(self.agents.keys())[0] if self.agents else "default"
    
    def generate_response(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7
    ) -> Optional[str]:
        """Генерация ответа через LLM"""
        return model_manager.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )


# Глобальный экземпляр координатора
coordinator = Coordinator()

