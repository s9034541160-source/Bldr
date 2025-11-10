"""
SQLAlchemy models for automated fine-tuning pipeline.
"""

from __future__ import annotations

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models import Base


class TrainingDataset(Base):
    """Represents a generated dataset of instruction-response pairs."""

    __tablename__ = "training_datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="pending", nullable=False, index=True)
    source_documents = Column(JSON, nullable=False)  # list of document ids with metadata
    config = Column(JSON, nullable=True)
    storage_path = Column(String, nullable=True)  # local filesystem path
    artifact_path = Column(String, nullable=True)  # path in MinIO or external storage
    total_examples = Column(Integer, default=0, nullable=False)
    sample_preview = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    jobs = relationship("TrainingJob", back_populates="dataset")


class TrainingJob(Base):
    """Tracks fine-tuning jobs executed via Unsloth."""

    __tablename__ = "training_jobs"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("training_datasets.id"), nullable=False, index=True)
    base_model_id = Column(String, nullable=False)
    status = Column(String, default="queued", nullable=False, index=True)
    task_id = Column(String, nullable=True, index=True)
    hyperparameters = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=True)
    output_path = Column(String, nullable=True)  # local path to adapter/model (LoRA)
    adapter_path = Column(String, nullable=True)  # remote storage path for adapter
    merged_path = Column(String, nullable=True)  # local merged HF model dir
    gguf_local_path = Column(String, nullable=True)
    artifact_path = Column(String, nullable=True)  # remote path for GGUF artifact
    gguf_path = Column(String, nullable=True)  # alias for remote gguf
    model_id = Column(String, nullable=True, index=True)
    validation_status = Column(String, default="pending", nullable=False)
    validation_metrics = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    dataset = relationship("TrainingDataset", back_populates="jobs")


__all__ = ["TrainingDataset", "TrainingJob"]

