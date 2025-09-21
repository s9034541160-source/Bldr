"""
Tools API endpoints для SuperBuilder
Предоставляет REST API для специализированных инструментов с загрузкой файлов.
"""

import asyncio
import json
import logging
import uuid
import os
import tempfile
from datetime import datetime
from typing import Dict, Any, List, Optional

# Redis for enterprise-grade job storage
import redis

from fastapi import APIRouter, HTTPException, File, UploadFile, Form, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import coordinator for tool execution (with error handling)
try:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from core.agents.coordinator_agent import CoordinatorAgent
    COORDINATOR_AVAILABLE = True
except ImportError as e:
    logger.warning(f"CoordinatorAgent не доступен: {e}")
    CoordinatorAgent = None
    COORDINATOR_AVAILABLE = False

try:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from core.tools_adapter import get_tools_adapter
    ToolsAdapter = get_tools_adapter
except ImportError as e:
    logger.warning(f"ToolsAdapter не доступен: {e}")
    ToolsAdapter = None

# Import existing WebSocket manager instead of separate server
try:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from core.websocket_manager import manager as websocket_manager
    WEBSOCKET_AVAILABLE = True
except ImportError as e:
    logger.warning(f"WebSocket manager не доступен: {e}")
    websocket_manager = None
    WEBSOCKET_AVAILABLE = False

# Создаем API router
router = APIRouter(prefix="/api/tools", tags=["tools"])

# Global instances
coordinator_agent = None
tools_adapter = None

# Redis-based job storage (no in-memory fallbacks)
REDIS_URL = os.getenv('REDIS_URL') or os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
REDIS_ACTIVE_SET = 'bldr:jobs:active'
REDIS_COMPLETED_SET = 'bldr:jobs:completed'
REDIS_JOB_KEY_PREFIX = 'bldr:job:'
JOB_TTL_SECONDS = int(os.getenv('JOB_TTL_SECONDS', str(48*3600)))  # 48 hours for completed jobs

_redis_client: Optional[redis.Redis] = None

def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        # Test connection
        try:
            _redis_client.ping()
        except Exception as e:
            raise RuntimeError(f"Redis connection failed: {e}")
    return _redis_client

# Pydantic models
class JobStatus(BaseModel):
    job_id: str
    status: str  # pending, running, completed, failed
    progress: int = 0
    message: str = ""
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class ToolExecutionResponse(BaseModel):
    success: bool
    job_id: str
    message: str
    estimated_time: Optional[int] = None

# Utility functions
async def get_coordinator():
    """Получить экземпляр координатора"""
    global coordinator_agent, tools_adapter
    
    if not COORDINATOR_AVAILABLE:
        # Заглушка для случая, если координатор недоступен
        class MockCoordinator:
            def process_query(self, query: str):
                return f"Processed: {query}"
        return MockCoordinator()
    
    if not coordinator_agent:
        if not tools_adapter and ToolsAdapter:
            if callable(ToolsAdapter):
                tools_adapter = ToolsAdapter()
            else:
                tools_adapter = ToolsAdapter
        if CoordinatorAgent:
            coordinator_agent = CoordinatorAgent(tools_system=tools_adapter)
    
    return coordinator_agent

def _job_key(job_id: str) -> str:
    return f"{REDIS_JOB_KEY_PREFIX}{job_id}"

def create_job(tool_type: str, params: Dict[str, Any]) -> str:
    """Создать новую задачу (хранится в Redis)."""
    r = get_redis()
    job_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    job = {
        'id': job_id,
        'tool_type': tool_type,
        'status': 'pending',
        'progress': 0,
        'message': 'Задача создана',
        'params': params,
        'created_at': now,
        'updated_at': now,
        'result': None,
        'error': None
    }
    r.set(_job_key(job_id), json.dumps(job, ensure_ascii=False))
    r.sadd(REDIS_ACTIVE_SET, job_id)
    return job_id

def update_job(job_id: str, status: str = '', progress: int = 0, 
               message: str = '', result: Any = None, error: str = ''):
    """Обновить статус задачи в Redis и отправить уведомления."""
    r = get_redis()
    job_raw = r.get(_job_key(job_id))
    if not job_raw:
        logger.warning(f"Job {job_id} not found in Redis for update")
        return
    if job_raw:
        if job_raw:
            job = json.loads(job_raw)
            if status: job['status'] = status
            if progress is not None: job['progress'] = progress
            if message: job['message'] = message
            if result is not None: job['result'] = result
            if error is not None: job['error'] = error
            job['updated_at'] = datetime.now().isoformat()

    r.set(_job_key(job_id), json.dumps(job, ensure_ascii=False))

    # Send WebSocket notification through existing manager
    if WEBSOCKET_AVAILABLE and websocket_manager:
        try:
            notification = {
                "type": "job_update",
                "job_id": job_id,
                "status": job['status'],
                "progress": job['progress'],
                "message": job['message'],
                "result": result,
                "error": error,
                "timestamp": datetime.now().isoformat()
            }
            asyncio.create_task(
                websocket_manager.broadcast(json.dumps(notification, ensure_ascii=False))
            )
        except Exception as e:
            logger.error(f"Failed to send WebSocket notification: {e}")

    # Move completed/cancelled jobs
    if status in ['completed', 'failed', 'cancelled']:
        r.srem(REDIS_ACTIVE_SET, job_id)
        r.sadd(REDIS_COMPLETED_SET, job_id)
        r.expire(_job_key(job_id), JOB_TTL_SECONDS)
        # Completion notification
        if WEBSOCKET_AVAILABLE and websocket_manager:
            try:
                completion_notification = {
                    "type": "job_completed",
                    "job_id": job_id,
                    "tool_type": job.get('tool_type'),
                    "success": status == 'completed',
                    "timestamp": datetime.now().isoformat()
                }
                asyncio.create_task(
                    websocket_manager.broadcast(json.dumps(completion_notification, ensure_ascii=False))
                )
            except Exception as e:
                logger.error(f"Failed to send completion notification: {e}")

async def execute_tool_job(job_id: str, coordinator, 
                          tool_name: str, params: Dict[str, Any]):
    """Выполнить инструмент асинхронно через реальную Master Tools System"""
    try:
        update_job(job_id, status='running', progress=10, message='Подключение к Master Tools System...')
        
        # Получаем инстанс Master Tools System через адаптер
        from core.tools_adapter import get_tools_adapter
        from core.model_manager import ModelManager
        
        # Инициализируем менеджер моделей если нужно
        model_manager = ModelManager() if not hasattr(coordinator, 'model_manager') else coordinator.model_manager
        tools_adapter = get_tools_adapter(coordinator.rag_system if hasattr(coordinator, 'rag_system') else None, model_manager)
        
        update_job(job_id, progress=20, message='Подготовка параметров...')
        
        # Конвертируем параметры в формат Master Tools
        master_params = convert_params_to_master_format(tool_name, params)
        
        update_job(job_id, progress=30, message=f'Выполнение {tool_name}...')
        
        # Выполняем через Master Tools System
        if tool_name == 'estimate_analyzer':
            result = await execute_estimate_analysis(tools_adapter, master_params, job_id)
        elif tool_name == 'image_analyzer':
            result = await execute_image_analysis(tools_adapter, master_params, job_id)
        elif tool_name == 'document_analyzer':
            result = await execute_document_analysis(tools_adapter, master_params, job_id)
        elif tool_name == 'tender_analyzer':
            result = await execute_tender_analysis(tools_adapter, master_params, job_id)
        else:
            raise ValueError(f"Неизвестный инструмент: {tool_name}")
        
        update_job(job_id, status='completed', progress=100, 
                  message='Анализ завершен', result=result)
        
    except Exception as e:
        logger.error(f"Ошибка выполнения задачи {job_id}: {e}")
        update_job(job_id, status='failed', error=str(e), 
                  message=f'Ошибка: {str(e)}')

# === REAL EXECUTION HELPERS (NO MOCKS) ===

def convert_params_to_master_format(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Конвертация параметров в формат, ожидаемый Master Tools System"""
    if tool_name == 'estimate_analyzer':
        return {
            'files': [f['temp_path'] for f in params.get('files', [])],
            'region': params.get('region', 'moscow'),
            'analysis_type': params.get('analysis_type', 'full')
        }
    if tool_name == 'image_analyzer':
        return {
            'images': [f['temp_path'] for f in params.get('images', [])],
            'analysis_type': params.get('analysis_type', 'comprehensive'),
            'detect_objects': params.get('detect_objects', True),
            'extract_dimensions': params.get('extract_dimensions', True),
            'recognize_text': params.get('recognize_text', True),
            'confidence_threshold': params.get('confidence_threshold', 0.7)
        }
    if tool_name == 'document_analyzer':
        return {
            'documents': [f['temp_path'] for f in params.get('documents', [])],
            'analysis_type': params.get('analysis_type', 'full'),
            'extract_data': params.get('extract_data', True),
            'check_compliance': params.get('check_compliance', False)
        }
    if tool_name == 'tender_analyzer':
        return {
            'tender_documents': [f['temp_path'] for f in params.get('tender_documents', [])],
            'analysis_depth': params.get('analysis_depth', 'comprehensive'),
            'include_financial_analysis': params.get('include_financial_analysis', True),
            'include_risk_assessment': params.get('include_risk_assessment', True),
            'include_compliance_check': params.get('include_compliance_check', True),
            'include_competitor_analysis': params.get('include_competitor_analysis', True),
            'include_recommendations': params.get('include_recommendations', True)
        }
    return params

async def execute_estimate_analysis(tools_adapter, master_params: Dict[str, Any], job_id: str) -> Dict[str, Any]:
    update_job(job_id, progress=45, message='Разбор сметных файлов...')
    # Унифицированный парсер смет
    try:
        result = tools_adapter.execute_tool('parse_estimate_unified', input_data=master_params.get('files', []), region=master_params.get('region'))
        return result
    except Exception as e:
        return { 'status': 'error', 'error': str(e) }

async def execute_image_analysis(tools_adapter, master_params: Dict[str, Any], job_id: str) -> Dict[str, Any]:
    results = []
    images = master_params.get('images', [])
    total = max(len(images), 1)
    for idx, image_path in enumerate(images, start=1):
        try:
            res = tools_adapter.execute_tool('analyze_image', image_path=image_path, analysis_type=master_params.get('analysis_type'))
            results.append(res)
        except Exception as e:
            results.append({ 'status': 'error', 'error': str(e), 'image_path': image_path })
        update_job(job_id, progress=30 + int(50 * idx / total), message=f'Обработано {idx}/{total} изображений')
    return { 'status': 'success', 'results': results, 'total_processed': len(results) }

async def execute_document_analysis(tools_adapter, master_params: Dict[str, Any], job_id: str) -> Dict[str, Any]:
    update_job(job_id, progress=60, message='Анализ документов...')
    try:
        # Используем универсальный анализ контента
        res = tools_adapter.execute_tool('comprehensive_analysis', documents=master_params.get('documents', []), analysis_type=master_params.get('analysis_type'))
        return res
    except Exception as e:
        return { 'status': 'error', 'error': str(e) }

async def execute_tender_analysis(tools_adapter, master_params: Dict[str, Any], job_id: str) -> Dict[str, Any]:
    update_job(job_id, progress=70, message='Комплексный анализ тендера...')
    try:
        res = tools_adapter.execute_tool('analyze_tender', **master_params)
        return res
    except Exception as e:
        return { 'status': 'error', 'error': str(e) }

# API Endpoints

@router.get("/list")
async def list_tools():
    """Получить список доступных инструментов анализа (из unified tools, при наличии)"""
    tools_map: Dict[str, Dict[str, Any]] = {}
    categories: Dict[str, str] = {
        'financial': 'Финансовые инструменты',
        'visual': 'Визуальный анализ',
        'documents': 'Анализ документов',
        'business': 'Бизнес-анализ'
    }
    # Try unified tools first
    try:
        from core.unified_tools_system import unified_tools
        if hasattr(unified_tools, 'list_available_tools'):
            info = {
                'tools': [{'name': tool.name, 'title': tool.description, 'description': tool.description, 'category': tool.category} for tool in unified_tools.list_tools()]
            }
            for t in info.get('tools', []):
                name = t.get('name') or t.get('id')
                if not name:
                    continue
                tools_map[name] = {
                    'name': t.get('title', name),
                    'description': t.get('description', ''),
                    'category': t.get('category', 'general'),
                    'supports_files': t.get('supports_files', False),
                    'file_types': t.get('file_types', [])
                }
    except Exception as e:
        logger.warning(f"Unified tools not available: {e}")
    # Fallback to static if empty
    if not tools_map:
        tools_map = {
            'estimate_analyzer': {
                'name': 'Анализатор смет',
                'description': 'Анализ сметной документации и расчетов',
                'category': 'financial',
                'supports_files': True,
                'file_types': ['.xls', '.xlsx', '.pdf', '.doc', '.docx']
            },
            'image_analyzer': {
                'name': 'Анализатор изображений',
                'description': 'Анализ чертежей и изображений строительных объектов',
                'category': 'visual',
                'supports_files': True,
                'file_types': ['.jpg', '.jpeg', '.png', '.tiff', '.pdf']
            },
            'document_analyzer': {
                'name': 'Анализатор документов',
                'description': 'Анализ проектной документации и спецификаций',
                'category': 'documents',
                'supports_files': True,
                'file_types': ['.pdf', '.doc', '.docx', '.txt', '.rtf']
            },
            'tender_analyzer': {
                'name': 'Анализатор тендеров',
                'description': 'Комплексный анализ тендерной документации',
                'category': 'business',
                'supports_files': True,
                'file_types': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.png']
            }
        }
    return {
        'success': True,
        'tools': tools_map,
        'total_count': len(tools_map),
        'categories': categories
    }

@router.post("/analyze/estimate")
async def analyze_estimate(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    params: str = Form(...)
):
    """Анализ сметной документации"""
    try:
        # Parse parameters
        analysis_params = json.loads(params)
        
        # Save uploaded files temporarily
        file_paths = []
        for file in files:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}")
            content = await file.read()
            temp_file.write(content)
            temp_file.close()
            file_paths.append({
                'original_name': file.filename,
                'temp_path': temp_file.name,
                'size': len(content),
                'type': file.content_type
            })
        
        # Create job
        job_params = {
            'files': file_paths,
            'analysis_type': analysis_params.get('analysisType', 'full'),
            'region': analysis_params.get('region', 'moscow'),
            'include_gesn': analysis_params.get('includeGESN', True),
            'include_fer': analysis_params.get('includeFER', False)
        }
        
        job_id = create_job('estimate_analyzer', job_params)
        
        # Send new job notification through existing manager
        if WEBSOCKET_AVAILABLE and websocket_manager:
            try:
                new_job_notification = {
                    "type": "new_job",
                    "job_id": job_id,
                    "tool_type": "estimate_analyzer",
                    "estimated_time": 120,
                    "timestamp": datetime.now().isoformat()
                }
                await websocket_manager.broadcast(json.dumps(new_job_notification, ensure_ascii=False))
            except Exception as e:
                logger.error(f"Failed to send new job notification: {e}")
        
        # Execute in background
        coordinator = await get_coordinator()
        background_tasks.add_task(
            execute_tool_job, job_id, coordinator, 'estimate_analyzer', job_params
        )
        
        return ToolExecutionResponse(
            success=True,
            job_id=job_id,
            message="Анализ смет запущен",
            estimated_time=120  # 2 minutes
        )
        
    except Exception as e:
        logger.error(f"Ошибка анализа смет: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/images")
async def analyze_images(
    background_tasks: BackgroundTasks,
    images: List[UploadFile] = File(...),
    params: str = Form(...)
):
    """Анализ изображений и чертежей"""
    try:
        # Parse parameters
        analysis_params = json.loads(params)
        
        # Save uploaded images temporarily
        image_paths = []
        for image in images:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{image.filename}")
            content = await image.read()
            temp_file.write(content)
            temp_file.close()
            image_paths.append({
                'original_name': image.filename,
                'temp_path': temp_file.name,
                'size': len(content),
                'type': image.content_type
            })
        
        # Create job
        job_params = {
            'images': image_paths,
            'analysis_type': analysis_params.get('analysisType', 'comprehensive'),
            'detect_objects': analysis_params.get('detectObjects', True),
            'extract_dimensions': analysis_params.get('extractDimensions', True),
            'recognize_text': analysis_params.get('recognizeText', True),
            'confidence_threshold': analysis_params.get('confidenceThreshold', 0.7)
        }
        
        job_id = create_job('image_analyzer', job_params)
        
        # Send new job notification through existing manager
        if WEBSOCKET_AVAILABLE and websocket_manager:
            try:
                new_job_notification = {
                    "type": "new_job",
                    "job_id": job_id,
                    "tool_type": "image_analyzer",
                    "estimated_time": 180,
                    "timestamp": datetime.now().isoformat()
                }
                await websocket_manager.broadcast(json.dumps(new_job_notification, ensure_ascii=False))
            except Exception as e:
                logger.error(f"Failed to send new job notification: {e}")
        
        # Execute in background
        coordinator = await get_coordinator()
        background_tasks.add_task(
            execute_tool_job, job_id, coordinator, 'image_analyzer', job_params
        )
        
        return ToolExecutionResponse(
            success=True,
            job_id=job_id,
            message="Анализ изображений запущен",
            estimated_time=180  # 3 minutes
        )
        
    except Exception as e:
        logger.error(f"Ошибка анализа изображений: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/documents")
async def analyze_documents(
    background_tasks: BackgroundTasks,
    documents: List[UploadFile] = File(...),
    params: str = Form(...)
):
    """Анализ документов"""
    try:
        analysis_params = json.loads(params)
        
        # Save uploaded documents temporarily
        doc_paths = []
        for doc in documents:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{doc.filename}")
            content = await doc.read()
            temp_file.write(content)
            temp_file.close()
            doc_paths.append({
                'original_name': doc.filename,
                'temp_path': temp_file.name,
                'size': len(content),
                'type': doc.content_type
            })
        
        job_params = {
            'documents': doc_paths,
            'analysis_type': analysis_params.get('analysisType', 'full'),
            'extract_data': analysis_params.get('extractData', True),
            'check_compliance': analysis_params.get('checkCompliance', False)
        }
        
        job_id = create_job('document_analyzer', job_params)
        
        # Send new job notification through existing manager
        if WEBSOCKET_AVAILABLE and websocket_manager:
            try:
                new_job_notification = {
                    "type": "new_job",
                    "job_id": job_id,
                    "tool_type": "document_analyzer",
                    "estimated_time": 90,
                    "timestamp": datetime.now().isoformat()
                }
                await websocket_manager.broadcast(json.dumps(new_job_notification, ensure_ascii=False))
            except Exception as e:
                logger.error(f"Failed to send new job notification: {e}")
        
        # Execute in background
        coordinator = await get_coordinator()
        background_tasks.add_task(
            execute_tool_job, job_id, coordinator, 'document_analyzer', job_params
        )
        
        return ToolExecutionResponse(
            success=True,
            job_id=job_id,
            message="Анализ документов запущен",
            estimated_time=90
        )
        
    except Exception as e:
        logger.error(f"Ошибка анализа документов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/tender")
async def analyze_tender(
    background_tasks: BackgroundTasks,
    tender_documents: List[UploadFile] = File(...),
    analysis_params: str = Form(...)
):
    """Комплексный анализ тендерной документации"""
    try:
        # Parse parameters
        params = json.loads(analysis_params)
        
        # Save uploaded tender documents temporarily
        doc_paths = []
        for doc in tender_documents:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{doc.filename}")
            content = await doc.read()
            temp_file.write(content)
            temp_file.close()
            doc_paths.append({
                'original_name': doc.filename,
                'temp_path': temp_file.name,
                'size': len(content),
                'type': doc.content_type
            })
        
        job_params = {
            'tender_documents': doc_paths,
            'analysis_depth': params.get('analysisDepth', 'comprehensive'),
            'include_financial_analysis': params.get('includeFinancialAnalysis', True),
            'include_risk_assessment': params.get('includeRiskAssessment', True),
            'include_compliance_check': params.get('includeComplianceCheck', True),
            'include_competitor_analysis': params.get('includeCompetitorAnalysis', True),
            'include_recommendations': params.get('includeRecommendations', True)
        }
        
        job_id = create_job('tender_analyzer', job_params)
        
        # Send new job notification through existing manager
        if WEBSOCKET_AVAILABLE and websocket_manager:
            try:
                new_job_notification = {
                    "type": "new_job",
                    "job_id": job_id,
                    "tool_type": "tender_analyzer",
                    "estimated_time": 300,
                    "timestamp": datetime.now().isoformat()
                }
                await websocket_manager.broadcast(json.dumps(new_job_notification, ensure_ascii=False))
            except Exception as e:
                logger.error(f"Failed to send new job notification: {e}")
        
        # Execute in background
        coordinator = await get_coordinator()
        background_tasks.add_task(
            execute_tool_job, job_id, coordinator, 'tender_analyzer', job_params
        )
        
        return ToolExecutionResponse(
            success=True,
            job_id=job_id,
            message="Комплексный анализ тендера запущен",
            estimated_time=300  # 5 minutes
        )
        
    except Exception as e:
        logger.error(f"Ошибка анализа тендера: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{job_id}/status")
async def get_job_status(job_id: str):
    """Получить статус задачи из Redis"""
    try:
        r = get_redis()
        job_raw = r.get(_job_key(job_id))
        if not job_raw:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        job = json.loads(job_raw)
        return {
            'success': True,
            'job_id': job_id,
            'status': job['status'],
            'progress': job['progress'],
            'message': job['message'],
            'result': job.get('result'),
            'error': job.get('error'),
            'created_at': job['created_at'],
            'updated_at': job['updated_at']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis error: {e}")

@router.get("/jobs/completed")
async def get_completed_jobs():
    """Получить список завершенных задач (из Redis)"""
    try:
        r = get_redis()
        job_ids = list(r.smembers(REDIS_COMPLETED_SET))
        jobs_by_tool: Dict[str, List[Dict[str, Any]]] = {}
        for jid in job_ids:
            raw = r.get(_job_key(jid))
            if not raw:
                continue
            job = json.loads(raw)
            tool_type = job.get('tool_type', 'unknown')
            jobs_by_tool.setdefault(tool_type, []).append({
                'job_id': job['id'],
                'status': job['status'],
                'progress': job['progress'],
                'message': job['message'],
                'created_at': job['created_at']
            })
        return {
            'success': True,
            'jobs': jobs_by_tool,
            'total_completed': len(job_ids)
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis error: {e}")

@router.get("/jobs/active")
async def get_active_jobs():
    """Получить список активных задач (из Redis)"""
    try:
        r = get_redis()
        job_ids = list(r.smembers(REDIS_ACTIVE_SET))
        jobs_by_tool: Dict[str, List[Dict[str, Any]]] = {}
        for jid in job_ids:
            raw = r.get(_job_key(jid))
            if not raw:
                continue
            job = json.loads(raw)
            tool_type = job.get('tool_type', 'unknown')
            jobs_by_tool.setdefault(tool_type, []).append({
                'job_id': job['id'],
                'status': job['status'],
                'progress': job['progress'],
                'message': job['message'],
                'created_at': job['created_at']
            })
        return {
            'success': True,
            'jobs': jobs_by_tool,
            'total_active': len(job_ids)
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis error: {e}")

@router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Отменить задачу"""
    try:
        r = get_redis()
        if not r.get(_job_key(job_id)):
            raise HTTPException(status_code=404, detail="Задача не найдена или уже завершена")
        update_job(job_id, status='cancelled', message='Задача отменена пользователем')
        return {'success': True, 'message': 'Задача отменена'}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis error: {e}")

@router.get("/jobs/{job_id}/download")
async def download_job_result(job_id: str):
    """Скачать результат задачи"""
    try:
        r = get_redis()
        raw = r.get(_job_key(job_id))
        if not raw:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        if raw:
            job = json.loads(raw)
            if job.get('status') != 'completed' or not job.get('result'):
                raise HTTPException(status_code=400, detail="Результат недоступен")
        # Create temporary file with result
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
        json.dump(job['result'], temp_file, ensure_ascii=False, indent=2)
        temp_file.close()
        return FileResponse(
            temp_file.name,
            filename=f"{job.get('tool_type','tool')}_result_{job_id[:8]}.json",
            media_type='application/json'
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis error: {e}")

@router.delete("/jobs/cleanup")
async def cleanup_completed_jobs():
    """Очистить завершенные задачи (удалить старые ключи и члены set)"""
    try:
        r = get_redis()
        cutoff_time = datetime.now().timestamp() - (24 * 60 * 60)
        cleaned = 0
        to_remove = []
        try:
            job_ids = list(r.smembers(REDIS_COMPLETED_SET))
        except Exception:
            job_ids = []
        for job_id in job_ids:
            try:
                raw = r.get(_job_key(job_id))
            except Exception:
                raw = None
            if not raw:
                # key already expired, remove from set
                try:
                    r.srem(REDIS_COMPLETED_SET, job_id)
                except Exception:
                    pass
                continue
            try:
                job = json.loads(raw)
            except Exception:
                continue
            try:
                upd = job.get('updated_at') or job.get('created_at')
                from datetime import datetime as _dt
                ts = _dt.fromisoformat(upd).timestamp() if isinstance(upd, str) else float(upd)
            except Exception:
                ts = cutoff_time - 1
            if ts < cutoff_time:
                try:
                    r.delete(_job_key(job_id))
                    r.srem(REDIS_COMPLETED_SET, job_id)
                except Exception:
                    pass
                cleaned += 1
        return {
            'success': True,
            'cleaned_jobs': cleaned,
            'message': f'Очищено {cleaned} завершенных задач'
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis error: {e}")

@router.get("/info")
async def get_tools_info():
    """Получить информацию о доступных инструментах"""
    return {
        'success': True,
        'tools': [
            {
                'id': 'estimate',
                'name': 'Анализ смет',
                'description': 'Загрузка и анализ сметной документации',
                'supported_formats': ['.xlsx', '.xls', '.pdf', '.csv'],
                'max_file_size': '50MB',
                'estimated_time': '2-3 минуты'
            },
            {
                'id': 'images',
                'name': 'Анализ изображений',
                'description': 'Анализ чертежей, планов и фотографий',
                'supported_formats': ['.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.pdf'],
                'max_file_size': '100MB',
                'estimated_time': '3-5 минут'
            },
            {
                'id': 'documents',
                'name': 'Анализ документов',
                'description': 'Обработка проектной документации',
                'supported_formats': ['.pdf', '.doc', '.docx', '.txt'],
                'max_file_size': '50MB',
                'estimated_time': '1-2 минуты'
            }
        ],
        'statistics': {
            'active_jobs': len(active_jobs),
            'completed_jobs': len(completed_jobs),
            'total_processed': len(completed_jobs)
        }
    }

# Health check
@router.get("/health")
async def health_check():
    """Проверка работоспособности системы инструментов"""
    try:
        coordinator = await get_coordinator()
        # Redis status
        try:
            r = get_redis()
            r_ok = bool(r.ping())
            active_count = len(r.smembers(REDIS_ACTIVE_SET))
            completed_count = len(r.smembers(REDIS_COMPLETED_SET))
        except Exception:
            r_ok = False
            active_count = completed_count = 0
        return {
            'status': 'healthy' if coordinator and r_ok else 'degraded' if coordinator or r_ok else 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'components': {
                'coordinator': 'healthy' if coordinator else 'unhealthy',
                'tools_adapter': 'healthy' if tools_adapter else 'unhealthy',
                'redis': 'healthy' if r_ok else 'unhealthy',
                'active_jobs': active_count,
                'completed_jobs': completed_count
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        )

# Export router
__all__ = ["router"]