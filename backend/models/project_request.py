"""
SQLAlchemy model for incoming project requests.
"""

from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, Text
from sqlalchemy.sql import func

from backend.models import Base


class ProjectRequest(Base):
    """Хранение входящих заявок на проекты."""

    __tablename__ = "project_requests"

    id = Column(Integer, primary_key=True, index=True)
    channel = Column(String, nullable=False, index=True)
    external_id = Column(String, nullable=True, index=True)
    subject = Column(String, nullable=True)
    body = Column(Text, nullable=True)
    customer_name = Column(String, nullable=True)
    contact_email = Column(String, nullable=True, index=True)
    contact_phone = Column(String, nullable=True)
    project_location = Column(String, nullable=True)
    status = Column(String, nullable=False, default="received", index=True)
    metadata_json = Column("metadata", JSON, nullable=True)
    attachments = Column(JSON, nullable=True)
    raw_payload = Column(JSON, nullable=True)
    processed = Column(Boolean, default=False, nullable=False)
    received_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)


__all__ = ["ProjectRequest"]

