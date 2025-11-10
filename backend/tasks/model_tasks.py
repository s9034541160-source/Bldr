"""
Celery tasks for model fine-tuning and maintenance via Unsloth.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict

from celery import shared_task

from backend.config.settings import settings
from backend.models import SessionLocal
from backend.models.training import TrainingDataset, TrainingJob
from backend.services.minio_service import minio_service
from backend.services.training.unsloth_trainer import (
    FineTuneRequest,
    UnslothFineTuner,
)

logger = logging.getLogger(__name__)


@shared_task(
    name="models.fine_tune_unsloth",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def fine_tune_unsloth(self, job_id: int) -> Dict[str, str]:  # type: ignore[override]
    """Фоновая задача дообучения модели через Unsloth."""
    session = SessionLocal()
    job = None
    try:
        job = (
            session.query(TrainingJob)
            .filter(TrainingJob.id == job_id)
            .with_for_update()
            .one_or_none()
        )
        if not job:
            raise ValueError(f"TrainingJob {job_id} not found")
        dataset = session.query(TrainingDataset).filter(TrainingDataset.id == job.dataset_id).one()

        dataset_path = _ensure_dataset_local(dataset, session)

        job.status = "running"
        job.started_at = datetime.utcnow()
        session.commit()

        payload = _build_request_payload(job, dataset_path)
        config = FineTuneRequest(**payload)
        logger.info(
            "Starting unsloth fine-tune for job=%s model=%s dataset=%s",
            job.id,
            config.base_model_id or "default",
            config.dataset_path,
        )

        tuner = UnslothFineTuner()
        result = tuner.train(config)

        job.status = "completed"
        job.completed_at = datetime.utcnow()
        job.metrics = result.metrics
        job.output_path = result.model_path
        job.artifact_path = result.model_path
        session.commit()
        return result.to_dict()
    except Exception as exc:  # noqa: BLE001
        logger.error("Fine-tune job %s failed: %s", job_id, exc, exc_info=True)
        if job:
            job.status = "failed"
            job.error = str(exc)
            session.commit()
        raise
    finally:
        session.close()


def _ensure_dataset_local(dataset: TrainingDataset, session) -> str:
    if dataset.storage_path and Path(dataset.storage_path).exists():
        return dataset.storage_path
    if not dataset.artifact_path:
        raise RuntimeError("Dataset artifact path is missing")
    target_dir = Path(settings.UNSLOTH_OUTPUT_DIR) / "datasets" / f"dataset_{dataset.id}"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / "train.jsonl"
    logger.info("Downloading dataset %s from storage", dataset.id)
    data = minio_service.download_file("models", dataset.artifact_path)
    target_file.write_bytes(data)
    dataset.storage_path = str(target_file)
    session.commit()
    return str(target_file)


def _build_request_payload(job: TrainingJob, dataset_path: str) -> Dict[str, object]:
    payload: Dict[str, object] = {
        "dataset_path": dataset_path,
        "output_dir": str(Path(settings.UNSLOTH_OUTPUT_DIR) / "models" / f"job_{job.id}"),
        "base_model_id": job.base_model_id,
    }
    hyperparams = job.hyperparameters or {}
    allowed_keys = set(FineTuneRequest.__dataclass_fields__.keys())
    for key, value in hyperparams.items():
        if key in allowed_keys and value is not None:
            payload[key] = value
    return payload


__all__ = ["fine_tune_unsloth"]

