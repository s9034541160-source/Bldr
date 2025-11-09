"""
API эндпоинты для управления правами доступа к документам
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.models import get_db
from backend.services.document_permission_service import DocumentPermissionService
from backend.middleware.rbac import get_current_user, require_permission
from backend.models.auth import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["document-permissions"])


class GrantPermissionRequest(BaseModel):
    """Запрос на предоставление права"""
    subject_type: str  # "user", "role", "project"
    subject_id: int
    permission_type: str  # "read", "write", "delete", "admin"


class PermissionResponse(BaseModel):
    """Ответ с информацией о праве"""
    id: int
    document_id: int
    subject_type: str
    subject_id: int
    permission_type: str
    inherited_from: Optional[int] = None
    
    class Config:
        from_attributes = True


@router.post("/{document_id}/permissions", response_model=PermissionResponse)
@require_permission("document", "admin")
async def grant_permission(
    document_id: int,
    request: GrantPermissionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Предоставление права доступа к документу"""
    permission_service = DocumentPermissionService(db)
    
    permission = permission_service.grant_permission(
        document_id=document_id,
        subject_type=request.subject_type,
        subject_id=request.subject_id,
        permission_type=request.permission_type
    )
    
    return PermissionResponse(
        id=permission.id,
        document_id=permission.document_id,
        subject_type=permission.subject_type,
        subject_id=permission.subject_id,
        permission_type=permission.permission_type,
        inherited_from=permission.inherited_from
    )


@router.delete("/{document_id}/permissions")
@require_permission("document", "admin")
async def revoke_permission(
    document_id: int,
    subject_type: str,
    subject_id: int,
    permission_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Отзыв права доступа к документу"""
    permission_service = DocumentPermissionService(db)
    
    success = permission_service.revoke_permission(
        document_id=document_id,
        subject_type=subject_type,
        subject_id=subject_id,
        permission_type=permission_type
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    return {"status": "revoked"}


@router.get("/{document_id}/permissions", response_model=List[PermissionResponse])
@require_permission("document", "read")
async def get_permissions(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение всех прав доступа к документу"""
    permission_service = DocumentPermissionService(db)
    permissions = permission_service.get_document_permissions(document_id)
    
    return [
        PermissionResponse(
            id=p.id,
            document_id=p.document_id,
            subject_type=p.subject_type,
            subject_id=p.subject_id,
            permission_type=p.permission_type,
            inherited_from=p.inherited_from
        )
        for p in permissions
    ]


@router.post("/{document_id}/inherit-from-project")
@require_permission("document", "admin")
async def inherit_from_project(
    document_id: int,
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Наследование прав от проекта"""
    permission_service = DocumentPermissionService(db)
    
    permissions = permission_service.inherit_from_project(document_id, project_id)
    
    return {
        "status": "inherited",
        "permissions_count": len(permissions)
    }

