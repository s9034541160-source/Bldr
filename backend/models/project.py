"""
SQLAlchemy модели для проектов
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Numeric, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.models import Base


class Project(Base):
    """Модель проекта"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    code = Column(String, unique=True, nullable=False, index=True)  # Уникальный код проекта
    
    # Даты
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    planned_end_date = Column(Date, nullable=True)
    
    # Финансы
    budget = Column(Numeric(15, 2), nullable=True)
    spent = Column(Numeric(15, 2), default=0, nullable=False)
    
    # Статус
    status = Column(String, default="planning", nullable=False, index=True)
    # planning, in_progress, on_hold, completed, cancelled
    
    # Владелец и команда
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", foreign_keys=[owner_id], backref="owned_projects")
    manager = relationship("User", foreign_keys=[manager_id], backref="managed_projects")
    documents = relationship("Document", backref="project")

