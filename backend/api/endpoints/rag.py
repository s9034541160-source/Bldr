"""
API эндпоинты для RAG системы
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from backend.services.rag_service import rag_service
from backend.middleware.rbac import get_current_user
from backend.models.auth import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["rag"])


class IndexDocumentRequest(BaseModel):
    """Запрос на индексацию документа"""
    document_id: str
    text: str
    metadata: Optional[Dict[str, Any]] = None


class SearchRequest(BaseModel):
    """Запрос на поиск"""
    query: str
    limit: int = 5
    score_threshold: float = 0.7
    filter: Optional[Dict[str, Any]] = None


class RAGQueryRequest(BaseModel):
    """Запрос на RAG генерацию"""
    query: str
    limit: int = 5
    score_threshold: float = 0.7
    max_tokens: int = 512
    temperature: float = 0.7


@router.get("/metrics")
async def get_rag_metrics(current_user: User = Depends(get_current_user)):
    """Метрики производительности RAG"""
    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles:
        raise HTTPException(status_code=403, detail="Only admins can view RAG metrics")
    return rag_service.get_metrics()


@router.post("/index")
async def index_document(
    request: IndexDocumentRequest,
    current_user: User = Depends(get_current_user)
):
    """Индексация документа"""
    try:
        success = rag_service.index_document(
            document_id=request.document_id,
            text=request.text,
            metadata=request.metadata
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to index document")
        
        return {"status": "indexed", "document_id": request.document_id}
    except Exception as e:
        logger.error(f"Indexing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search_documents(
    request: SearchRequest,
    current_user: User = Depends(get_current_user)
):
    """Поиск документов"""
    try:
        results = rag_service.search(
            query=request.query,
            limit=request.limit,
            score_threshold=request.score_threshold,
            filter_dict=request.filter
        )
        
        return {"results": results, "count": len(results)}
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def rag_query(
    request: RAGQueryRequest,
    current_user: User = Depends(get_current_user)
):
    """RAG запрос - поиск + генерация ответа"""
    try:
        result = rag_service.rag_query(
            query=request.query,
            limit=request.limit,
            score_threshold=request.score_threshold,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        return result
    except Exception as e:
        logger.error(f"RAG query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Удаление документа из индекса"""
    try:
        success = rag_service.delete_document(document_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete document")
        
        return {"status": "deleted", "document_id": document_id}
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

