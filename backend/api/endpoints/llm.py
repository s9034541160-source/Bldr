"""
API эндпоинты для работы с LLM
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.core.model_manager import model_manager
from backend.core.coordinator import coordinator
from backend.middleware.rbac import get_current_user
from backend.models.auth import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/llm", tags=["llm"])


class GenerateRequest(BaseModel):
    """Запрос на генерацию текста"""
    prompt: str
    model_id: Optional[str] = None
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40


class GenerateResponse(BaseModel):
    """Ответ с сгенерированным текстом"""
    text: str
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
            top_k=request.top_k
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


@router.get("/models")
async def list_models(current_user: User = Depends(get_current_user)):
    """Список загруженных моделей"""
    models = model_manager.list_models()
    return {"models": models}


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


@router.post("/models/{model_id}/load")
async def load_model(
    model_id: str,
    model_path: str,
    current_user: User = Depends(get_current_user)
):
    """Загрузка модели"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only superusers can load models")
    
    success = model_manager.load_model(
        model_path=model_path,
        model_id=model_id
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to load model")
    
    return {"status": "loaded", "model_id": model_id}

