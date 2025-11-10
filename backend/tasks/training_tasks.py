"""
Celery tasks for dataset preparation.
"""

from __future__ import annotations

import logging

from celery import shared_task

from backend.models import SessionLocal
from backend.models.training import TrainingDataset
from backend.services.training.dataset_builder import TrainingDatasetBuilder

logger = logging.getLogger(__name__)


@shared_task(
    name="training.build_dataset",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def build_training_dataset(self, dataset_id: int) -> None:  # type: ignore[override]
    session = SessionLocal()
    try:
        builder = TrainingDatasetBuilder(session)
        builder.build(dataset_id)
        logger.info("Training dataset %s built successfully", dataset_id)
    except Exception as exc:  # noqa: BLE001
        dataset = session.query(TrainingDataset).filter(TrainingDataset.id == dataset_id).one_or_none()
        if dataset:
            dataset.status = "failed"
            dataset.error = str(exc)
            session.commit()
        logger.error("Failed to build dataset %s: %s", dataset_id, exc, exc_info=True)
        raise
    finally:
        session.close()


__all__ = ["build_training_dataset"]

