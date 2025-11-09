"""
API эндпоинты для валидации ИИ ответов
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.services.validation_controller import validation_controller
from backend.core.model_manager import model_manager
from backend.middleware.rbac import get_current_user
from backend.models.auth import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/validation", tags=["validation"])


class ValidateRequest(BaseModel):
    """Запрос на валидацию ответа"""
    query: str
    llm_response: str
    use_cache: bool = True


class GenerateAndValidateRequest(BaseModel):
    """Запрос на генерацию и валидацию"""
    query: str
    model_id: Optional[str] = None
    max_tokens: int = 512
    temperature: float = 0.7
    use_cache: bool = True


@router.post("/validate")
async def validate_response(
    request: ValidateRequest,
    current_user: User = Depends(get_current_user)
):
    """Валидация ответа LLM через RAG"""
    try:
        result = validation_controller.validate_response(
            query=request.query,
            llm_response=request.llm_response,
            use_cache=request.use_cache
        )
        
        return result
    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-and-validate")
async def generate_and_validate(
    request: GenerateAndValidateRequest,
    current_user: User = Depends(get_current_user)
):
    """Генерация ответа через LLM с последующей валидацией через RAG"""
    try:
        # Генерация ответа через LLM
        llm_response = model_manager.generate(
            prompt=request.query,
            model_id=request.model_id,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        if not llm_response:
            raise HTTPException(status_code=500, detail="LLM generation failed")
        
        # Валидация ответа
        validation_result = validation_controller.validate_response(
            query=request.query,
            llm_response=llm_response,
            use_cache=request.use_cache
        )
        
        return {
            "llm_response": llm_response,
            "validation": validation_result
        }
        
    except Exception as e:
        logger.error(f"Generate and validate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_validation_metrics(
    current_user: User = Depends(get_current_user)
):
    """Получение метрик валидации"""
    # TODO: Реализовать сбор метрик из Redis/БД
    return {
        "total_validations": 0,
        "validated_count": 0,
        "requires_verification_count": 0,
        "average_discrepancy": 0.0,
        "average_confidence": 0.0
    }

