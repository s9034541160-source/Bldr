"""
Meta-Tools API endpoints для SuperBuilder
Предоставляет REST API для работы с мета-инструментами и DAG оркестрацией.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

# Import Meta-Tools System components
try:
    from core.meta_tools.meta_tools_system import MetaToolsSystem, MetaToolCategory
    from core.meta_tools.dag_orchestrator import DAGOrchestrator, Priority
    from core.meta_tools.celery_integration import CeleryIntegration, CeleryMetaToolsSystem
    META_TOOLS_AVAILABLE = True
except ImportError as e:
    print(f"Meta-Tools System недоступна: {e}")
    META_TOOLS_AVAILABLE = False

try:
    from core.tools_adapter import get_tools_adapter
except ImportError:
    get_tools_adapter = None

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем API router
router = APIRouter(prefix="/api/meta-tools", tags=["meta-tools"])

# Global instances (будут инициализированы при старте приложения)
meta_tools_system: Optional[MetaToolsSystem] = None
celery_integration: Optional[CeleryIntegration] = None

# Pydantic models для запросов и ответов
class MetaToolExecutionRequest(BaseModel):
    """Запрос на выполнение мета-инструмента"""
    tool_name: str = Field(..., description="Имя мета-инструмента")
    params: Dict[str, Any] = Field(default_factory=dict, description="Параметры для мета-инструмента")
    priority: int = Field(default=5, ge=1, le=9, description="Приоритет задачи (1-9)")
    async_execution: bool = Field(default=False, description="Асинхронное выполнение через Celery")

class WorkflowCreateRequest(BaseModel):
    """Запрос на создание workflow"""
    name: str = Field(..., description="Имя workflow")
    description: str = Field(default="", description="Описание workflow")
    tasks: List[Dict[str, Any]] = Field(..., description="Список задач workflow")

class TaskStatusResponse(BaseModel):
    """Ответ со статусом задачи"""
    task_id: str
    status: str
    ready: bool
    successful: Optional[bool] = None
    failed: Optional[bool] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    progress: Optional[Dict[str, Any]] = None

class MetaToolInfo(BaseModel):
    """Информация о мета-инструменте"""
    name: str
    description: str
    category: str
    required_params: List[str]
    optional_params: List[str]
    estimated_time: int
    complexity: str
    tags: List[str]

class MetaToolsListResponse(BaseModel):
    """Ответ со списком мета-инструментов"""
    success: bool
    meta_tools: List[MetaToolInfo]
    total: int

class ExecutionResponse(BaseModel):
    """Ответ на выполнение мета-инструмента"""
    success: bool
    message: str
    task_id: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None

# Utility functions
async def get_meta_tools_system() -> MetaToolsSystem:
    """Получить экземпляр Meta-Tools System"""
    global meta_tools_system
    
    if not META_TOOLS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Meta-Tools System недоступна")
    
    if not meta_tools_system:
        # Инициализируем систему инструментов
        if get_tools_adapter:
            tools_adapter = get_tools_adapter(None, None)  # Mock parameters
        else:
            tools_adapter = None
        
        # Создаем Meta-Tools System
        try:
            # Пытаемся создать с Celery интеграцией
            global celery_integration
            if not celery_integration:
                celery_integration = CeleryIntegration()
            
            meta_tools_system = CeleryMetaToolsSystem(
                tools_adapter,
                celery_integration=celery_integration
            )
            logger.info("Meta-Tools System с Celery интеграцией инициализирована")
            
        except Exception as e:
            # Fallback к базовой версии
            logger.warning(f"Celery недоступен, используем базовую Meta-Tools System: {e}")
            meta_tools_system = MetaToolsSystem(tools_adapter)
    
    return meta_tools_system

async def get_celery_integration() -> Optional[CeleryIntegration]:
    """Получить экземпляр Celery интеграции"""
    global celery_integration
    return celery_integration

# API Endpoints
@router.get("/", summary="Информация о Meta-Tools System")
async def get_meta_tools_info():
    """Получить общую информацию о Meta-Tools System"""
    if not META_TOOLS_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "Meta-Tools System недоступна"}
        )
    
    system = await get_meta_tools_system()
    stats = system.get_orchestrator_statistics() if hasattr(system, 'get_orchestrator_statistics') else {}
    
    return {
        "success": True,
        "system_info": {
            "meta_tools_available": True,
            "celery_available": celery_integration is not None,
            "system_type": type(system).__name__,
            "statistics": stats
        }
    }

@router.get("/list", response_model=MetaToolsListResponse, summary="Список доступных мета-инструментов")
async def list_meta_tools(
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    search: Optional[str] = Query(None, description="Поиск по названию или описанию")
):
    """Получить список всех доступных мета-инструментов с возможностью фильтрации"""
    try:
        system = await get_meta_tools_system()
        meta_tools_data = system.list_meta_tools()
        
        tools = meta_tools_data.get("meta_tools", [])
        
        # Применяем фильтры
        if category and category != "all":
            tools = [t for t in tools if t.get("category") == category]
        
        if search:
            search_lower = search.lower()
            tools = [
                t for t in tools 
                if search_lower in t.get("name", "").lower() 
                or search_lower in t.get("description", "").lower()
                or any(search_lower in tag.lower() for tag in t.get("tags", []))
            ]
        
        return MetaToolsListResponse(
            success=True,
            meta_tools=[MetaToolInfo(**tool) for tool in tools],
            total=len(tools)
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения списка мета-инструментов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", summary="Поиск мета-инструментов")
async def search_meta_tools(
    query: str = Query(..., description="Поисковый запрос"),
    category: Optional[str] = Query(None, description="Категория для фильтрации")
):
    """Поиск мета-инструментов по запросу"""
    try:
        system = await get_meta_tools_system()
        
        # Конвертируем категорию в enum если указана
        category_filter = None
        if category and category != "all":
            try:
                category_filter = MetaToolCategory(category)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Неизвестная категория: {category}")
        
        results = system.search_meta_tools(query, category_filter)
        
        return {
            "success": True,
            "query": query,
            "category": category,
            "results": results,
            "total": len(results)
        }
        
    except Exception as e:
        logger.error(f"Ошибка поиска мета-инструментов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{tool_name}", summary="Информация о мета-инструменте")
async def get_meta_tool_info(tool_name: str):
    """Получить подробную информацию о конкретном мета-инструменте"""
    try:
        system = await get_meta_tools_system()
        tool_info = system.get_meta_tool_info(tool_name)
        
        if not tool_info:
            raise HTTPException(status_code=404, detail=f"Мета-инструмент '{tool_name}' не найден")
        
        return {
            "success": True,
            "tool_info": tool_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения информации о мета-инструменте {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute", response_model=ExecutionResponse, summary="Синхронное выполнение мета-инструмента")
async def execute_meta_tool_sync(request: MetaToolExecutionRequest):
    """Синхронное выполнение мета-инструмента (для быстрых операций)"""
    try:
        system = await get_meta_tools_system()
        
        # Проверяем существование мета-инструмента
        tool_info = system.get_meta_tool_info(request.tool_name)
        if not tool_info:
            raise HTTPException(status_code=404, detail=f"Мета-инструмент '{request.tool_name}' не найден")
        
        # Для длительных задач рекомендуем асинхронное выполнение
        if tool_info.get("estimated_time", 0) > 10 or tool_info.get("complexity") == "high":
            return ExecutionResponse(
                success=False,
                message=f"Мета-инструмент '{request.tool_name}' требует длительного выполнения. Используйте /execute/async",
                error="Use async execution for long-running tasks"
            )
        
        # Выполняем мета-инструмент
        start_time = datetime.now()
        result = await system.execute_meta_tool(request.tool_name, **request.params)
        execution_time = (datetime.now() - start_time).total_seconds()
        
        if result.get("status") == "success":
            return ExecutionResponse(
                success=True,
                message="Мета-инструмент выполнен успешно",
                result=result.get("result"),
                execution_time=execution_time
            )
        else:
            return ExecutionResponse(
                success=False,
                message="Ошибка выполнения мета-инструмента",
                error=result.get("error", "Unknown error"),
                execution_time=execution_time
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка выполнения мета-инструмента {request.tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute/async", response_model=ExecutionResponse, summary="Асинхронное выполнение мета-инструмента")
async def execute_meta_tool_async(request: MetaToolExecutionRequest):
    """Асинхронное выполнение мета-инструмента через Celery"""
    try:
        system = await get_meta_tools_system()
        celery = await get_celery_integration()
        
        if not celery or not hasattr(system, 'execute_meta_tool_async_celery'):
            raise HTTPException(status_code=503, detail="Celery интеграция недоступна")
        
        # Проверяем существование мета-инструмента
        tool_info = system.get_meta_tool_info(request.tool_name)
        if not tool_info:
            raise HTTPException(status_code=404, detail=f"Мета-инструмент '{request.tool_name}' не найден")
        
        # Запускаем асинхронно
        task_id = await system.execute_meta_tool_async_celery(
            request.tool_name,
            priority=request.priority,
            **request.params
        )
        
        return ExecutionResponse(
            success=True,
            message="Мета-инструмент запущен асинхронно",
            task_id=task_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка асинхронного выполнения мета-инструмента {request.tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks/active", summary="Список активных задач")
async def get_active_tasks():
    """Получить список активных Celery задач"""
    try:
        celery = await get_celery_integration()
        
        if not celery:
            return {
                "success": True,
                "tasks": [],
                "message": "Celery интеграция недоступна"
            }
        
        active_tasks = celery.list_active_tasks()
        
        return {
            "success": True,
            "tasks": active_tasks,
            "total": len(active_tasks)
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения активных задач: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks/{task_id}/status", response_model=TaskStatusResponse, summary="Статус задачи")
async def get_task_status(task_id: str):
    """Получить статус конкретной задачи"""
    try:
        celery = await get_celery_integration()
        
        if not celery:
            raise HTTPException(status_code=503, detail="Celery интеграция недоступна")
        
        status_info = celery.get_task_status(task_id)
        
        return TaskStatusResponse(
            task_id=status_info["task_id"],
            status=status_info["status"],
            ready=status_info["ready"],
            successful=status_info.get("successful"),
            failed=status_info.get("failed"),
            result=status_info.get("result"),
            error=status_info.get("error"),
            progress=status_info.get("progress")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения статуса задачи {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tasks/{task_id}/cancel", summary="Отменить задачу")
async def cancel_task(task_id: str, terminate: bool = Query(False, description="Жесткое завершение")):
    """Отменить выполнение задачи"""
    try:
        celery = await get_celery_integration()
        
        if not celery:
            raise HTTPException(status_code=503, detail="Celery интеграция недоступна")
        
        success = celery.cancel_task(task_id, terminate=terminate)
        
        return {
            "success": success,
            "message": f"Задача {task_id} {'отменена' if success else 'не может быть отменена'}",
            "task_id": task_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка отмены задачи {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tasks/cleanup", summary="Очистить завершенные задачи")
async def cleanup_completed_tasks():
    """Очистить завершенные задачи из кеша"""
    try:
        celery = await get_celery_integration()
        
        if not celery:
            return {
                "success": True,
                "cleaned": 0,
                "message": "Celery интеграция недоступна"
            }
        
        cleaned_count = celery.cleanup_completed_tasks()
        
        return {
            "success": True,
            "cleaned": cleaned_count,
            "message": f"Очищено {cleaned_count} завершенных задач"
        }
        
    except Exception as e:
        logger.error(f"Ошибка очистки задач: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics", summary="Статистика работы системы")
async def get_system_statistics():
    """Получить статистику работы Meta-Tools System и Celery"""
    try:
        system = await get_meta_tools_system()
        celery = await get_celery_integration()
        
        # Статистика оркестратора
        orchestrator_stats = system.get_orchestrator_statistics() if hasattr(system, 'get_orchestrator_statistics') else {}
        
        # Статистика Celery воркеров
        celery_stats = {}
        if celery:
            try:
                celery_stats = celery.get_worker_stats()
            except Exception as e:
                celery_stats = {"error": str(e)}
        
        return {
            "success": True,
            "statistics": {
                "meta_tools_system": {
                    "type": type(system).__name__,
                    "orchestrator": orchestrator_stats
                },
                "celery": celery_stats if celery else {"available": False},
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Workflow endpoints
@router.post("/workflows", summary="Создать workflow")
async def create_workflow(request: WorkflowCreateRequest):
    """Создать новый DAG workflow"""
    try:
        system = await get_meta_tools_system()
        
        if not hasattr(system, 'orchestrator'):
            raise HTTPException(status_code=503, detail="DAG Orchestrator недоступен")
        
        orchestrator = system.orchestrator
        
        # Создаем workflow
        workflow = orchestrator.create_workflow(request.name, request.description)
        
        # Добавляем задачи
        task_ids = {}
        for task_data in request.tasks:
            task_id = orchestrator.add_task_to_workflow(
                workflow.id,
                task_data["tool_name"],
                task_data.get("params", {}),
                dependencies=task_data.get("dependencies", []),
                priority=Priority(task_data.get("priority", 2)),
                timeout=task_data.get("timeout"),
                max_retries=task_data.get("max_retries", 3)
            )
            task_ids[task_data.get("id", len(task_ids))] = task_id
        
        return {
            "success": True,
            "workflow_id": workflow.id,
            "task_ids": task_ids,
            "message": f"Workflow '{request.name}' создан успешно"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка создания workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workflows/{workflow_id}/execute", summary="Выполнить workflow")
async def execute_workflow(workflow_id: str):
    """Запустить выполнение workflow"""
    try:
        system = await get_meta_tools_system()
        
        if not hasattr(system, 'orchestrator'):
            raise HTTPException(status_code=503, detail="DAG Orchestrator недоступен")
        
        orchestrator = system.orchestrator
        
        # Выполняем workflow асинхронно
        result = await orchestrator.execute_workflow(workflow_id)
        
        return {
            "success": result.get("status") != "failed",
            "workflow_id": workflow_id,
            "result": result,
            "message": "Workflow выполнен" if result.get("status") != "failed" else "Ошибка выполнения workflow"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка выполнения workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflows/{workflow_id}/status", summary="Статус workflow")
async def get_workflow_status(workflow_id: str):
    """Получить статус workflow"""
    try:
        system = await get_meta_tools_system()
        
        if not hasattr(system, 'orchestrator'):
            raise HTTPException(status_code=503, detail="DAG Orchestrator недоступен")
        
        orchestrator = system.orchestrator
        status = orchestrator.get_workflow_status(workflow_id)
        
        if not status:
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} не найден")
        
        return {
            "success": True,
            "workflow_status": status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения статуса workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check
@router.get("/health", summary="Проверка состояния системы")
async def health_check():
    """Проверка работоспособности Meta-Tools System"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }
    
    # Проверяем Meta-Tools System
    try:
        system = await get_meta_tools_system()
        health_status["components"]["meta_tools"] = {
            "status": "healthy",
            "type": type(system).__name__
        }
    except Exception as e:
        health_status["components"]["meta_tools"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Проверяем Celery
    try:
        celery = await get_celery_integration()
        if celery:
            # Пытаемся получить статистику воркеров
            celery.get_worker_stats()
            health_status["components"]["celery"] = {"status": "healthy"}
        else:
            health_status["components"]["celery"] = {"status": "unavailable"}
    except Exception as e:
        health_status["components"]["celery"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        if health_status["status"] == "healthy":
            health_status["status"] = "degraded"
    
    status_code = 200 if health_status["status"] in ["healthy", "degraded"] else 503
    return JSONResponse(status_code=status_code, content=health_status)

# Export router
__all__ = ["router"]