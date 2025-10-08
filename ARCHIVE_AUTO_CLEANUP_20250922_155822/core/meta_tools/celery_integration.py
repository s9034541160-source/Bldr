"""
Celery интеграция для SuperBuilder Meta-Tools System
Обеспечивает асинхронное выполнение длительных задач с поддержкой распределенной обработки.
"""

import asyncio
import json
import logging
import pickle
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import asdict
from enum import Enum

try:
    from celery import Celery, Task
    from celery.result import AsyncResult
    from celery import states
    CELERY_AVAILABLE = True
except ImportError:
    print("Celery не установлен. Установите: pip install celery redis")
    CELERY_AVAILABLE = False
    Celery = None
    Task = None
    AsyncResult = None
    states = None

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    print("Redis не установлен. Установите: pip install redis")
    REDIS_AVAILABLE = False
    redis = None

from .dag_orchestrator import DAGOrchestrator, DAGWorkflow, TaskNode, TaskStatus, Priority
from .meta_tools_system import MetaToolsSystem

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CeleryTaskStatus(Enum):
    """Статусы Celery задач"""
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    REVOKED = "REVOKED"


class CeleryIntegration:
    """
    Интеграция с Celery для асинхронного выполнения мета-инструментов и DAG workflow'ов
    """
    
    def __init__(self, 
                 broker_url: str = "redis://localhost:6379/0",
                 result_backend: str = "redis://localhost:6379/0",
                 task_serializer: str = "pickle",
                 accept_content: List[str] = None,
                 result_serializer: str = "pickle"):
        """
        Инициализация Celery интеграции
        
        Args:
            broker_url: URL брокера сообщений (Redis/RabbitMQ)
            result_backend: Backend для хранения результатов
            task_serializer: Сериализатор для задач
            accept_content: Типы контента для приема
            result_serializer: Сериализатор для результатов
        """
        if not CELERY_AVAILABLE:
            raise ImportError("Celery не установлен. Установите: pip install celery redis")
        
        self.broker_url = broker_url
        self.result_backend = result_backend
        
        # Создаем Celery приложение
        self.app = Celery('superbuilder_meta_tools')
        self.app.conf.update(
            broker_url=broker_url,
            result_backend=result_backend,
            task_serializer=task_serializer,
            accept_content=accept_content or ['pickle', 'json'],
            result_serializer=result_serializer,
            timezone='Europe/Moscow',
            enable_utc=True,
            task_track_started=True,
            task_time_limit=3600,  # 1 час максимум на задачу
            task_soft_time_limit=3300,  # Мягкий лимит 55 минут
            worker_prefetch_multiplier=1,
            task_acks_late=True,
            worker_disable_rate_limits=False,
            task_compression='gzip',
            result_compression='gzip',
            result_expires=86400,  # Результаты хранятся 24 часа
        )
        
        # Регистрируем задачи
        self._register_celery_tasks()
        
        # Кеш для активных задач
        self.active_tasks: Dict[str, AsyncResult] = {}
        
        logger.info(f"Celery интеграция инициализирована с broker: {broker_url}")
    
    def _register_celery_tasks(self) -> None:
        """Регистрация Celery задач"""
        
        @self.app.task(bind=True, name='execute_meta_tool_async')
        def execute_meta_tool_async(task_self, 
                                  meta_system_config: Dict[str, Any],
                                  tool_name: str, 
                                  params: Dict[str, Any]) -> Dict[str, Any]:
            """
            Асинхронное выполнение мета-инструмента через Celery
            """
            try:
                # Обновляем статус задачи
                task_self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': 0,
                        'total': 100,
                        'status': f'Запуск мета-инструмента {tool_name}'
                    }
                )
                
                # Восстанавливаем MetaToolsSystem из конфигурации
                # В реальной реализации это будет более сложная десериализация
                meta_system = self._restore_meta_system(meta_system_config)
                
                # Выполняем мета-инструмент
                # Поскольку Celery не поддерживает async напрямую, используем asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    result = loop.run_until_complete(
                        meta_system.execute_meta_tool(tool_name, **params)
                    )
                finally:
                    loop.close()
                
                return {
                    'status': 'SUCCESS',
                    'result': result,
                    'task_id': task_self.request.id,
                    'completed_at': datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Ошибка выполнения мета-инструмента {tool_name}: {e}")
                return {
                    'status': 'FAILURE',
                    'error': str(e),
                    'task_id': task_self.request.id,
                    'failed_at': datetime.now().isoformat()
                }
        
        @self.app.task(bind=True, name='execute_workflow_async')
        def execute_workflow_async(task_self,
                                 orchestrator_config: Dict[str, Any],
                                 workflow_data: Dict[str, Any]) -> Dict[str, Any]:
            """
            Асинхронное выполнение DAG workflow через Celery
            """
            try:
                task_self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': 0,
                        'total': 100,
                        'status': f'Запуск workflow {workflow_data.get("name", "Unknown")}'
                    }
                )
                
                # Восстанавливаем оркестратор
                orchestrator = self._restore_orchestrator(orchestrator_config)
                
                # Восстанавливаем workflow
                workflow = self._restore_workflow(workflow_data)
                orchestrator.workflows[workflow.id] = workflow
                
                # Выполняем workflow асинхронно
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    result = loop.run_until_complete(
                        orchestrator.execute_workflow(workflow.id)
                    )
                finally:
                    loop.close()
                
                return {
                    'status': 'SUCCESS',
                    'result': result,
                    'task_id': task_self.request.id,
                    'completed_at': datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Ошибка выполнения workflow: {e}")
                return {
                    'status': 'FAILURE',
                    'error': str(e),
                    'task_id': task_self.request.id,
                    'failed_at': datetime.now().isoformat()
                }
        
        @self.app.task(bind=True, name='execute_single_tool_async')
        def execute_single_tool_async(task_self,
                                    tools_system_config: Dict[str, Any],
                                    tool_name: str,
                                    params: Dict[str, Any]) -> Dict[str, Any]:
            """
            Асинхронное выполнение отдельного инструмента
            """
            try:
                task_self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': 50,
                        'total': 100,
                        'status': f'Выполнение инструмента {tool_name}'
                    }
                )
                
                # Восстанавливаем tools_system
                tools_system = self._restore_tools_system(tools_system_config)
                
                # Выполняем инструмент
                if hasattr(tools_system, 'execute_tool'):
                    result = tools_system.execute_tool(tool_name, **params)
                elif hasattr(tools_system, tool_name):
                    method = getattr(tools_system, tool_name)
                    result = method(**params)
                else:
                    raise ValueError(f"Инструмент {tool_name} не найден")
                
                return {
                    'status': 'SUCCESS',
                    'result': result,
                    'task_id': task_self.request.id,
                    'completed_at': datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Ошибка выполнения инструмента {tool_name}: {e}")
                return {
                    'status': 'FAILURE',
                    'error': str(e),
                    'task_id': task_self.request.id,
                    'failed_at': datetime.now().isoformat()
                }
        
        # Сохраняем ссылки на задачи
        self.execute_meta_tool_async = execute_meta_tool_async
        self.execute_workflow_async = execute_workflow_async
        self.execute_single_tool_async = execute_single_tool_async
    
    def submit_meta_tool(self, 
                        meta_system: MetaToolsSystem,
                        tool_name: str,
                        params: Dict[str, Any],
                        priority: int = 5,
                        eta: Optional[datetime] = None,
                        countdown: Optional[int] = None) -> str:
        """
        Отправить мета-инструмент на асинхронное выполнение
        
        Args:
            meta_system: Экземпляр MetaToolsSystem
            tool_name: Имя мета-инструмента
            params: Параметры выполнения
            priority: Приоритет задачи (0-9, где 9 - максимальный)
            eta: Время запуска задачи
            countdown: Задержка запуска в секундах
            
        Returns:
            ID задачи Celery
        """
        # Сериализуем конфигурацию meta_system (упрощенно)
        meta_system_config = {
            'type': 'MetaToolsSystem',
            'tools_system_type': type(meta_system.tools_system).__name__
        }
        
        # Отправляем задачу
        result = self.execute_meta_tool_async.apply_async(
            args=(meta_system_config, tool_name, params),
            priority=priority,
            eta=eta,
            countdown=countdown,
            task_id=str(uuid.uuid4())
        )
        
        # Сохраняем в кеше
        self.active_tasks[result.id] = result
        
        logger.info(f"Отправлен мета-инструмент {tool_name} на выполнение, task_id: {result.id}")
        return result.id
    
    def submit_workflow(self,
                       orchestrator: DAGOrchestrator,
                       workflow: DAGWorkflow,
                       priority: int = 5,
                       eta: Optional[datetime] = None,
                       countdown: Optional[int] = None) -> str:
        """
        Отправить workflow на асинхронное выполнение
        
        Args:
            orchestrator: Экземпляр DAGOrchestrator
            workflow: Workflow для выполнения
            priority: Приоритет задачи
            eta: Время запуска задачи
            countdown: Задержка запуска в секундах
            
        Returns:
            ID задачи Celery
        """
        # Сериализуем конфигурацию оркестратора
        orchestrator_config = {
            'type': 'DAGOrchestrator',
            'max_concurrent_tasks': orchestrator.max_concurrent_tasks,
            'tools_system_type': type(orchestrator.tools_system).__name__
        }
        
        # Сериализуем workflow
        workflow_data = workflow.to_dict()
        
        # Отправляем задачу
        result = self.execute_workflow_async.apply_async(
            args=(orchestrator_config, workflow_data),
            priority=priority,
            eta=eta,
            countdown=countdown,
            task_id=str(uuid.uuid4())
        )
        
        self.active_tasks[result.id] = result
        
        logger.info(f"Отправлен workflow '{workflow.name}' на выполнение, task_id: {result.id}")
        return result.id
    
    def submit_tool(self,
                   tools_system: Any,
                   tool_name: str,
                   params: Dict[str, Any],
                   priority: int = 5,
                   eta: Optional[datetime] = None,
                   countdown: Optional[int] = None) -> str:
        """
        Отправить отдельный инструмент на асинхронное выполнение
        
        Args:
            tools_system: Система инструментов
            tool_name: Имя инструмента
            params: Параметры
            priority: Приоритет задачи
            eta: Время запуска задачи
            countdown: Задержка запуска в секундах
            
        Returns:
            ID задачи Celery
        """
        tools_system_config = {
            'type': type(tools_system).__name__
        }
        
        result = self.execute_single_tool_async.apply_async(
            args=(tools_system_config, tool_name, params),
            priority=priority,
            eta=eta,
            countdown=countdown,
            task_id=str(uuid.uuid4())
        )
        
        self.active_tasks[result.id] = result
        
        logger.info(f"Отправлен инструмент {tool_name} на выполнение, task_id: {result.id}")
        return result.id
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Получить статус задачи
        
        Args:
            task_id: ID задачи
            
        Returns:
            Информация о статусе задачи
        """
        if task_id in self.active_tasks:
            result = self.active_tasks[task_id]
        else:
            result = AsyncResult(task_id, app=self.app)
        
        status_info = {
            'task_id': task_id,
            'status': result.status,
            'ready': result.ready(),
            'successful': result.successful() if result.ready() else None,
            'failed': result.failed() if result.ready() else None
        }
        
        if result.ready():
            if result.successful():
                status_info['result'] = result.get()
            else:
                status_info['error'] = str(result.info)
                status_info['traceback'] = result.traceback
        else:
            # Получаем промежуточный статус если доступен
            if hasattr(result, 'info') and result.info:
                status_info['progress'] = result.info
        
        return status_info
    
    def get_task_result(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """
        Получить результат задачи (блокирующий вызов)
        
        Args:
            task_id: ID задачи
            timeout: Таймаут ожидания в секундах
            
        Returns:
            Результат выполнения задачи
        """
        if task_id in self.active_tasks:
            result = self.active_tasks[task_id]
        else:
            result = AsyncResult(task_id, app=self.app)
        
        return result.get(timeout=timeout)
    
    def cancel_task(self, task_id: str, terminate: bool = False) -> bool:
        """
        Отменить задачу
        
        Args:
            task_id: ID задачи
            terminate: Жесткое завершение задачи
            
        Returns:
            True если задача была отменена
        """
        try:
            if task_id in self.active_tasks:
                result = self.active_tasks[task_id]
            else:
                result = AsyncResult(task_id, app=self.app)
            
            if terminate:
                result.revoke(terminate=True)
            else:
                result.revoke()
            
            # Удаляем из кеша
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            
            logger.info(f"Задача {task_id} отменена (terminate={terminate})")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отмены задачи {task_id}: {e}")
            return False
    
    def list_active_tasks(self) -> List[Dict[str, Any]]:
        """
        Получить список активных задач
        
        Returns:
            Список информации об активных задачах
        """
        active_tasks = []
        
        for task_id, result in self.active_tasks.items():
            task_info = {
                'task_id': task_id,
                'status': result.status,
                'ready': result.ready(),
                'name': getattr(result, 'name', 'unknown')
            }
            
            if not result.ready() and hasattr(result, 'info'):
                task_info['progress'] = result.info
            
            active_tasks.append(task_info)
        
        return active_tasks
    
    def cleanup_completed_tasks(self) -> int:
        """
        Очистить завершенные задачи из кеша
        
        Returns:
            Количество очищенных задач
        """
        completed_tasks = []
        
        for task_id, result in self.active_tasks.items():
            if result.ready():
                completed_tasks.append(task_id)
        
        for task_id in completed_tasks:
            del self.active_tasks[task_id]
        
        logger.info(f"Очищено {len(completed_tasks)} завершенных задач")
        return len(completed_tasks)
    
    def get_worker_stats(self) -> Dict[str, Any]:
        """
        Получить статистику воркеров
        
        Returns:
            Статистика воркеров Celery
        """
        try:
            inspect = self.app.control.inspect()
            
            stats = {
                'active_tasks': inspect.active(),
                'scheduled_tasks': inspect.scheduled(),
                'reserved_tasks': inspect.reserved(),
                'registered_tasks': inspect.registered(),
                'worker_stats': inspect.stats()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики воркеров: {e}")
            return {'error': str(e)}
    
    def start_worker(self, 
                    concurrency: int = 4,
                    queues: Optional[List[str]] = None,
                    loglevel: str = 'info') -> None:
        """
        Запустить Celery worker (для разработки)
        
        Args:
            concurrency: Количество параллельных процессов
            queues: Очереди для обработки
            loglevel: Уровень логирования
        """
        logger.info("Запуск Celery worker...")
        
        worker = self.app.Worker(
            concurrency=concurrency,
            queues=queues or ['celery'],
            loglevel=loglevel
        )
        
        worker.start()
    
    # ====== HELPER METHODS ======
    
    def _restore_meta_system(self, config: Dict[str, Any]) -> MetaToolsSystem:
        """Восстановить MetaToolsSystem из конфигурации (заглушка)"""
        # В реальной реализации здесь будет полная десериализация
        class MockToolsSystem:
            def execute_tool(self, tool_name: str, **params):
                return f"Mock result from {tool_name}"
        
        tools_system = MockToolsSystem()
        return MetaToolsSystem(tools_system)
    
    def _restore_orchestrator(self, config: Dict[str, Any]) -> DAGOrchestrator:
        """Восстановить DAGOrchestrator из конфигурации (заглушка)"""
        class MockToolsSystem:
            def execute_tool(self, tool_name: str, **params):
                return f"Mock result from {tool_name}"
        
        tools_system = MockToolsSystem()
        return DAGOrchestrator(tools_system, config.get('max_concurrent_tasks', 5))
    
    def _restore_workflow(self, workflow_data: Dict[str, Any]) -> DAGWorkflow:
        """Восстановить DAGWorkflow из данных"""
        workflow = DAGWorkflow(
            id=workflow_data['id'],
            name=workflow_data['name'],
            description=workflow_data['description'],
            created_at=datetime.fromisoformat(workflow_data['created_at']),
            status=TaskStatus(workflow_data['status']),
            progress=workflow_data['progress']
        )
        
        # Восстанавливаем задачи
        for task_id, task_data in workflow_data['tasks'].items():
            task = TaskNode(
                id=task_data['id'],
                tool_name=task_data['tool_name'],
                params=task_data['params'],
                dependencies=task_data['dependencies'],
                status=TaskStatus(task_data['status']),
                result=task_data['result'],
                error=task_data['error'],
                priority=Priority(task_data['priority']),
                timeout=task_data['timeout'],
                retries=task_data['retries'],
                max_retries=task_data['max_retries']
            )
            
            if task_data['start_time']:
                task.start_time = datetime.fromisoformat(task_data['start_time'])
            if task_data['end_time']:
                task.end_time = datetime.fromisoformat(task_data['end_time'])
                
            workflow.tasks[task_id] = task
        
        return workflow
    
    def _restore_tools_system(self, config: Dict[str, Any]) -> Any:
        """Восстановить tools_system из конфигурации (заглушка)"""
        class MockToolsSystem:
            def execute_tool(self, tool_name: str, **params):
                return f"Mock result from {tool_name}"
        
        return MockToolsSystem()


class CeleryMetaToolsSystem(MetaToolsSystem):
    """
    Расширенная версия MetaToolsSystem с поддержкой Celery
    """
    
    def __init__(self, 
                 tools_system, 
                 dag_orchestrator: Optional[DAGOrchestrator] = None,
                 celery_integration: Optional[CeleryIntegration] = None):
        """
        Инициализация с поддержкой Celery
        
        Args:
            tools_system: Базовая система инструментов
            dag_orchestrator: Оркестратор DAG
            celery_integration: Интеграция с Celery
        """
        super().__init__(tools_system, dag_orchestrator)
        
        self.celery_integration = celery_integration
        if celery_integration:
            logger.info("MetaToolsSystem интегрирована с Celery")
    
    async def execute_meta_tool_async_celery(self, 
                                           name: str,
                                           priority: int = 5,
                                           **params) -> str:
        """
        Асинхронное выполнение мета-инструмента через Celery
        
        Args:
            name: Имя мета-инструмента
            priority: Приоритет задачи
            **params: Параметры выполнения
            
        Returns:
            ID задачи Celery
        """
        if not self.celery_integration:
            raise ValueError("Celery интеграция не настроена")
        
        return self.celery_integration.submit_meta_tool(
            self, name, params, priority=priority
        )
    
    def get_celery_task_status(self, task_id: str) -> Dict[str, Any]:
        """Получить статус Celery задачи"""
        if not self.celery_integration:
            raise ValueError("Celery интеграция не настроена")
        
        return self.celery_integration.get_task_status(task_id)
    
    def cancel_celery_task(self, task_id: str) -> bool:
        """Отменить Celery задачу"""
        if not self.celery_integration:
            raise ValueError("Celery интеграция не настроена")
        
        return self.celery_integration.cancel_task(task_id)


# Пример использования
async def example_celery_integration():
    """Пример использования Celery интеграции"""
    
    if not CELERY_AVAILABLE:
        print("Celery не установлен, пример не может быть выполнен")
        return
    
    # Создаем базовую систему инструментов
    class MockToolsSystem:
        def execute_tool(self, tool_name: str, **params):
            import time
            time.sleep(2)  # Имитация длительной работы
            return f"Result from {tool_name} with {params}"
    
    tools_system = MockToolsSystem()
    
    # Создаем Celery интеграцию
    celery_integration = CeleryIntegration()
    
    # Создаем мета-систему с поддержкой Celery
    meta_system = CeleryMetaToolsSystem(tools_system, celery_integration=celery_integration)
    
    print("Отправляем мета-инструмент на асинхронное выполнение...")
    
    # Запускаем мета-инструмент асинхронно
    task_id = await meta_system.execute_meta_tool_async_celery(
        "comprehensive_analysis_project",
        priority=8,
        project_name="Тестовый проект",
        project_type="жилое строительство"
    )
    
    print(f"Задача отправлена с ID: {task_id}")
    
    # Проверяем статус задачи
    import time
    while True:
        status = meta_system.get_celery_task_status(task_id)
        print(f"Статус задачи: {status}")
        
        if status['ready']:
            break
        
        time.sleep(5)
    
    print("Задача завершена!")


if __name__ == "__main__":
    # Запуск примера
    asyncio.run(example_celery_integration())