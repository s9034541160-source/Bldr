"""
SQLAlchemy модели для проектов
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Numeric, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from backend.models import Base


class Project(Base):
    """Модель проекта"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    code = Column(String, unique=True, nullable=False, index=True)  # Уникальный код проекта
    storage_path = Column(String, nullable=False)
    geo_latitude = Column(Numeric(10, 6), nullable=True)
    geo_longitude = Column(Numeric(10, 6), nullable=True)
    cadastral_number = Column(String, nullable=True)
    development_zone = Column(String, nullable=True)
    zone_allowed = Column(Boolean, nullable=True)
    planned_duration_days = Column(Integer, nullable=True)
    expected_start = Column(Date, nullable=True)
    expected_completion = Column(Date, nullable=True)
    preliminary_budget = Column(Numeric(15, 2), nullable=True)
    preliminary_teo_path = Column(String, nullable=True)
    teo_approval_status = Column(String, default="not_required", nullable=False)
    teo_approval_route = Column(JSONB, nullable=True)
    teo_approval_history = Column(JSONB, nullable=True)
    teo_approved_at = Column(DateTime(timezone=True), nullable=True)
    
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

