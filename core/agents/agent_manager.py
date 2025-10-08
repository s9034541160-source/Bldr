#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AGENT MANAGER FOR Bldr Empire
=============================

Менеджер агентов с четким разделением ответственности
на основе паттернов из agents-towards-production.
"""

from typing import Dict, Any, List, Optional, Type
from core.agents.base_agent import BaseAgent, Task, TaskResult
from core.agents.specialized_agents import ChiefEngineerAgent, AnalystAgent, CoordinatorAgent
from core.exceptions import AgentCommunicationError, AgentPlanningError
from core.structured_logging import get_logger

logger = get_logger("agent_manager")

class AgentManager:
    """
    🚀 МЕНЕДЖЕР АГЕНТОВ
    
    Управляет всеми агентами системы с четким разделением ответственности:
    - Регистрация и управление агентами
    - Маршрутизация задач к подходящим агентам
    - Мониторинг производительности
    - Координация между агентами
    """
    
    def __init__(self, tools_system=None):
        self.tools_system = tools_system
        self.agents: Dict[str, BaseAgent] = {}
        self.logger = get_logger("agent_manager")
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Инициализация всех агентов"""
        # Создаем специализированных агентов
        self.agents["chief_engineer"] = ChiefEngineerAgent(self.tools_system)
        self.agents["analyst"] = AnalystAgent(self.tools_system)
        self.agents["coordinator"] = CoordinatorAgent(self.tools_system)
        
        self.logger.log_agent_activity(
            agent_name="agent_manager",
            action="agents_initialized",
            query="",
            result_status="success",
            context={"agents_count": len(self.agents)}
        )
    
    def register_agent(self, agent: BaseAgent):
        """Регистрация нового агента"""
        self.agents[agent.name] = agent
        self.logger.log_agent_activity(
            agent_name="agent_manager",
            action="agent_registered",
            query="",
            result_status="success",
            context={"agent_name": agent.name, "specialization": agent.specialization}
        )
    
    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """Получение агента по имени"""
        return self.agents.get(agent_name)
    
    def get_available_agents(self) -> List[BaseAgent]:
        """Получение доступных агентов"""
        return [agent for agent in self.agents.values() if agent.is_available]
    
    def find_best_agent(self, task: Task) -> Optional[BaseAgent]:
        """
        🎯 ПОИСК ЛУЧШЕГО АГЕНТА ДЛЯ ЗАДАЧИ
        
        Args:
            task: Задача для выполнения
        
        Returns:
            Подходящий агент или None
        """
        available_agents = self.get_available_agents()
        
        if not available_agents:
            raise AgentPlanningError(
                "agent_manager",
                task.description,
                "Нет доступных агентов"
            )
        
        # Ищем агента, который может обработать задачу
        for agent in available_agents:
            if agent.can_handle(task):
                self.logger.log_agent_activity(
                    agent_name="agent_manager",
                    action="agent_selected",
                    query=task.description,
                    result_status="success",
                    context={
                        "selected_agent": agent.name,
                        "task_id": task.id,
                        "specialization": agent.specialization
                    }
                )
                return agent
        
        # Если никто не подходит, возвращаем координатора
        coordinator = self.agents.get("coordinator")
        if coordinator and coordinator.is_available:
            self.logger.log_agent_activity(
                agent_name="agent_manager",
                action="fallback_to_coordinator",
                query=task.description,
                result_status="success",
                context={"task_id": task.id}
            )
            return coordinator
        
        return None
    
    async def execute_task(self, task: Task) -> TaskResult:
        """
        🚀 ВЫПОЛНЕНИЕ ЗАДАЧИ ЧЕРЕЗ ПОДХОДЯЩЕГО АГЕНТА
        
        Args:
            task: Задача для выполнения
        
        Returns:
            Результат выполнения
        """
        try:
            # Находим подходящего агента
            agent = self.find_best_agent(task)
            
            if not agent:
                return TaskResult(
                    task_id=task.id,
                    success=False,
                    error_message="Не найден подходящий агент для выполнения задачи"
                )
            
            # Выполняем задачу через агента
            result = await agent.execute_task(task)
            
            self.logger.log_agent_activity(
                agent_name="agent_manager",
                action="task_executed",
                query=task.description,
                result_status="success" if result.success else "error",
                context={
                    "task_id": task.id,
                    "executing_agent": agent.name,
                    "success": result.success
                }
            )
            
            return result
            
        except Exception as e:
            self.logger.log_error(e, {"task_id": task.id})
            return TaskResult(
                task_id=task.id,
                success=False,
                error_message=f"Ошибка выполнения задачи: {str(e)}"
            )
    
    async def execute_multiple_tasks(self, tasks: List[Task], max_concurrent: int = 3) -> Dict[str, TaskResult]:
        """
        🚀 ПАРАЛЛЕЛЬНОЕ ВЫПОЛНЕНИЕ НЕСКОЛЬКИХ ЗАДАЧ
        
        Args:
            tasks: Список задач
            max_concurrent: Максимальное количество одновременных выполнений
        
        Returns:
            Словарь с результатами выполнения
        """
        import asyncio
        
        semaphore = asyncio.Semaphore(max_concurrent)
        results = {}
        
        async def execute_single_task(task):
            async with semaphore:
                result = await self.execute_task(task)
                return task.id, result
        
        # Запускаем все задачи параллельно
        tasks_coroutines = [execute_single_task(task) for task in tasks]
        completed_tasks = await asyncio.gather(*tasks_coroutines, return_exceptions=True)
        
        # Собираем результаты
        for task_result in completed_tasks:
            if isinstance(task_result, Exception):
                self.logger.log_error(task_result, {"context": "parallel_execution"})
            else:
                task_id, result = task_result
                results[task_id] = result
        
        return results
    
    def get_system_status(self) -> Dict[str, Any]:
        """Получение статуса всей системы агентов"""
        status = {
            "total_agents": len(self.agents),
            "available_agents": len(self.get_available_agents()),
            "agents": {}
        }
        
        for agent_name, agent in self.agents.items():
            status["agents"][agent_name] = {
                "status": agent.get_status(),
                "performance": agent.get_performance_metrics()
            }
        
        return status
    
    def get_agent_performance_summary(self) -> Dict[str, Any]:
        """Получение сводки по производительности агентов"""
        summary = {}
        
        for agent_name, agent in self.agents.items():
            metrics = agent.get_performance_metrics()
            summary[agent_name] = {
                "specialization": agent.specialization,
                "is_available": agent.is_available,
                "performance": metrics
            }
        
        return summary
    
    def set_agent_availability(self, agent_name: str, available: bool):
        """Установка доступности агента"""
        if agent_name in self.agents:
            self.agents[agent_name].set_availability(available)
            self.logger.log_agent_activity(
                agent_name="agent_manager",
                action="agent_availability_changed",
                query="",
                result_status="success",
                context={"agent_name": agent_name, "available": available}
            )
    
    def get_agent_capabilities(self) -> Dict[str, List[str]]:
        """Получение способностей всех агентов"""
        capabilities = {}
        
        for agent_name, agent in self.agents.items():
            capabilities[agent_name] = {
                "specialization": agent.specialization,
                "capabilities": agent.get_capabilities()
            }
        
        return capabilities
