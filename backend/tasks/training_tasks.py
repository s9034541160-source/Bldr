"""
Celery tasks for dataset preparation.
"""

from __future__ import annotations

import logging

import json
from typing import List

from celery import shared_task

from backend.config.settings import settings
from backend.core.model_manager import model_manager
from backend.models import SessionLocal
from backend.models.training import TrainingDataset, TrainingJob
from backend.services.training.dataset_builder import TrainingDatasetBuilder

logger = logging.getLogger(__name__)

DEFAULT_VALIDATION_PROMPTS: List[str] = [
    prompt.strip()
    for prompt in settings.UNSLOTH_DEFAULT_VALIDATION_PROMPTS.split("||")
    if prompt.strip()
]


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


@shared_task(
    name="training.validate_model",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def validate_trained_model(self, job_id: int) -> None:  # type: ignore[override]
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
        if not job.gguf_local_path or not job.model_id:
            raise RuntimeError("Fine-tuned model artifacts are missing")

        job.validation_status = "running"
        session.commit()

        model_loaded = model_manager.load_model(
            model_path=job.gguf_local_path,
            model_id=job.model_id,
            n_ctx=settings.UNSLOTH_MAX_SEQ_LENGTH,
        )
        if not model_loaded:
            raise RuntimeError(f"Unable to load GGUF model for validation (job {job.id})")

        prompts = _extract_validation_prompts(job)
        results = []
        for prompt in prompts:
            response = model_manager.generate(
                prompt=prompt,
                model_id=job.model_id,
                max_tokens=settings.UNSLOTH_VALIDATION_MAX_TOKENS,
                temperature=settings.UNSLOTH_VALIDATION_TEMPERATURE,
            )
            results.append({"prompt": prompt, "response": response})

        job.validation_status = "completed"
        job.status = "validated"
        job.validation_metrics = {"samples": results}
        session.commit()
    except Exception as exc:  # noqa: BLE001
        logger.error("Validation for job %s failed: %s", job_id, exc, exc_info=True)
        if job:
            job.validation_status = "failed"
            metrics = job.validation_metrics or {}
            metrics.update({"error": str(exc)})
            job.validation_metrics = metrics
            session.commit()
        raise
    finally:
        try:
            if job and job.model_id:
                model_manager.unload_model(job.model_id)
        finally:
            session.close()


def _extract_validation_prompts(job: TrainingJob) -> List[str]:
    hyperparams = job.hyperparameters or {}
    prompts = hyperparams.get("validation_prompts")
    if isinstance(prompts, str):
        try:
            parsed = json.loads(prompts)
            if isinstance(parsed, list):
                prompts = parsed
        except json.JSONDecodeError:
            prompts = [p.strip() for p in prompts.splitlines() if p.strip()]
    if isinstance(prompts, list):
        cleaned = [str(prompt).strip() for prompt in prompts if str(prompt).strip()]
        if cleaned:
            return cleaned
    return DEFAULT_VALIDATION_PROMPTS


__all__ = ["build_training_dataset", "validate_trained_model"]

