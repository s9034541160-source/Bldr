"""
Celery application configuration for BLDR.EMPIRE.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, Iterable

from celery import Celery
from kombu import Exchange, Queue

from backend.config.settings import settings

logger = logging.getLogger(__name__)


@dataclass(slots=True, kw_only=True)
class QueueDefinition:
    """Lightweight description of a Celery queue."""

    name: str
    routing_key: str
    durable: bool = True
    exchange_type: str = "direct"

    def as_queue(self) -> Queue:
        exchange = Exchange(self.name, type=self.exchange_type, durable=self.durable)
        return Queue(
            name=self.name,
            exchange=exchange,
            routing_key=self.routing_key,
            durable=self.durable,
        )


def _build_queues(definitions: Iterable[QueueDefinition]) -> Iterable[Queue]:
    for definition in definitions:
        yield definition.as_queue()


celery_app = Celery(
    "bldr.empire",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "backend.tasks.document_tasks",
        "backend.tasks.process_tasks",
        "backend.tasks.system_tasks",
        "backend.tasks.training_tasks",
        "backend.tasks.model_tasks",
    ],
)

queue_definitions = [
    QueueDefinition(name=settings.CELERY_DEFAULT_QUEUE, routing_key="default"),
    QueueDefinition(name=settings.CELERY_DOCUMENT_QUEUE, routing_key=settings.CELERY_DOCUMENT_QUEUE),
    QueueDefinition(name=settings.CELERY_PROCESS_QUEUE, routing_key=settings.CELERY_PROCESS_QUEUE),
    QueueDefinition(name=settings.CELERY_MONITORING_QUEUE, routing_key=settings.CELERY_MONITORING_QUEUE),
    QueueDefinition(name=settings.CELERY_MODEL_QUEUE, routing_key=settings.CELERY_MODEL_QUEUE),
]

celery_app.conf.update(
    task_default_queue=settings.CELERY_DEFAULT_QUEUE,
    task_queues=list(_build_queues(queue_definitions)),
    task_routes={
        "documents.reindex_document": {"queue": settings.CELERY_DOCUMENT_QUEUE},
        "processes.poll_email_inbox": {"queue": settings.CELERY_PROCESS_QUEUE},
        "processes.ingest_google_form_submission": {"queue": settings.CELERY_PROCESS_QUEUE},
        "processes.ingest_telegram_update": {"queue": settings.CELERY_PROCESS_QUEUE},
        "training.build_dataset": {"queue": settings.CELERY_PROCESS_QUEUE},
        "system.health_check": {"queue": settings.CELERY_MONITORING_QUEUE},
        "models.fine_tune_unsloth": {"queue": settings.CELERY_MODEL_QUEUE},
        "training.validate_model": {"queue": settings.CELERY_MODEL_QUEUE},
    },
    broker_connection_retry_on_startup=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Moscow",
    enable_utc=True,
    result_expires=settings.CELERY_RESULT_EXPIRES,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    worker_send_task_events=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
)

celery_app.autodiscover_tasks(["backend.tasks"])


@celery_app.on_after_configure.connect
def _startup_banner(*_args, **_kwargs) -> None:
    """Log Celery bootstrap configuration once worker starts."""
    logger.info(
        "Celery configured (broker=%s, backend=%s, default_queue=%s)",
        settings.celery_broker_url,
        settings.celery_result_backend,
        settings.CELERY_DEFAULT_QUEUE,
    )


__all__ = ["celery_app"]

