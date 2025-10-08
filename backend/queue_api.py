#!/usr/bin/env python3
"""
Queue API - API для работы с очередью задач
Предоставляет endpoints для управления активными и завершенными задачами
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# Импортируем Redis
try:
    import redis
    HAS_REDIS = True
except ImportError:
    logger.warning("Redis not available")
    HAS_REDIS = False

def get_redis_client():
    """Получение подключения к Redis"""
    if not HAS_REDIS:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    redis_db = int(os.getenv("REDIS_DB", "0"))
    
    try:
        client = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
        # Проверяем подключение
        client.ping()
        return client
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise HTTPException(status_code=503, detail=f"Redis connection failed: {str(e)}")

# Pydantic модели для API
class QueueTask(BaseModel):
    id: str
    type: str
    status: str
    progress: int
    owner: str
    started_at: str
    eta: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class JobCancelRequest(BaseModel):
    reason: Optional[str] = None

# Создаем роутер
queue_router = APIRouter(prefix="/queue", tags=["Queue Management"])

@queue_router.get("/active", response_model=Dict[str, List[QueueTask]])
async def get_active_jobs(redis_client = Depends(get_redis_client)):
    """Получает список активных задач"""
    try:
        # Получаем все ключи активных задач
        active_keys = redis_client.keys("celery-task-meta-*")
        
        active_jobs = {}
        
        for key in active_keys:
            try:
                task_data = redis_client.get(key)
                if task_data:
                    task_info = json.loads(task_data)
                    
                    # Извлекаем информацию о задаче
                    task_id = key.replace("celery-task-meta-", "")
                    tool_type = task_info.get("name", "unknown").split(".")[-1]
                    
                    if tool_type not in active_jobs:
                        active_jobs[tool_type] = []
                    
                    task = QueueTask(
                        id=task_id,
                        type=tool_type,
                        status=task_info.get("status", "PENDING"),
                        progress=task_info.get("progress", 0),
                        owner=task_info.get("owner", "system"),
                        started_at=task_info.get("date_done", datetime.now().isoformat()),
                        eta=task_info.get("eta"),
                        result=task_info.get("result"),
                        error=task_info.get("error")
                    )
                    
                    active_jobs[tool_type].append(task)
                    
            except Exception as e:
                logger.warning(f"Error parsing task {key}: {e}")
                continue
        
        return active_jobs
        
    except Exception as e:
        logger.error(f"Error getting active jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting active jobs: {str(e)}")

@queue_router.get("/completed", response_model=Dict[str, List[QueueTask]])
async def get_completed_jobs(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of completed jobs to return"),
    redis_client = Depends(get_redis_client)
):
    """Получает список завершенных задач"""
    try:
        # Получаем все ключи завершенных задач
        completed_keys = redis_client.keys("celery-task-meta-*")
        
        completed_jobs = {}
        completed_tasks = []
        
        for key in completed_keys:
            try:
                task_data = redis_client.get(key)
                if task_data:
                    task_info = json.loads(task_data)
                    
                    # Проверяем, что задача завершена
                    if task_info.get("status") in ["SUCCESS", "FAILURE"]:
                        task_id = key.replace("celery-task-meta-", "")
                        tool_type = task_info.get("name", "unknown").split(".")[-1]
                        
                        task = QueueTask(
                            id=task_id,
                            type=tool_type,
                            status=task_info.get("status", "UNKNOWN"),
                            progress=100 if task_info.get("status") == "SUCCESS" else 0,
                            owner=task_info.get("owner", "system"),
                            started_at=task_info.get("date_done", datetime.now().isoformat()),
                            eta=None,
                            result=task_info.get("result"),
                            error=task_info.get("error")
                        )
                        
                        completed_tasks.append((task, task_info.get("date_done", "")))
                        
            except Exception as e:
                logger.warning(f"Error parsing completed task {key}: {e}")
                continue
        
        # Сортируем по дате завершения (новые первыми)
        completed_tasks.sort(key=lambda x: x[1], reverse=True)
        
        # Ограничиваем количество
        completed_tasks = completed_tasks[:limit]
        
        # Группируем по типам инструментов
        for task, _ in completed_tasks:
            if task.type not in completed_jobs:
                completed_jobs[task.type] = []
            completed_jobs[task.type].append(task)
        
        return completed_jobs
        
    except Exception as e:
        logger.error(f"Error getting completed jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting completed jobs: {str(e)}")

@queue_router.post("/cancel/{job_id}")
async def cancel_job(
    job_id: str,
    cancel_request: JobCancelRequest,
    redis_client = Depends(get_redis_client)
):
    """Отменяет активную задачу"""
    try:
        # Проверяем, существует ли задача
        task_key = f"celery-task-meta-{job_id}"
        task_data = redis_client.get(task_key)
        
        if not task_data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        task_info = json.loads(task_data)
        
        # Проверяем, что задача еще активна
        if task_info.get("status") in ["SUCCESS", "FAILURE"]:
            raise HTTPException(status_code=400, detail="Job already completed")
        
        # Помечаем задачу как отмененную
        task_info["status"] = "REVOKED"
        task_info["error"] = f"Canceled by user: {cancel_request.reason or 'No reason provided'}"
        task_info["date_done"] = datetime.now().isoformat()
        
        # Сохраняем обновленную информацию
        redis_client.set(task_key, json.dumps(task_info))
        
        return {"status": "success", "message": f"Job {job_id} canceled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error canceling job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error canceling job: {str(e)}")

@queue_router.get("/download/{job_id}")
async def download_job_result(
    job_id: str,
    redis_client = Depends(get_redis_client)
):
    """Скачивает результат завершенной задачи"""
    try:
        # Получаем информацию о задаче
        task_key = f"celery-task-meta-{job_id}"
        task_data = redis_client.get(task_key)
        
        if not task_data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        task_info = json.loads(task_data)
        
        # Проверяем, что задача завершена успешно
        if task_info.get("status") != "SUCCESS":
            raise HTTPException(status_code=400, detail="Job not completed successfully")
        
        result = task_info.get("result")
        if not result:
            raise HTTPException(status_code=404, detail="No result available")
        
        # Создаем простой JSON файл с результатом
        import io
        import zipfile
        
        # Создаем ZIP архив с результатом
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Добавляем результат как JSON файл
            zip_file.writestr(f"job_{job_id}_result.json", json.dumps(result, indent=2, ensure_ascii=False))
            
            # Добавляем метаданные задачи
            metadata = {
                "job_id": job_id,
                "status": task_info.get("status"),
                "completed_at": task_info.get("date_done"),
                "tool_type": task_info.get("name", "unknown").split(".")[-1]
            }
            zip_file.writestr(f"job_{job_id}_metadata.json", json.dumps(metadata, indent=2, ensure_ascii=False))
        
        zip_buffer.seek(0)
        
        from fastapi.responses import StreamingResponse
        
        return StreamingResponse(
            io.BytesIO(zip_buffer.getvalue()),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=job_{job_id}_result.zip"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading job result {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error downloading job result: {str(e)}")

@queue_router.get("/statistics", response_model=Dict[str, Any])
async def get_queue_statistics(redis_client = Depends(get_redis_client)):
    """Получает статистику очереди"""
    try:
        # Получаем все ключи задач
        task_keys = redis_client.keys("celery-task-meta-*")
        
        total_tasks = len(task_keys)
        active_tasks = 0
        completed_tasks = 0
        failed_tasks = 0
        
        tool_stats = {}
        
        for key in task_keys:
            try:
                task_data = redis_client.get(key)
                if task_data:
                    task_info = json.loads(task_data)
                    status = task_info.get("status", "UNKNOWN")
                    tool_type = task_info.get("name", "unknown").split(".")[-1]
                    
                    # Подсчитываем статистику
                    if status in ["PENDING", "STARTED", "RETRY"]:
                        active_tasks += 1
                    elif status == "SUCCESS":
                        completed_tasks += 1
                    elif status == "FAILURE":
                        failed_tasks += 1
                    
                    # Статистика по инструментам
                    if tool_type not in tool_stats:
                        tool_stats[tool_type] = {"total": 0, "active": 0, "completed": 0, "failed": 0}
                    
                    tool_stats[tool_type]["total"] += 1
                    if status in ["PENDING", "STARTED", "RETRY"]:
                        tool_stats[tool_type]["active"] += 1
                    elif status == "SUCCESS":
                        tool_stats[tool_type]["completed"] += 1
                    elif status == "FAILURE":
                        tool_stats[tool_type]["failed"] += 1
                        
            except Exception as e:
                logger.warning(f"Error parsing task {key}: {e}")
                continue
        
        statistics = {
            "total_tasks": total_tasks,
            "active_tasks": active_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "tool_statistics": tool_stats,
            "last_updated": datetime.now().isoformat()
        }
        
        return statistics
        
    except Exception as e:
        logger.error(f"Error getting queue statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting queue statistics: {str(e)}")

# Health check endpoint
@queue_router.get("/health")
async def health_check():
    """Проверка состояния Queue API"""
    return {"status": "healthy", "service": "Queue Management API"}
