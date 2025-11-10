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


__all__ = ["poll_email_inbox", "ingest_google_form_submission", "ingest_telegram_update"]

