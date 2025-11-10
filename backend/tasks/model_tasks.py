"""
Celery tasks for model fine-tuning and maintenance via Unsloth.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from celery import shared_task

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
def fine_tune_unsloth(self, payload: Dict[str, Any]) -> Dict[str, Any]:  # type: ignore[override]
    """
    Фоновая задача дообучения модели через Unsloth.

    Args:
        payload: словарь параметров FineTuneRequest
    """
    config = FineTuneRequest(**payload)
    logger.info(
        "Starting unsloth fine-tune for %s using dataset %s",
        config.base_model_id or "default",
        config.dataset_path,
    )
    tuner = UnslothFineTuner()
    result = tuner.train(config)
    return result.to_dict()


__all__ = ["fine_tune_unsloth"]

