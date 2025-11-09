"""
API эндпоинты для гибридного подхода к знаниям
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.services.hybrid_knowledge_service import hybrid_knowledge_service
from backend.middleware.rbac import get_current_user
from backend.models.auth import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hybrid", tags=["hybrid"])


class HybridQueryRequest(BaseModel):
    """Запрос на гибридный ответ"""
    query: str
    use_llm: bool = True
    use_rag_fallback: bool = True
    max_tokens: int = 512
    temperature: float = 0.7


@router.post("/query")
async def hybrid_query(
    request: HybridQueryRequest,
    current_user: User = Depends(get_current_user)
):
    """Гибридный запрос: LLM + RAG валидация"""
    try:
        result = hybrid_knowledge_service.answer_query(
            query=request.query,
            use_llm=request.use_llm,
            use_rag_fallback=request.use_rag_fallback,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        return result
    except Exception as e:
        logger.error(f"Hybrid query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

