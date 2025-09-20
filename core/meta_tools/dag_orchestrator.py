"""
DAG Orchestrator для SuperBuilder - управление сложными многошаговыми задачами
с зависимостями между инструментами и параллельным выполнением.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Tuple
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque

try:
    import networkx as nx
except ImportError:
    print("NetworkX не установлен. Установите: pip install networkx")
    nx = None

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Статусы выполнения задач"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class Priority(Enum):
    """Приоритеты задач"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class TaskNode:
    """Узел задачи в DAG"""
    id: str
    tool_name: str
    params: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    priority: Priority = Priority.NORMAL
    timeout: Optional[int] = None  # секунды
    retries: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        """Инициализация после создания объекта"""
        if not self.id:
            self.id = str(uuid.uuid4())
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Продолжительность выполнения задачи"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
    
    def is_ready(self, completed_tasks: Set[str]) -> bool:
        """Проверка готовности задачи к выполнению"""
        return all(dep in completed_tasks for dep in self.dependencies)
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь"""
        return {
            "id": self.id,
            "tool_name": self.tool_name,
            "params": self.params,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "priority": self.priority.value,
            "timeout": self.timeout,
            "retries": self.retries,
            "max_retries": self.max_retries,
            "duration": str(self.duration) if self.duration else None
        }


@dataclass
class DAGWorkflow:
    """Workflow представляет граф задач с зависимостями"""
    id: str
    name: str
    description: str
    tasks: Dict[str, TaskNode] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    
    def __post_init__(self):
        """Инициализация после создания объекта"""
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def add_task(self, task: TaskNode) -> None:
        """Добавить задачу в workflow"""
        self.tasks[task.id] = task
    
    def add_dependency(self, task_id: str, dependency_id: str) -> None:
        """Добавить зависимость между задачами"""
        if task_id in self.tasks and dependency_id in self.tasks:
            if dependency_id not in self.tasks[task_id].dependencies:
                self.tasks[task_id].dependencies.append(dependency_id)
    
    def validate_dag(self) -> Tuple[bool, Optional[str]]:
        """Валидация DAG на цикличность"""
        if not nx:
            return False, "NetworkX не доступен для валидации DAG"
        
        try:
            # Создаем граф NetworkX
            G = nx.DiGraph()
            
            # Добавляем узлы
            for task_id in self.tasks:
                G.add_node(task_id)
            
            # Добавляем ребра (зависимости)
            for task_id, task in self.tasks.items():
                for dep_id in task.dependencies:
                    G.add_edge(dep_id, task_id)
            
            # Проверяем на цикличность
            if not nx.is_directed_acyclic_graph(G):
                cycles = list(nx.simple_cycles(G))
                return False, f"Обнаружены циклы в DAG: {cycles}"
            
            return True, None
            
        except Exception as e:
            return False, f"Ошибка валидации DAG: {str(e)}"
    
    def get_ready_tasks(self, completed_tasks: Set[str]) -> List[TaskNode]:
        """Получить задачи готовые к выполнению"""
        ready_tasks = []
        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING and task.is_ready(completed_tasks):
                ready_tasks.append(task)
        
        # Сортируем по приоритету
        ready_tasks.sort(key=lambda x: x.priority.value, reverse=True)
        return ready_tasks
    
    def update_progress(self) -> None:
        """Обновить прогресс выполнения workflow"""
        if not self.tasks:
            self.progress = 0.0
            return
        
        total_tasks = len(self.tasks)
        completed_tasks = sum(1 for task in self.tasks.values() 
                            if task.status in [TaskStatus.COMPLETED, TaskStatus.SKIPPED])
        
        self.progress = (completed_tasks / total_tasks) * 100.0
        
        # Обновляем общий статус workflow
        if self.progress == 100.0:
            self.status = TaskStatus.COMPLETED
        elif self.progress > 0:
            self.status = TaskStatus.RUNNING
        else:
            self.status = TaskStatus.PENDING
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "tasks": {task_id: task.to_dict() for task_id, task in self.tasks.items()},
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "progress": self.progress
        }


class DAGOrchestrator:
    """
    Оркестратор для выполнения DAG workflow'ов с поддержкой
    параллельного выполнения, retry логики и monitoring'а.
    """
    
    def __init__(self, tools_system, max_concurrent_tasks: int = 5):
        """
        Инициализация оркестратора
        
        Args:
            tools_system: Система инструментов для выполнения задач
            max_concurrent_tasks: Максимальное количество параллельных задач
        """
        self.tools_system = tools_system
        self.max_concurrent_tasks = max_concurrent_tasks
        self.workflows: Dict[str, DAGWorkflow] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.completed_tasks: Dict[str, Set[str]] = defaultdict(set)
        
        # Очереди задач по приоритетам
        self.task_queues = {
            Priority.CRITICAL: deque(),
            Priority.HIGH: deque(),
            Priority.NORMAL: deque(),
            Priority.LOW: deque()
        }
        
        # Статистика
        self.stats = {
            "workflows_executed": 0,
            "tasks_executed": 0,
            "tasks_failed": 0,
            "average_execution_time": 0.0
        }
        
        logger.info(f"DAG Orchestrator инициализирован с max_concurrent_tasks={max_concurrent_tasks}")
    
    def create_workflow(self, name: str, description: str = "") -> DAGWorkflow:
        """Создать новый workflow"""
        workflow = DAGWorkflow(
            id=str(uuid.uuid4()),
            name=name,
            description=description
        )
        self.workflows[workflow.id] = workflow
        logger.info(f"Создан workflow '{name}' с ID: {workflow.id}")
        return workflow
    
    def add_task_to_workflow(self, 
                           workflow_id: str,
                           tool_name: str,
                           params: Dict[str, Any],
                           dependencies: List[str] = None,
                           priority: Priority = Priority.NORMAL,
                           timeout: Optional[int] = None,
                           max_retries: int = 3) -> Optional[str]:
        """
        Добавить задачу в workflow
        
        Returns:
            ID созданной задачи или None при ошибке
        """
        if workflow_id not in self.workflows:
            logger.error(f"Workflow с ID {workflow_id} не найден")
            return None
        
        task = TaskNode(
            id=str(uuid.uuid4()),
            tool_name=tool_name,
            params=params or {},
            dependencies=dependencies or [],
            priority=priority,
            timeout=timeout,
            max_retries=max_retries
        )
        
        self.workflows[workflow_id].add_task(task)
        logger.info(f"Добавлена задача '{tool_name}' в workflow {workflow_id}")
        return task.id
    
    def add_dependency(self, workflow_id: str, task_id: str, dependency_id: str) -> bool:
        """Добавить зависимость между задачами"""
        if workflow_id not in self.workflows:
            logger.error(f"Workflow с ID {workflow_id} не найден")
            return False
        
        self.workflows[workflow_id].add_dependency(task_id, dependency_id)
        logger.info(f"Добавлена зависимость: {task_id} -> {dependency_id}")
        return True
    
    async def execute_task(self, workflow_id: str, task: TaskNode) -> Any:
        """
        Выполнить отдельную задачу
        
        Args:
            workflow_id: ID workflow
            task: Задача для выполнения
            
        Returns:
            Результат выполнения задачи
        """
        task.status = TaskStatus.RUNNING
        task.start_time = datetime.now()
        
        logger.info(f"Начало выполнения задачи {task.id} ({task.tool_name})")
        
        try:
            # Создаем задачу с таймаутом если указан
            if task.timeout:
                result = await asyncio.wait_for(
                    self._execute_tool(task),
                    timeout=task.timeout
                )
            else:
                result = await self._execute_tool(task)
            
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.end_time = datetime.now()
            
            # Добавляем в множество завершенных задач
            self.completed_tasks[workflow_id].add(task.id)
            
            logger.info(f"Задача {task.id} выполнена успешно за {task.duration}")
            self.stats["tasks_executed"] += 1
            
            return result
            
        except asyncio.TimeoutError:
            task.error = f"Задача превысила лимит времени {task.timeout} секунд"
            task.status = TaskStatus.FAILED
            task.end_time = datetime.now()
            
            logger.error(f"Задача {task.id} превысила таймаут: {task.timeout} секунд")
            
        except Exception as e:
            task.error = str(e)
            task.status = TaskStatus.FAILED
            task.end_time = datetime.now()
            
            logger.error(f"Ошибка выполнения задачи {task.id}: {e}")
            self.stats["tasks_failed"] += 1
            
            # Проверяем возможность retry
            if task.retries < task.max_retries:
                task.retries += 1
                task.status = TaskStatus.PENDING
                logger.info(f"Повторная попытка #{task.retries} для задачи {task.id}")
                return await self.execute_task(workflow_id, task)
        
        return None
    
    async def _execute_tool(self, task: TaskNode) -> Any:
        """Выполнить инструмент асинхронно"""
        # Если tools_system поддерживает async выполнение
        if hasattr(self.tools_system, 'execute_tool_async'):
            return await self.tools_system.execute_tool_async(task.tool_name, **task.params)
        
        # Иначе выполняем синхронно в executor
        loop = asyncio.get_event_loop()
        if hasattr(self.tools_system, 'execute_tool'):
            return await loop.run_in_executor(
                None, 
                lambda: self.tools_system.execute_tool(task.tool_name, **task.params)
            )
        elif hasattr(self.tools_system, task.tool_name):
            method = getattr(self.tools_system, task.tool_name)
            return await loop.run_in_executor(None, lambda: method(**task.params))
        else:
            raise ValueError(f"Инструмент {task.tool_name} не найден в tools_system")
    
    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Выполнить workflow полностью
        
        Args:
            workflow_id: ID workflow для выполнения
            
        Returns:
            Результат выполнения workflow
        """
        if workflow_id not in self.workflows:
            return {"error": f"Workflow с ID {workflow_id} не найден"}
        
        workflow = self.workflows[workflow_id]
        
        # Валидация DAG
        is_valid, error = workflow.validate_dag()
        if not is_valid:
            logger.error(f"Ошибка валидации workflow {workflow_id}: {error}")
            return {"error": f"Невалидный DAG: {error}"}
        
        logger.info(f"Начало выполнения workflow '{workflow.name}' ({workflow_id})")
        workflow.status = TaskStatus.RUNNING
        
        start_time = datetime.now()
        
        try:
            # Основной цикл выполнения
            while True:
                # Получаем готовые к выполнению задачи
                ready_tasks = workflow.get_ready_tasks(self.completed_tasks[workflow_id])
                
                if not ready_tasks:
                    # Проверяем, есть ли еще выполняющиеся задачи
                    running_tasks = [t for t in workflow.tasks.values() 
                                   if t.status == TaskStatus.RUNNING]
                    if not running_tasks:
                        break  # Все задачи завершены
                
                # Ограничиваем количество параллельных задач
                available_slots = self.max_concurrent_tasks - len(self.running_tasks)
                tasks_to_start = ready_tasks[:available_slots]
                
                # Запускаем готовые задачи
                for task in tasks_to_start:
                    task_coroutine = self.execute_task(workflow_id, task)
                    async_task = asyncio.create_task(task_coroutine)
                    self.running_tasks[task.id] = async_task
                
                # Ждем завершения хотя бы одной задачи
                if self.running_tasks:
                    done, pending = await asyncio.wait(
                        self.running_tasks.values(),
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    # Удаляем завершенные задачи из running_tasks
                    for task_id in list(self.running_tasks.keys()):
                        if self.running_tasks[task_id] in done:
                            del self.running_tasks[task_id]
                
                # Обновляем прогресс
                workflow.update_progress()
                
                # Небольшая пауза для предотвращения busy-waiting
                await asyncio.sleep(0.1)
            
            # Ждем завершения всех оставшихся задач
            if self.running_tasks:
                await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)
                self.running_tasks.clear()
            
            # Финальное обновление статуса
            workflow.update_progress()
            end_time = datetime.now()
            
            # Статистика
            execution_time = (end_time - start_time).total_seconds()
            self.stats["workflows_executed"] += 1
            
            # Считаем среднее время выполнения
            if self.stats["workflows_executed"] == 1:
                self.stats["average_execution_time"] = execution_time
            else:
                self.stats["average_execution_time"] = (
                    (self.stats["average_execution_time"] * (self.stats["workflows_executed"] - 1) + execution_time) /
                    self.stats["workflows_executed"]
                )
            
            logger.info(f"Workflow '{workflow.name}' завершен за {execution_time:.2f} секунд")
            
            return {
                "workflow_id": workflow_id,
                "status": workflow.status.value,
                "progress": workflow.progress,
                "execution_time": execution_time,
                "tasks_completed": len(self.completed_tasks[workflow_id]),
                "tasks_total": len(workflow.tasks),
                "results": {task_id: task.result for task_id, task in workflow.tasks.items() 
                          if task.status == TaskStatus.COMPLETED}
            }
            
        except Exception as e:
            workflow.status = TaskStatus.FAILED
            logger.error(f"Ошибка выполнения workflow {workflow_id}: {e}")
            return {
                "workflow_id": workflow_id,
                "status": "failed",
                "error": str(e)
            }
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Получить статус workflow"""
        if workflow_id not in self.workflows:
            return None
        
        workflow = self.workflows[workflow_id]
        workflow.update_progress()
        
        return {
            "id": workflow.id,
            "name": workflow.name,
            "status": workflow.status.value,
            "progress": workflow.progress,
            "tasks": {
                "total": len(workflow.tasks),
                "pending": len([t for t in workflow.tasks.values() if t.status == TaskStatus.PENDING]),
                "running": len([t for t in workflow.tasks.values() if t.status == TaskStatus.RUNNING]),
                "completed": len([t for t in workflow.tasks.values() if t.status == TaskStatus.COMPLETED]),
                "failed": len([t for t in workflow.tasks.values() if t.status == TaskStatus.FAILED])
            }
        }
    
    def cancel_workflow(self, workflow_id: str) -> bool:
        """Отменить выполнение workflow"""
        if workflow_id not in self.workflows:
            return False
        
        workflow = self.workflows[workflow_id]
        workflow.status = TaskStatus.CANCELLED
        
        # Отменяем все pending задачи
        for task in workflow.tasks.values():
            if task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
        
        # Отменяем running задачи
        tasks_to_cancel = []
        for task_id, async_task in self.running_tasks.items():
            if any(task.id == task_id for task in workflow.tasks.values()):
                async_task.cancel()
                tasks_to_cancel.append(task_id)
        
        for task_id in tasks_to_cancel:
            del self.running_tasks[task_id]
        
        logger.info(f"Workflow {workflow_id} отменен")
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику работы оркестратора"""
        return {
            "workflows": {
                "total": len(self.workflows),
                "executed": self.stats["workflows_executed"],
                "running": len([w for w in self.workflows.values() if w.status == TaskStatus.RUNNING]),
                "completed": len([w for w in self.workflows.values() if w.status == TaskStatus.COMPLETED]),
                "failed": len([w for w in self.workflows.values() if w.status == TaskStatus.FAILED])
            },
            "tasks": {
                "executed": self.stats["tasks_executed"],
                "failed": self.stats["tasks_failed"],
                "success_rate": (
                    (self.stats["tasks_executed"] - self.stats["tasks_failed"]) / 
                    max(1, self.stats["tasks_executed"]) * 100
                )
            },
            "performance": {
                "average_execution_time": self.stats["average_execution_time"],
                "current_running_tasks": len(self.running_tasks),
                "max_concurrent_tasks": self.max_concurrent_tasks
            }
        }


# Пример использования
async def example_usage():
    """Пример использования DAG Orchestrator"""
    
    # Mock tools system для примера
    class MockToolsSystem:
        async def execute_tool_async(self, tool_name: str, **params):
            await asyncio.sleep(1)  # Имитация работы
            return f"Result from {tool_name} with {params}"
    
    # Создаем оркестратор
    tools_system = MockToolsSystem()
    orchestrator = DAGOrchestrator(tools_system, max_concurrent_tasks=3)
    
    # Создаем workflow
    workflow = orchestrator.create_workflow(
        name="Комплексный анализ проекта",
        description="Анализ проекта с поиском норм, расчетом сметы и генерацией отчета"
    )
    
    # Добавляем задачи
    task1_id = orchestrator.add_task_to_workflow(
        workflow.id,
        "search_rag_database",
        {"query": "СП 48", "doc_types": ["norms"]},
        priority=Priority.HIGH
    )
    
    task2_id = orchestrator.add_task_to_workflow(
        workflow.id,
        "calculate_estimate",
        {"project_data": {"area": 1000}},
        dependencies=[task1_id]
    )
    
    task3_id = orchestrator.add_task_to_workflow(
        workflow.id,
        "create_document",
        {"template": "report", "data": {}},
        dependencies=[task1_id, task2_id]
    )
    
    # Выполняем workflow
    result = await orchestrator.execute_workflow(workflow.id)
    print("Результат выполнения:", json.dumps(result, indent=2, ensure_ascii=False))
    
    # Получаем статистику
    stats = orchestrator.get_statistics()
    print("Статистика:", json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    # Запуск примера
    asyncio.run(example_usage())