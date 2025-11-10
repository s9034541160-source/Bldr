"""
Координатор для управления агентами и инструментами
"""

from __future__ import annotations

import heapq
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from backend.core.model_manager import model_manager

logger = logging.getLogger(__name__)


@dataclass(order=True, slots=True, kw_only=True)
class QueuedTask:
    """Описание задачи в очереди координатора."""

    priority: int
    order: int
    task: str = field(compare=False)
    agent_id: Optional[str] = field(default=None, compare=False)
    context: Dict[str, Any] = field(default_factory=dict, compare=False)


class Coordinator:
    """Координатор для управления выполнением задач через агентов"""

    def __init__(self) -> None:
        self.agents: Dict[str, Any] = {}
        self.tools: Dict[str, Any] = {}
        self.task_queue: List[QueuedTask] = []
        self._task_counter: int = 0
        self._register_default_agents()

    def register_agent(self, agent_id: str, agent: Any) -> None:
        """Регистрация агента"""
        self.agents[agent_id] = agent
        logger.info("Agent %s registered", agent_id)

    def register_tool(self, tool_id: str, tool: Any) -> None:
        """Регистрация инструмента"""
        self.tools[tool_id] = tool
        logger.info("Tool %s registered", tool_id)

    def list_agents(self) -> List[str]:
        """Возвращает список идентификаторов зарегистрированных агентов"""
        return list(self.agents.keys())

    def submit_task(
        self,
        task: str,
        *,
        priority: int = 0,
        agent_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Помещение задачи в очередь"""
        self._task_counter += 1
        queued = QueuedTask(
            priority=-priority,
            order=self._task_counter,
            task=task,
            agent_id=agent_id,
            context=context or {},
        )
        heapq.heappush(self.task_queue, queued)
        logger.info("Task '%s' queued with priority %s", task, priority)
        return {"success": True, "queued": True, "task": task, "priority": priority}

    def execute_task(
        self,
        task: str,
        agent_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        *,
        priority: int = 0,
        enqueue: bool = False,
    ) -> Dict[str, Any]:
        """Выполнение задачи"""
        if enqueue:
            return self.submit_task(task, priority=priority, agent_id=agent_id, context=context)

        if not agent_id:
            agent_id = self._select_agent(task)

        if agent_id not in self.agents:
            return {"success": False, "error": f"Agent {agent_id} not found"}

        agent = self.agents[agent_id]

        try:
            result = agent.execute(task, context or {})
            return {
                "success": True,
                "agent_id": agent_id,
                "priority": priority,
                "result": result,
            }
        except Exception as exc:  # noqa: BLE001
            logger.error("Task execution failed: %s", exc)
            return {"success": False, "error": str(exc)}

    def execute_next_task(self) -> Dict[str, Any]:
        """Выполнение следующей задачи из очереди"""
        if not self.task_queue:
            return {"success": False, "error": "No queued tasks"}
        queued = heapq.heappop(self.task_queue)
        priority = -queued.priority
        return self.execute_task(
            queued.task,
            agent_id=queued.agent_id,
            context=queued.context,
            priority=priority,
        )

    def _select_agent(self, task: str) -> str:
        """Автоматический выбор агента на основе задачи"""
        task_lower = task.lower()
        match task_lower:
            case s if "document" in s or "документ" in s:
                return "document_agent"
            case s if "project" in s or "проект" in s:
                return "project_agent"
            case s if "estimate" in s or "смет" in s:
                return "estimate_agent"
            case s if "process" in s or "процесс" in s:
                return "process_agent"
            case _:
                return list(self.agents.keys())[0] if self.agents else "default"

    def generate_response(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> Optional[str]:
        """Генерация ответа через LLM"""
        return model_manager.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    def _register_default_agents(self) -> None:
        """Регистрация базовых специализированных агентов"""
        try:
            from backend.core.agents.specialized import bootstrap_default_agents

            for agent_id, agent in bootstrap_default_agents().items():
                self.register_agent(agent_id, agent)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to register default agents: %s", exc)


# Глобальный экземпляр координатора
coordinator = Coordinator()

