"""
Сервис для управления правами доступа к документам
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.models.document import Document
from backend.models.document_permission import DocumentPermission, PermissionType
from backend.models.project import Project
from backend.models.auth import User, Role
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DocumentPermissionService:
    """Сервис для управления правами доступа к документам"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_permission(
        self,
        user: User,
        document: Document,
        permission_type: str
    ) -> bool:
        """
        Проверка прав доступа пользователя к документу
        
        Args:
            user: Пользователь
            document: Документ
            permission_type: Тип права ("read", "write", "delete", "admin")
            
        Returns:
            True если есть право, False иначе
        """
        # Владелец документа имеет все права
        if document.created_by == user.id:
            return True
        
        # Проверка прямых прав пользователя
        user_permission = self.db.query(DocumentPermission).filter(
            DocumentPermission.document_id == document.id,
            DocumentPermission.subject_type == "user",
            DocumentPermission.subject_id == user.id,
            DocumentPermission.permission_type == permission_type
        ).first()
        
        if user_permission:
            return True
        
        # Проверка прав через роли
        for role in user.roles:
            role_permission = self.db.query(DocumentPermission).filter(
                DocumentPermission.document_id == document.id,
                DocumentPermission.subject_type == "role",
                DocumentPermission.subject_id == role.id,
                DocumentPermission.permission_type == permission_type
            ).first()
            
            if role_permission:
                return True
        
        # Проверка наследования прав от проекта
        if document.project_id:
            project_permission = self.db.query(DocumentPermission).filter(
                DocumentPermission.document_id == document.id,
                DocumentPermission.subject_type == "project",
                DocumentPermission.subject_id == document.project_id,
                DocumentPermission.permission_type == permission_type
            ).first()
            
            if project_permission:
                return True
            
            # Проверка прав через проект (если пользователь владелец/менеджер проекта)
            project = self.db.query(Project).filter(Project.id == document.project_id).first()
            if project:
                if project.owner_id == user.id or project.manager_id == user.id:
                    return True
        
        # Проверка прав на чтение через наследование (admin имеет все права)
        admin_permission = self.db.query(DocumentPermission).filter(
            DocumentPermission.document_id == document.id,
            DocumentPermission.subject_type.in_(["user", "role"]),
            DocumentPermission.subject_id.in_([user.id] + [r.id for r in user.roles]),
            DocumentPermission.permission_type == "admin"
        ).first()
        
        if admin_permission:
            return True
        
        return False
    
    def grant_permission(
        self,
        document_id: int,
        subject_type: str,
        subject_id: int,
        permission_type: str,
        inherited_from: Optional[int] = None
    ) -> DocumentPermission:
        """
        Предоставление права доступа
        
        Args:
            document_id: ID документа
            subject_type: Тип субъекта ("user", "role", "project")
            subject_id: ID субъекта
            permission_type: Тип права
            inherited_from: ID родительского права (для наследования)
        """
        # Проверка на существующее право
        existing = self.db.query(DocumentPermission).filter(
            DocumentPermission.document_id == document_id,
            DocumentPermission.subject_type == subject_type,
            DocumentPermission.subject_id == subject_id,
            DocumentPermission.permission_type == permission_type
        ).first()
        
        if existing:
            return existing
        
        permission = DocumentPermission(
            document_id=document_id,
            subject_type=subject_type,
            subject_id=subject_id,
            permission_type=permission_type,
            inherited_from=inherited_from
        )
        
        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)
        
        logger.info(f"Granted {permission_type} permission to {subject_type}:{subject_id} for document {document_id}")
        return permission
    
    def revoke_permission(
        self,
        document_id: int,
        subject_type: str,
        subject_id: int,
        permission_type: str
    ) -> bool:
        """Отзыв права доступа"""
        permission = self.db.query(DocumentPermission).filter(
            DocumentPermission.document_id == document_id,
            DocumentPermission.subject_type == subject_type,
            DocumentPermission.subject_id == subject_id,
            DocumentPermission.permission_type == permission_type
        ).first()
        
        if permission:
            self.db.delete(permission)
            self.db.commit()
            logger.info(f"Revoked {permission_type} permission from {subject_type}:{subject_id} for document {document_id}")
            return True
        
        return False
    
    def inherit_from_project(
        self,
        document_id: int,
        project_id: int
    ) -> List[DocumentPermission]:
        """
        Наследование прав от проекта
        
        Args:
            document_id: ID документа
            project_id: ID проекта
        """
        # Получение прав проекта
        project_permissions = self.db.query(DocumentPermission).filter(
            DocumentPermission.document_id == project_id,
            DocumentPermission.subject_type == "project"
        ).all()
        
        created_permissions = []
        
        for project_perm in project_permissions:
            # Создание наследуемого права для документа
            permission = self.grant_permission(
                document_id=document_id,
                subject_type=project_perm.subject_type,
                subject_id=project_perm.subject_id,
                permission_type=project_perm.permission_type,
                inherited_from=project_perm.id
            )
            created_permissions.append(permission)
        
        return created_permissions
    
    def get_document_permissions(
        self,
        document_id: int
    ) -> List[DocumentPermission]:
        """Получение всех прав доступа к документу"""
        return self.db.query(DocumentPermission).filter(
            DocumentPermission.document_id == document_id
        ).all()
    
    def log_access(
        self,
        document_id: int,
        user_id: int,
        action_type: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Логирование доступа к документу"""
        from backend.models.document_permission import DocumentAccessLog
        
        log_entry = DocumentAccessLog(
            document_id=document_id,
            user_id=user_id,
            action_type=action_type,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(log_entry)
        self.db.commit()
        
        logger.info(f"Logged {action_type} access to document {document_id} by user {user_id}")

