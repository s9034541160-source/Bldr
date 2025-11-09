"""
Middleware для проверки прав доступа к документам
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.models import get_db
from backend.models.document import Document
from backend.models.auth import User
from backend.services.document_permission_service import DocumentPermissionService
from backend.middleware.rbac import get_current_user
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def require_document_permission(permission_type: str):
    """
    Dependency для проверки прав доступа к документу
    
    Args:
        permission_type: Тип права ("read", "write", "delete", "admin")
    """
    def permission_checker(
        document_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        permission_service = DocumentPermissionService(db)
        
        if not permission_service.check_permission(current_user, document, permission_type):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You don't have {permission_type} permission for this document"
            )
        
        # Логирование доступа
        permission_service.log_access(
            document_id=document_id,
            user_id=current_user.id,
            action_type=permission_type
        )
        
        return document
    
    return permission_checker

