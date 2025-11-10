"""
Utility for dispatching Celery tasks from application code.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from celery import signature

from backend.config.settings import settings
from backend.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@dataclass(slots=True, kw_only=True)
class TaskDispatchResult:
    """Structured response when enqueuing Celery task."""

    task_id: str
    queue: str
    task_name: str
    eta: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskQueue:
    """Centralised helper for submitting Celery tasks with consistent logging."""

    def __init__(self):
        self._app = celery_app

    def enqueue(
        self,
        *,
        task_name: str,
        queue: Optional[str] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        countdown: Optional[int] = None,
        eta: Optional[datetime] = None,
    ) -> TaskDispatchResult:
        sig = signature(task_name, kwargs=kwargs or {})
        async_result = sig.apply_async(queue=queue, countdown=countdown, eta=eta)
        dispatch = TaskDispatchResult(
            task_id=async_result.id,
            queue=queue or self._app.conf.task_default_queue,
            task_name=task_name,
            eta=eta.isoformat() if eta else None,
        )
        logger.info("Task dispatched: %s", dispatch)
        return dispatch

    def schedule_document_indexing(
        self,
        *,
        document_id: int,
        version_number: Optional[int] = None,
        reprocess_chunks: bool = True,
    ) -> TaskDispatchResult:
        return self.enqueue(
            task_name="documents.reindex_document",
            queue=settings.CELERY_DOCUMENT_QUEUE,
            kwargs={
                "document_id": document_id,
                "version_number": version_number,
                "reprocess_chunks": reprocess_chunks,
            },
        )

    def schedule_email_polling(self, *, limit: int = 25) -> TaskDispatchResult:
        return self.enqueue(
            task_name="processes.poll_email_inbox",
            queue=settings.CELERY_PROCESS_QUEUE,
            kwargs={"limit": limit},
        )

    def schedule_model_finetune(
        self,
        *,
        dataset_path: str,
        base_model_id: Optional[str] = None,
        output_dir: Optional[str] = None,
        extra_kwargs: Optional[Dict[str, Any]] = None,
    ) -> TaskDispatchResult:
        payload = {
            "dataset_path": dataset_path,
            "base_model_id": base_model_id,
            "output_dir": output_dir,
        }
        if extra_kwargs:
            payload.update(extra_kwargs)
        return self.enqueue(
            task_name="models.fine_tune_unsloth",
            queue=settings.CELERY_MODEL_QUEUE,
            kwargs=payload,
        )


task_queue = TaskQueue()


__all__ = ["task_queue", "TaskQueue", "TaskDispatchResult"]

