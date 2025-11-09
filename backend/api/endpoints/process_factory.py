"""
API эндпоинты для ProcessFactory
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from backend.core.process_factory import process_factory
from backend.middleware.rbac import get_current_user, require_role
from backend.models.auth import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/process-factory", tags=["process-factory"])


class CreateProcessRequest(BaseModel):
    """Запрос на создание процесса"""
    process_id: str
    process_name: str
    description: str
    process_type: str = "standard"
    inputs: Optional[List[Dict[str, str]]] = None
    outputs: Optional[List[Dict[str, str]]] = None
    steps: Optional[List[Dict[str, Any]]] = None


@router.post("/create")
@require_role(["admin", "manager"])
async def create_process(
    request: CreateProcessRequest,
    current_user: User = Depends(get_current_user)
):
    """Создание нового бизнес-процесса"""
    try:
        result = process_factory.create_process(
            process_id=request.process_id,
            process_name=request.process_name,
            description=request.description,
            process_type=request.process_type,
            inputs=request.inputs,
            outputs=request.outputs,
            steps=request.steps
        )
        
        return {
            "status": "created",
            "process": result
        }
    except Exception as e:
        logger.error(f"Process creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates")
async def list_templates(current_user: User = Depends(get_current_user)):
    """Список доступных шаблонов процессов"""
    templates = [
        {
            "id": "standard",
            "name": "Стандартный процесс",
            "description": "Базовый шаблон для обычных процессов"
        },
        {
            "id": "document",
            "name": "Процесс с документами",
            "description": "Шаблон для процессов, работающих с документами"
        },
        {
            "id": "calculation",
            "name": "Процесс с расчетами",
            "description": "Шаблон для процессов с математическими расчетами"
        },
        {
            "id": "approval",
            "name": "Процесс с согласованием",
            "description": "Шаблон для процессов с этапами согласования"
        },
        {
            "id": "integration",
            "name": "Процесс с интеграциями",
            "description": "Шаблон для процессов с внешними интеграциями"
        }
    ]
    
    return {"templates": templates}

