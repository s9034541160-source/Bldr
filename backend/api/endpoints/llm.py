"""
API эндпоинты для работы с LLM
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Union
from backend.config.settings import settings
from backend.core.model_manager import model_manager
from backend.middleware.rbac import get_current_user
from backend.models.auth import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/llm", tags=["llm"])


class GenerateRequest(BaseModel):
    """Запрос на генерацию текста"""
    model_config = {"protected_namespaces": ()}
    
    prompt: str
    model_id: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    repeat_penalty: Optional[float] = None
    stop: Optional[List[str]] = None


class GenerateResponse(BaseModel):
    """Ответ с сгенерированным текстом"""
    model_config = {"protected_namespaces": ()}
    
    text: str
    model_id: str


class LoadModelRequest(BaseModel):
    """Запрос на загрузку модели"""
    model_config = {"protected_namespaces": ()}

    model_path: str
    ttl_seconds: Optional[int] = None
    n_ctx: Optional[int] = None
    n_gpu_layers: Optional[int] = None
    verbose: bool = False
    priority: Optional[int] = None


class UpdatePriorityRequest(BaseModel):
    """Запрос на обновление приоритета модели"""

    priority: int


class GenerationParametersResponse(BaseModel):
    """Параметры генерации модели"""

    max_tokens: int
    temperature: float
    top_p: float
    top_k: int
    repeat_penalty: float
    stop: List[str]


class UpdateGenerationParametersRequest(BaseModel):
    """Обновление параметров генерации"""

    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    repeat_penalty: Optional[float] = None
    stop: Optional[List[str]] = None


class RegisterModelRequest(BaseModel):
    """Регистрация специализированной модели"""
    model_config = {"protected_namespaces": ()}

    model_id: str = Field(..., description="Уникальный идентификатор модели")
    model_path: str = Field(..., description="Путь к файлу модели")
    domain: str = Field(..., description="Домен использования (finance, legal, bim и т.д.)")
    priority: Optional[int] = None
    ttl_seconds: Optional[int] = None
    n_ctx: Optional[int] = None
    n_gpu_layers: Optional[int] = None
    parameters: Optional[Dict[str, Optional[Union[int, float, List[str]]]]] = None


class ModelOperationResponse(BaseModel):
    """Ответ на операции с моделью"""
    model_config = {"protected_namespaces": ()}

    status: str
    model_id: str


@router.post("/generate", response_model=GenerateResponse)
async def generate_text(
    request: GenerateRequest,
    current_user: User = Depends(get_current_user)
):
    """Генерация текста через LLM"""
    try:
        text = model_manager.generate(
            prompt=request.prompt,
            model_id=request.model_id,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            top_k=request.top_k,
            repeat_penalty=request.repeat_penalty,
            stop=request.stop,
        )
        
        if not text:
            raise HTTPException(status_code=500, detail="Generation failed")
        
        return GenerateResponse(
            text=text,
            model_id=request.model_id or model_manager.current_model or "unknown"
        )
    except Exception as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/stream")
async def generate_text_stream(
    request: GenerateRequest,
    current_user: User = Depends(get_current_user)
) -> StreamingResponse:
    """Потоковая генерация текста через LLM"""
    generator = model_manager.generate_stream(
        prompt=request.prompt,
        model_id=request.model_id,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        top_p=request.top_p,
        top_k=request.top_k,
        repeat_penalty=request.repeat_penalty,
        stop=request.stop,
    )

    if not generator:
        raise HTTPException(status_code=500, detail="Streaming generation failed")

    return StreamingResponse(generator, media_type="text/plain")


@router.get("/models")
async def list_models(current_user: User = Depends(get_current_user)):
    """Список загруженных моделей"""
    models = model_manager.list_models()
    memory_usage = model_manager.get_memory_usage()
    return {
        "models": models,
        "total_memory_bytes": memory_usage["total_memory_bytes"],
    }


@router.get("/registry")
async def list_registered_models(current_user: User = Depends(get_current_user)):
    """Список всех зарегистрированных моделей с конфигурацией"""
    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles:
        raise HTTPException(status_code=403, detail="Only admins can view the registry")
    return {"models": model_manager.list_registered_models()}


@router.get("/models/{model_id}")
async def get_model_info(
    model_id: str,
    current_user: User = Depends(get_current_user)
):
    """Информация о модели"""
    info = model_manager.get_model_info(model_id)
    if not info:
        raise HTTPException(status_code=404, detail="Model not found")
    return info


@router.post("/models/{model_id}/load", response_model=ModelOperationResponse)
async def load_model(
    model_id: str,
    request: LoadModelRequest,
    current_user: User = Depends(get_current_user)
) -> ModelOperationResponse:
    """Загрузка модели"""
    # Проверка на роль admin
    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles:
        raise HTTPException(status_code=403, detail="Only admins can load models")
    
    success = model_manager.load_model(
        model_path=request.model_path,
        model_id=model_id,
        n_ctx=request.n_ctx or settings.LLM_CONTEXT_SIZE,
        n_gpu_layers=request.n_gpu_layers or settings.LLM_N_GPU_LAYERS,
        verbose=request.verbose,
        ttl_seconds=request.ttl_seconds,
        priority=request.priority,
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to load model")
    
    return ModelOperationResponse(status="loaded", model_id=model_id)


@router.post("/models/register", response_model=ModelOperationResponse)
async def register_model(
    request: RegisterModelRequest,
    current_user: User = Depends(get_current_user)
) -> ModelOperationResponse:
    """Регистрация конфигурации модели (без загрузки)"""
    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles:
        raise HTTPException(status_code=403, detail="Only admins can register models")

    model_manager.register_model_config(
        model_id=request.model_id,
        config_data={
            "path": request.model_path,
            "priority": request.priority,
            "ttl_seconds": request.ttl_seconds,
            "n_ctx": request.n_ctx,
            "n_gpu_layers": request.n_gpu_layers,
            "domain": request.domain,
            "parameters": request.parameters or {},
        },
    )

    return ModelOperationResponse(status="registered", model_id=request.model_id)


@router.post("/models/{model_id}/unload", response_model=ModelOperationResponse)
async def unload_model(
    model_id: str,
    current_user: User = Depends(get_current_user)
) -> ModelOperationResponse:
    """Выгрузка модели"""
    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles:
        raise HTTPException(status_code=403, detail="Only admins can unload models")

    success = model_manager.unload_model(model_id)
    if not success:
        raise HTTPException(status_code=404, detail="Model not found")

    return ModelOperationResponse(status="unloaded", model_id=model_id)


@router.get("/metrics")
async def get_llm_metrics(current_user: User = Depends(get_current_user)):
    """Метрики использования LLM"""
    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles:
        raise HTTPException(status_code=403, detail="Only admins can view LLM metrics")
    return model_manager.get_memory_usage()


@router.post("/models/{model_id}/priority", response_model=ModelOperationResponse)
async def update_model_priority(
    model_id: str,
    request: UpdatePriorityRequest,
    current_user: User = Depends(get_current_user)
) -> ModelOperationResponse:
    """Обновление приоритета модели"""
    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles:
        raise HTTPException(status_code=403, detail="Only admins can update priorities")

    success = model_manager.set_model_priority(model_id, request.priority)
    if not success:
        raise HTTPException(status_code=404, detail="Model not found")

    return ModelOperationResponse(status="priority_updated", model_id=model_id)


@router.get("/models/domain/{domain}")
async def get_models_by_domain(
    domain: str,
    current_user: User = Depends(get_current_user)
):
    """Список моделей по домену"""
    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles:
        raise HTTPException(status_code=403, detail="Only admins can query by domain")
    models = model_manager.get_models_by_domain(domain)
    return {"domain": domain, "models": models}


@router.post("/models/domain/{domain}/load", response_model=ModelOperationResponse)
async def load_model_by_domain(
    domain: str,
    current_user: User = Depends(get_current_user)
) -> ModelOperationResponse:
    """Загрузка первой доступной модели по домену"""
    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles:
        raise HTTPException(status_code=403, detail="Only admins can load by domain")

    model_id = model_manager.load_model_by_domain(domain)
    if not model_id:
        raise HTTPException(status_code=404, detail="No model found for domain")

    return ModelOperationResponse(status="loaded", model_id=model_id)


@router.get(
    "/models/{model_id}/parameters",
    response_model=GenerationParametersResponse,
)
async def get_model_parameters(
    model_id: str,
    current_user: User = Depends(get_current_user)
) -> GenerationParametersResponse:
    """Получение параметров генерации модели"""
    defaults = model_manager.get_generation_defaults(model_id)
    return GenerationParametersResponse(
        max_tokens=defaults["max_tokens"],
        temperature=defaults["temperature"],
        top_p=defaults["top_p"],
        top_k=defaults["top_k"],
        repeat_penalty=defaults["repeat_penalty"],
        stop=defaults.get("stop", []),
    )


@router.post("/models/{model_id}/parameters", response_model=ModelOperationResponse)
async def update_model_parameters(
    model_id: str,
    request: UpdateGenerationParametersRequest,
    current_user: User = Depends(get_current_user)
) -> ModelOperationResponse:
    """Обновление параметров генерации модели"""
    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles:
        raise HTTPException(status_code=403, detail="Only admins can update parameters")

    updated = model_manager.update_generation_parameters(
        model_id,
        request.dict(exclude_none=True),
    )
    if not updated:
        raise HTTPException(status_code=400, detail="No parameters were updated")

    return ModelOperationResponse(status="parameters_updated", model_id=model_id)

