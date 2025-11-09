"""
SQLAlchemy модели для документов СОД
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.models import Base


class Document(Base):
    """Модель документа"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    document_type = Column(String, nullable=False, index=True)  # project, contract, estimate, etc.
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)  # Путь в MinIO
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String, nullable=False)
    
    # Версионирование
    version = Column(Integer, default=1, nullable=False)
    parent_version_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    
    # Метаданные
    metadata = Column(JSON, nullable=True)  # Дополнительные метаданные
    
    # Связи
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Статусы
    status = Column(String, default="draft", nullable=False)  # draft, approved, archived
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    parent_version = relationship("Document", remote_side=[id], backref="child_versions")
    creator = relationship("User", foreign_keys=[created_by], backref="created_documents")
    updater = relationship("User", foreign_keys=[updated_by], backref="updated_documents")


class DocumentVersion(Base):
    """Модель версии документа (для детального версионирования)"""
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    file_path = Column(String, nullable=False)
    file_hash = Column(String, nullable=False)  # MD5 или SHA256 для проверки целостности
    
    # Изменения
    change_description = Column(Text, nullable=True)
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("Document", backref="versions")
    changer = relationship("User", backref="document_versions")


class DocumentMetadata(Base):
    """Модель метаданных документа"""
    __tablename__ = "document_metadata"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    
    # Ключ-значение метаданных
    key = Column(String, nullable=False, index=True)
    value = Column(Text, nullable=True)
    value_type = Column(String, nullable=False)  # string, number, date, json
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    document = relationship("Document", backref="metadata_items")

