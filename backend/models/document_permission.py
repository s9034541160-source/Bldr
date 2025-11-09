"""
SQLAlchemy модели для прав доступа к документам
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.models import Base
import enum


class PermissionType(enum.Enum):
    """Типы прав доступа"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


class DocumentPermission(Base):
    """Модель прав доступа к документу"""
    __tablename__ = "document_permissions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    
    # Тип субъекта права (user, role, project)
    subject_type = Column(String, nullable=False)  # "user", "role", "project"
    subject_id = Column(Integer, nullable=False)  # ID пользователя, роли или проекта
    
    # Тип права
    permission_type = Column(String, nullable=False)  # "read", "write", "delete", "admin"
    
    # Наследование
    inherited_from = Column(Integer, ForeignKey("document_permissions.id"), nullable=True)
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    document = relationship("Document", backref="permissions")
    parent_permission = relationship("DocumentPermission", remote_side=[id], backref="child_permissions")


class DocumentAccessLog(Base):
    """Модель аудита доступа к документам"""
    __tablename__ = "document_access_logs"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Тип действия
    action_type = Column(String, nullable=False)  # "view", "download", "edit", "delete"
    
    # IP адрес и user agent
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    # Временная метка
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("Document", backref="access_logs")
    user = relationship("User", backref="document_access_logs")

