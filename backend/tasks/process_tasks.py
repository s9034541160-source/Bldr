"""
Celery tasks orchestrating business process pipelines.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from celery import shared_task
from sqlalchemy.orm import Session

from backend.models import SessionLocal
from backend.services.intake.pipeline import IntakePipeline
from backend.services.intake.telegram_handler import telegram_handler_from_settings
from backend.services.project_request_service import ProjectRequestService
from backend.services.redis_service import redis_service
GOOGLE_FORMS_LAST_ROW_KEY = "intake:google_forms:last_row"


logger = logging.getLogger(__name__)


def _get_session() -> Session:
    return SessionLocal()


@shared_task(
    bind=True,
    name="processes.poll_email_inbox",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def poll_email_inbox(self, limit: int = 25) -> Dict[str, Any]:  # type: ignore[override]
    """Fetch emails from IMAP inbox and register them as project requests."""
    pipeline = IntakePipeline.from_settings()
    try:
        requests = pipeline.email_handler.fetch_unseen(limit=limit)
    except RuntimeError as exc:
        logger.warning("Email polling skipped: %s", exc)
        return {"status": "skipped", "reason": str(exc)}

    session = _get_session()
    service = ProjectRequestService(session)
    stored_ids: List[int] = []
    try:
        for request in requests:
            entity = service.register_request(request)
            stored_ids.append(entity.id)
        return {"status": "ok", "stored": len(stored_ids), "request_ids": stored_ids}
    finally:
        session.close()


@shared_task(name="processes.ingest_google_form_submission")
def ingest_google_form_submission(submission: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Google Form submission payload into request entity."""
    pipeline = IntakePipeline.from_settings()
    request = pipeline.forms_parser.parse_submission(submission)

    session = _get_session()
    service = ProjectRequestService(session)
    try:
        entity = service.register_request(request)
        return {"status": "ok", "request_id": entity.id}
    finally:
        session.close()


@shared_task(
    bind=True,
    name="processes.poll_google_forms",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def poll_google_forms(self) -> Dict[str, Any]:  # type: ignore[override]
    """
    Загружает новые ответы Google Forms и регистрирует заявки.
    """
    pipeline = IntakePipeline.from_settings()
    if not pipeline.forms_service:
        logger.warning("Google Forms service is not configured.")
        return {"status": "skipped", "reason": "service_missing"}

    try:
        last_row = redis_service.get(GOOGLE_FORMS_LAST_ROW_KEY)
        since_row = int(last_row) if last_row else None
    except Exception as exc:
        logger.warning("Failed to read last row from Redis: %s", exc)
        since_row = None

    requests = pipeline.forms_service.fetch_requests(since_row=since_row)
    if not requests:
        return {"status": "ok", "stored": 0, "request_ids": []}

    session = _get_session()
    service = ProjectRequestService(session)
    stored_ids: List[int] = []
    max_row_index = since_row or 1
    try:
        for request in requests:
            entity = service.register_request(request)
            stored_ids.append(entity.id)
            row_index = request.metadata.get("row_index") if isinstance(request.metadata, dict) else None
            if isinstance(row_index, int):
                max_row_index = max(max_row_index, row_index)
        try:
            redis_service.set(GOOGLE_FORMS_LAST_ROW_KEY, max_row_index, ex=86400)
        except Exception as exc:
            logger.warning("Failed to update last row index: %s", exc)
        return {"status": "ok", "stored": len(stored_ids), "request_ids": stored_ids, "last_row": max_row_index}
    finally:
        session.close()


@shared_task(name="processes.ingest_telegram_update")
def ingest_telegram_update(update: Dict[str, Any]) -> Dict[str, Any]:
    """Process Telegram bot update and persist as project request."""
    handler = telegram_handler_from_settings()
    request = handler.parse_update(update)

    session = _get_session()
    service = ProjectRequestService(session)
    try:
        entity = service.register_request(request)
        return {"status": "ok", "request_id": entity.id}
    finally:
        session.close()


@shared_task(name="processes.create_project_from_request")
def create_project_from_request(request_id: int, owner_id: int | None = None, manager_id: int | None = None) -> Dict[str, Any]:
    """
    Создать проект на основе заявки и отметить заявку обработанной.
    """
    session = _get_session()
    service = ProjectRequestService(session)
    try:
        project = service.create_project_from_request(
            request_id, owner_id=owner_id, manager_id=manager_id, mark_processed=True
        )
        return {"status": "ok", "project_id": project.id, "code": project.code}
    finally:
        session.close()


@shared_task(name="processes.process_pending_requests")
def process_pending_requests(limit: int = 10) -> Dict[str, Any]:
    """
    Создать проекты для отложенных заявок (batch processing).
    """
    session = _get_session()
    request_service = ProjectRequestService(session)
    stored: List[int] = []
    try:
        pending = request_service.list_pending(limit=limit)
        for item in pending:
            project = request_service.create_project_from_request(item.id)
            stored.append(project.id)
        return {"status": "ok", "processed": len(stored), "project_ids": stored}
    finally:
        session.close()


__all__ = [
    "poll_email_inbox",
    "ingest_google_form_submission",
    "ingest_telegram_update",
    "create_project_from_request",
    "process_pending_requests",
    "poll_google_forms",
]

