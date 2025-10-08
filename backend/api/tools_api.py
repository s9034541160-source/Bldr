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
from typing import Dict, Any, List, Optional, Union

# Redis for enterprise-grade job storage
import redis

from fastapi import APIRouter, HTTPException, File, UploadFile, Form, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type alias for Redis response
RedisResponse = Union[str, bytes, None]

# Import coordinator for tool execution (with error handling)
try:
    import sys
    import os
    # Add the project root to sys.path
    project_root = os.path.join(os.path.dirname(__file__), '..', '..')
    sys.path.insert(0, project_root)
    
    from core.agents.coordinator_agent import CoordinatorAgent
    COORDINATOR_AVAILABLE = True
except ImportError as e:
    print(f"CoordinatorAgent import error: {e}")
    logger.warning(f"CoordinatorAgent не доступен: {e}")
    CoordinatorAgent = None
    COORDINATOR_AVAILABLE = False

try:
    import sys
    import os
    # Add the project root to sys.path
    project_root = os.path.join(os.path.dirname(__file__), '..', '..')
    sys.path.insert(0, project_root)
    
    from core.tools_adapter import get_tools_adapter
    ToolsAdapter = get_tools_adapter
except ImportError as e:
    print(f"ToolsAdapter import error: {e}")
    logger.warning(f"ToolsAdapter не доступен: {e}")
    ToolsAdapter = None

# Import existing WebSocket manager instead of separate server
try:
    import sys
    import os
    # Add the project root to sys.path
    project_root = os.path.join(os.path.dirname(__file__), '..', '..')
    sys.path.insert(0, project_root)
    
    from core.websocket_manager import manager as websocket_manager
    WEBSOCKET_AVAILABLE = True
except ImportError as e:
    print(f"WebSocket manager import error: {e}")
    logger.warning(f"WebSocket manager не доступен: {e}")
    websocket_manager = None
    WEBSOCKET_AVAILABLE = False

# Try to import optional modules that might not be available
try:
    from core.model_manager import ModelManager
except ImportError:
    ModelManager = None

try:
    from core.unified_tools_system import unified_tools
except ImportError:
    unified_tools = None

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

_redis_client: Optional[Union[redis.Redis, Any]] = None

def get_redis() -> Optional[Union[redis.Redis, Any]]:
    global _redis_client
    if _redis_client is None:
        # Try to initialize Redis client
        try:
            _redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
            # Test connection
            _redis_client.ping()
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            # Return a mock client that returns None for all operations
            class MockRedis:
                def get(self, *args, **kwargs):
                    return None
                def set(self, *args, **kwargs):
                    return None
                def smembers(self, *args, **kwargs):
                    return set()
                def sadd(self, *args, **kwargs):
                    return None
                def srem(self, *args, **kwargs):
                    return None
                def delete(self, *args, **kwargs):
                    return None
                def expire(self, *args, **kwargs):
                    return None
                def ping(self, *args, **kwargs):
                    raise Exception("Redis not available")
            _redis_client = MockRedis()
    return _redis_client

def _safe_redis_get(r, key: str) -> Optional[str]:
    """Safely get a value from Redis, handling async responses and errors."""
    try:
        if r is None:
            return None
        result = r.get(key)
        # Handle case where result might be awaitable
        if hasattr(result, '__await__'):
            # This is an async response, need to handle it properly
            logger.warning("Redis response appears to be async, which is unexpected")
            return None
        # Handle case where result might be bytes
        if isinstance(result, bytes):
            return result.decode('utf-8')
        return result
    except Exception as e:
        logger.error(f"Error getting key {key} from Redis: {e}")
        return None

def _safe_redis_smembers(r, key: str) -> set:
    """Safely get a set of members from Redis, handling async responses and errors."""
    try:
        if r is None:
            return set()
        result = r.smembers(key)
        # Handle case where result might be awaitable
        if hasattr(result, '__await__'):
            # This is an async response, need to handle it properly
            logger.warning("Redis response appears to be async, which is unexpected")
            return set()
        return result if result else set()
    except Exception as e:
        logger.error(f"Error getting members of {key} from Redis: {e}")
        return set()

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
            coordinator_agent = CoordinatorAgent(tools_system=tools_adapter, enable_meta_tools=False)
    
    return coordinator_agent

def _job_key(job_id: str) -> str:
    return f"{REDIS_JOB_KEY_PREFIX}{job_id}"

def create_job(tool_type: str, params: Dict[str, Any]) -> str:
    """Создать новую задачу (хранится в Redis)."""
    r = get_redis()
    if r is None:
        raise Exception("Redis client is not available")
        
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
    if r is None:
        logger.warning("Redis client is not available, skipping job update")
        return
    
    try:
        # Get job data from Redis using safe method
        job_raw = _safe_redis_get(r, _job_key(job_id))
        
        # Handle case where job_raw might be None
        if not job_raw:
            logger.warning(f"Job {job_id} not found in Redis for update")
            return
            
        # Parse job data
        try:
            job = json.loads(job_raw)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to parse job data for {job_id}: {e}")
            return
            
        # Update job fields
        if status: job['status'] = status
        if progress is not None: job['progress'] = progress
        if message: job['message'] = message
        if result is not None: job['result'] = result
        if error is not None: job['error'] = error
        job['updated_at'] = datetime.now().isoformat()
        
        # Save updated job data
        r.set(_job_key(job_id), json.dumps(job, ensure_ascii=False))

        # Send WebSocket notification through existing manager
        if WEBSOCKET_AVAILABLE and websocket_manager:
            try:
                notification = {
                    "type": "job_update",
                    "job_id": job_id,
                    "status": job.get('status', ''),
                    "progress": job.get('progress', 0),
                    "message": job.get('message', ''),
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
                        "tool_type": job.get('tool_type', ''),
                        "success": status == 'completed',
                        "timestamp": datetime.now().isoformat()
                    }
                    asyncio.create_task(
                        websocket_manager.broadcast(json.dumps(completion_notification, ensure_ascii=False))
                    )
                except Exception as e:
                    logger.error(f"Failed to send completion notification: {e}")
                    
    except Exception as e:
        logger.error(f"Error updating job {job_id}: {e}")

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
        
        # Конвертруем параметры в формат Master Tools
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
        elif tool_name == 'auto_budget':
            result = await execute_auto_budget(tools_adapter, master_params, job_id)
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
    if tool_name == 'auto_budget':
        return {
            'estimate_files': [f['temp_path'] for f in params.get('estimate_files', [])],
            'budget_params': params.get('budget_params', {})
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

async def execute_auto_budget(tools_adapter, master_params: Dict[str, Any], job_id: str) -> Dict[str, Any]:
    """Выполнение расчета бюджета"""
    update_job(job_id, progress=40, message='Расчет бюджета...')
    try:
        # Extract parameters
        estimate_files = master_params.get('estimate_files', [])
        budget_params = master_params.get('budget_params', {})
        
        # If we have estimate files, try to extract base cost
        if estimate_files:
            update_job(job_id, progress=50, message='Анализ сметных файлов...')
            # Try to parse estimate files to extract base cost
            parsing_success = False
            for estimate_file in estimate_files:
                try:
                    # Use existing estimate parser to extract base cost
                    from core.unified_estimate_parser import parse_estimate_unified
                    
                    parse_result = parse_estimate_unified(estimate_file)
                    
                    if parse_result.get('status') == 'success' and parse_result.get('total_cost', 0) > 0:
                        extracted_base_cost = parse_result['total_cost']
                        # Update budget params with extracted base cost
                        budget_params['base_cost'] = extracted_base_cost
                        update_job(job_id, progress=60, message=f'Извлечена базовая стоимость: {extracted_base_cost:,.2f}')
                        parsing_success = True
                        break  # Use the first successful parse result
                    else:
                        # Log parsing error but continue with manual base cost
                        error_msg = parse_result.get('error', 'Неизвестная ошибка парсинга')
                        logger.warning(f"Could not parse estimate file {estimate_file}: {error_msg}")
                except Exception as e:
                    logger.warning(f"Could not parse estimate file {estimate_file}: {e}")
            
            if not parsing_success and estimate_files:
                update_job(job_id, progress=55, message='Не удалось извлечь стоимость из файлов')
        
        # Validate that we have a base cost
        if budget_params.get('base_cost', 0) <= 0:
            return { 'status': 'error', 'error': 'Базовая стоимость должна быть больше 0. Пожалуйста, укажите стоимость вручную или загрузите файлы смет для автоматического извлечения.' }
        
        # Execute the auto_budget tool with the provided parameters
        update_job(job_id, progress=70, message='Выполнение расчета...')
        result = tools_adapter.execute_tool('auto_budget', **budget_params)
        
        return result
    except Exception as e:
        logger.error(f"Error in execute_auto_budget: {e}", exc_info=True)
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
            'auto_budget': {
                'name': 'Автоматический расчет бюджета',
                'description': 'Профессиональный расчет бюджета строительного проекта с учетом всех факторов',
                'category': 'financial',
                'supports_files': True,
                'file_types': ['.xls', '.xlsx', '.pdf', '.csv']
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

@router.post("/calculate/budget")
async def calculate_budget(
    background_tasks: BackgroundTasks,
    estimate_files: List[UploadFile] = File(default=None),
    params: str = Form(...)
):
    """Расчет бюджета на основе смет и параметров"""
    try:
        # Parse parameters
        budget_params = json.loads(params)
        
        # Save uploaded estimate files temporarily if provided
        file_paths = []
        if estimate_files:
            for file in estimate_files:
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
            'estimate_files': file_paths,
            'budget_params': budget_params
        }
        
        job_id = create_job('auto_budget', job_params)
        
        # Send new job notification through existing manager
        if WEBSOCKET_AVAILABLE and websocket_manager:
            try:
                new_job_notification = {
                    "type": "new_job",
                    "job_id": job_id,
                    "tool_type": "auto_budget",
                    "estimated_time": 60,
                    "timestamp": datetime.now().isoformat()
                }
                await websocket_manager.broadcast(json.dumps(new_job_notification, ensure_ascii=False))
            except Exception as e:
                logger.error(f"Failed to send new job notification: {e}")
        
        # Execute in background
        coordinator = await get_coordinator()
        background_tasks.add_task(
            execute_tool_job, job_id, coordinator, 'auto_budget', job_params
        )
        
        return ToolExecutionResponse(
            success=True,
            job_id=job_id,
            message="Расчет бюджета запущен",
            estimated_time=60  # 1 minute
        )
        
    except Exception as e:
        logger.error(f"Ошибка расчета бюджета: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{job_id}/status")
async def get_job_status(job_id: str):
    """Получить статус задачи"""
    try:
        r = get_redis()
        
        # Get job data from Redis using safe method
        raw = _safe_redis_get(r, _job_key(job_id))
        
        # Handle case where raw might be None
        if not raw:
            raise HTTPException(status_code=404, detail="Задача не найдена")
            
        # Parse job data
        try:
            job = json.loads(raw)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to parse job data for {job_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to parse job data")
            
        return {
            'success': True,
            'job_id': job_id,
            'status': job.get('status', 'unknown'),
            'progress': job.get('progress', 0),
            'message': job.get('message', ''),
            'result': job.get('result'),
            'error': job.get('error'),
            'created_at': job.get('created_at'),
            'updated_at': job.get('updated_at')
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis error: {e}")

@router.get("/jobs/{job_id}/result")
async def get_job_result(job_id: str):
    """Получить результат выполнения задачи в виде файла"""
    try:
        r = get_redis()
        
        # Get job data from Redis using safe method
        raw = _safe_redis_get(r, _job_key(job_id))
        
        # Handle case where raw might be None
        if not raw:
            raise HTTPException(status_code=404, detail="Задача не найдена")
            
        # Parse job data
        try:
            job = json.loads(raw)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to parse job data for {job_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to parse job data")
        
        # Check if job is completed and has result
        if job.get('status') != 'completed' or not job.get('result'):
            raise HTTPException(status_code=400, detail="Результат недоступен")
            
        # Create temporary file with result
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
        if job.get('result'):
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

@router.get("/jobs/completed")
async def get_completed_jobs():
    """Получить список завершенных задач (из Redis)"""
    try:
        r = get_redis()
        if r is None:
            return {
                'success': True,
                'jobs': {},
                'total_completed': 0
            }
            
        job_ids = list(_safe_redis_smembers(r, REDIS_COMPLETED_SET))
        jobs = {}
        for jid in job_ids:
            raw = _safe_redis_get(r, _job_key(jid))
            if not raw:
                continue
            try:
                job = json.loads(raw)
            except (json.JSONDecodeError, TypeError) as e:
                logger.error(f"Failed to parse job data for {jid}: {e}")
                continue
                
            # Add job to results
            tool_type = job.get('tool_type', 'unknown')
            if tool_type not in jobs:
                jobs[tool_type] = []
            jobs[tool_type].append(job)
            
        return {
            'success': True,
            'jobs': jobs,
            'total_completed': len(job_ids)
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis error: {e}")

@router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Отменить задачу"""
    try:
        r = get_redis()
        if r is None:
            raise HTTPException(status_code=503, detail="Redis not available")
            
        job_raw = _safe_redis_get(r, _job_key(job_id))
        if not job_raw:
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
        if r is None:
            raise HTTPException(status_code=503, detail="Redis not available")
            
        raw = _safe_redis_get(r, _job_key(job_id))
        if not raw:
            raise HTTPException(status_code=404, detail="Задача не найдена")
            
        try:
            job = json.loads(raw)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to parse job data for {job_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to parse job data")
            
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
        if r is None:
            return {
                'success': True,
                'cleaned_jobs': 0,
                'message': 'Redis not available, no cleanup performed'
            }
            
        cutoff_time = datetime.now().timestamp() - (24 * 60 * 60)
        cleaned = 0
        
        # Get completed job IDs using safe method
        job_ids = list(_safe_redis_smembers(r, REDIS_COMPLETED_SET))
            
        for job_id in job_ids:
            try:
                raw = _safe_redis_get(r, _job_key(job_id))
                
                # Handle case where raw might be None
                if not raw:
                    # key already expired, remove from set
                    try:
                        r.srem(REDIS_COMPLETED_SET, job_id)
                    except Exception:
                        pass
                    continue
                    
                # Parse job data
                try:
                    job = json.loads(raw)
                except (json.JSONDecodeError, TypeError) as e:
                    logger.error(f"Failed to parse job data for {job_id}: {e}")
                    continue
                    
                # Check if job is old enough to be cleaned
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
                    
            except Exception as e:
                logger.error(f"Error processing job {job_id}: {e}")
                continue
                
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
                'id': 'budget',
                'name': 'Автобюджет',
                'description': 'Автоматический расчет строительного бюджета',
                'supported_formats': ['.xlsx', '.xls', '.pdf', '.csv'],
                'max_file_size': '50MB',
                'estimated_time': '1 минута'
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
            'active_jobs': 0,
            'completed_jobs': 0,
            'total_processed': 0
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
            if r is not None:
                r_ok = bool(r.ping())
                active_count = len(_safe_redis_smembers(r, REDIS_ACTIVE_SET))
                completed_count = len(_safe_redis_smembers(r, REDIS_COMPLETED_SET))
            else:
                r_ok = False
                active_count = completed_count = 0
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

@router.post("/extract/base-cost")
async def extract_base_cost(
    estimate_files: List[UploadFile] = File(...)
):
    """Extract base cost from estimate files"""
    try:
        if not estimate_files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Save uploaded files temporarily
        file_paths = []
        for file in estimate_files:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}")
            content = await file.read()
            temp_file.write(content)
            temp_file.close()
            file_paths.append(temp_file.name)
        
        # Try to parse estimate files to extract base cost
        for file_path in file_paths:
            try:
                # Use existing estimate parser to extract base cost
                from core.unified_estimate_parser import parse_estimate_unified
                
                parse_result = parse_estimate_unified(file_path)
                
                if parse_result.get('status') == 'success' and parse_result.get('total_cost', 0) > 0:
                    extracted_base_cost = parse_result['total_cost']
                    # Clean up temporary files
                    for temp_path in file_paths:
                        try:
                            os.unlink(temp_path)
                        except:
                            pass
                    return {
                        'success': True,
                        'base_cost': extracted_base_cost,
                        'message': f'Базовая стоимость успешно извлечена: {extracted_base_cost:,.2f}'
                    }
            except Exception as e:
                logger.warning(f"Could not parse estimate file {file_path}: {e}")
                continue
        
        # Clean up temporary files
        for temp_path in file_paths:
            try:
                os.unlink(temp_path)
            except:
                pass
                
        return {
            'success': False,
            'error': 'Не удалось извлечь базовую стоимость из предоставленных файлов'
        }
        
    except Exception as e:
        logger.error(f"Error extracting base cost: {e}")
        raise HTTPException(status_code=500, detail=str(e))
