#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BASE AGENT FOR Bldr Empire
===========================

Базовый класс для всех агентов с четким разделением ответственности
на основе паттернов из agents-towards-production.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import logging

from core.exceptions import AgentException, AgentPlanningError, AgentExecutionError
from core.structured_logging import get_logger

logger = get_logger("base_agent")

@dataclass
class Task:
    """Задача для выполнения агентом"""
    id: str
    description: str
    input_data: Dict[str, Any]
    priority: int = 1  # 1 = высший приоритет
    timeout_seconds: Optional[int] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class TaskResult:
    """Результат выполнения задачи"""
    task_id: str
    success: bool
    result_data: Any = None
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class BaseAgent(ABC):
    """
    🚀 БАЗОВЫЙ КЛАСС АГЕНТА
    
    Четкое разделение ответственности:
    - Каждый агент имеет свою специализацию
    - Единый интерфейс для всех агентов
    - Изолированная обработка ошибок
    - Структурированное логирование
    """
    
    def __init__(self, name: str, specialization: str):
        self.name = name
        self.specialization = specialization
        self.logger = get_logger(f"agent_{name}")
        self.is_available = True
        self.current_tasks: List[Task] = []
        self.completed_tasks: List[TaskResult] = []
    
    @abstractmethod
    async def process(self, task: Task) -> TaskResult:
        """
        🎯 ОСНОВНОЙ МЕТОД ОБРАБОТКИ ЗАДАЧ
        
        Args:
            task: Задача для выполнения
        
        Returns:
            TaskResult с результатом выполнения
        
        Raises:
            AgentExecutionError: При ошибке выполнения
        """
        pass
    
    @abstractmethod
    def can_handle(self, task: Task) -> bool:
        """
        🎯 ПРОВЕРКА СПОСОБНОСТИ ОБРАБОТКИ ЗАДАЧИ
        
        Args:
            task: Задача для проверки
        
        Returns:
            True если агент может обработать задачу
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        🎯 ПОЛУЧЕНИЕ СПОСОБНОСТЕЙ АГЕНТА
        
        Returns:
            Список возможностей агента
        """
        pass
    
    async def execute_task(self, task: Task) -> TaskResult:
        """
        🚀 ВЫПОЛНЕНИЕ ЗАДАЧИ С ОБРАБОТКОЙ ОШИБОК
        
        Args:
            task: Задача для выполнения
        
        Returns:
            TaskResult с результатом
        """
        start_time = datetime.now()
        
        try:
            # Проверяем доступность агента
            if not self.is_available:
                raise AgentExecutionError(
                    self.name, 
                    task.description, 
                    "Агент недоступен"
                )
            
            # Проверяем способность обработки
            if not self.can_handle(task):
                raise AgentExecutionError(
                    self.name,
                    task.description,
                    f"Агент {self.name} не может обработать задачу типа {task.description}"
                )
            
            # Добавляем задачу в текущие
            self.current_tasks.append(task)
            
            # Логируем начало выполнения
            self.logger.log_agent_activity(
                agent_name=self.name,
                action="task_started",
                query=task.description,
                result_status="processing",
                context={"task_id": task.id, "priority": task.priority}
            )
            
            # Выполняем задачу
            result = await self.process(task)
            
            # Вычисляем время выполнения
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            result.execution_time_ms = execution_time
            
            # Убираем из текущих задач
            self.current_tasks = [t for t in self.current_tasks if t.id != task.id]
            
            # Добавляем в завершенные
            self.completed_tasks.append(result)
            
            # Логируем завершение
            self.logger.log_agent_activity(
                agent_name=self.name,
                action="task_completed",
                query=task.description,
                result_status="success" if result.success else "error",
                context={
                    "task_id": task.id,
                    "execution_time_ms": execution_time,
                    "success": result.success
                }
            )
            
            return result
            
        except AgentException as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            self.logger.log_error(e, {"task_id": task.id, "agent_name": self.name})
            
            return TaskResult(
                task_id=task.id,
                success=False,
                error_message=str(e),
                execution_time_ms=execution_time
            )
        
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            self.logger.log_error(e, {"task_id": task.id, "agent_name": self.name})
            
            return TaskResult(
                task_id=task.id,
                success=False,
                error_message=f"Неожиданная ошибка: {str(e)}",
                execution_time_ms=execution_time
            )
    
    def get_status(self) -> Dict[str, Any]:
        """Получение статуса агента"""
        return {
            "name": self.name,
            "specialization": self.specialization,
            "is_available": self.is_available,
            "current_tasks_count": len(self.current_tasks),
            "completed_tasks_count": len(self.completed_tasks),
            "capabilities": self.get_capabilities()
        }
    
    def set_availability(self, available: bool):
        """Установка доступности агента"""
        self.is_available = available
        self.logger.log_agent_activity(
            agent_name=self.name,
            action="availability_changed",
            query="",
            result_status="available" if available else "unavailable",
            context={"available": available}
        )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Получение метрик производительности"""
        if not self.completed_tasks:
            return {"message": "Нет завершенных задач"}
        
        successful_tasks = [t for t in self.completed_tasks if t.success]
        failed_tasks = [t for t in self.completed_tasks if not t.success]
        
        avg_execution_time = sum(t.execution_time_ms for t in self.completed_tasks) / len(self.completed_tasks)
        
        return {
            "total_tasks": len(self.completed_tasks),
            "successful_tasks": len(successful_tasks),
            "failed_tasks": len(failed_tasks),
            "success_rate": len(successful_tasks) / len(self.completed_tasks),
            "avg_execution_time_ms": avg_execution_time,
            "current_load": len(self.current_tasks)
        }
