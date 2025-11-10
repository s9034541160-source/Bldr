"""
High-level orchestration for dataset generation and fine-tuning jobs.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from backend.models.training import TrainingDataset, TrainingJob
from backend.services.task_queue import task_queue

logger = logging.getLogger(__name__)


class TrainingPipelineService:
    """Facade to manage training datasets and fine-tuning jobs."""

    def __init__(self, db: Session):
        self.db = db

    # --------------------------
    # Dataset management
    # --------------------------
    def create_dataset(
        self,
        *,
        name: str,
        description: Optional[str],
        document_ids: List[int],
        config: Optional[Dict[str, Any]] = None,
    ) -> TrainingDataset:
        dataset = TrainingDataset(
            name=name,
            description=description,
            source_documents=[{"document_id": doc_id} for doc_id in document_ids],
            config=config or {},
            status="pending",
        )
        self.db.add(dataset)
        self.db.commit()
        self.db.refresh(dataset)

        dispatch = task_queue.schedule_dataset_build(dataset_id=dataset.id)
        logger.info("Scheduled dataset build %s (task=%s)", dataset.id, dispatch.task_id)
        return dataset

    def list_datasets(self) -> List[TrainingDataset]:
        return (
            self.db.query(TrainingDataset)
            .order_by(TrainingDataset.created_at.desc())
            .all()
        )

    def get_dataset(self, dataset_id: int) -> TrainingDataset:
        dataset = (
            self.db.query(TrainingDataset)
            .filter(TrainingDataset.id == dataset_id)
            .one_or_none()
        )
        if not dataset:
            raise ValueError(f"TrainingDataset {dataset_id} not found")
        return dataset

    # --------------------------
    # Fine-tuning jobs
    # --------------------------
    def create_job(
        self,
        *,
        dataset_id: int,
        base_model_id: str,
        hyperparameters: Optional[Dict[str, Any]] = None,
    ) -> TrainingJob:
        dataset = self.get_dataset(dataset_id)
        if dataset.status != "ready":
            raise ValueError("Dataset must be in 'ready' status before fine-tuning")

        job = TrainingJob(
            dataset_id=dataset.id,
            base_model_id=base_model_id,
            status="queued",
            hyperparameters=hyperparameters or {},
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        dispatch = task_queue.schedule_model_finetune(job_id=job.id)
        job.task_id = dispatch.task_id
        self.db.commit()
        logger.info("Scheduled fine-tune job %s (task=%s)", job.id, dispatch.task_id)
        return job

    def list_jobs(self) -> List[TrainingJob]:
        return (
            self.db.query(TrainingJob)
            .order_by(TrainingJob.created_at.desc())
            .all()
        )

    def get_job(self, job_id: int) -> TrainingJob:
        job = (
            self.db.query(TrainingJob)
            .filter(TrainingJob.id == job_id)
            .one_or_none()
        )
        if not job:
            raise ValueError(f"TrainingJob {job_id} not found")
        return job


__all__ = ["TrainingPipelineService"]

