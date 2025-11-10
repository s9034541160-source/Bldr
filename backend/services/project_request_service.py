"""
Service for persisting and managing incoming project requests.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from backend.models.project_request import ProjectRequest
from backend.services.intake.models import IncomingAttachment, IncomingRequest
from backend.services.minio_service import minio_service
from backend.services.ocr.deepseek_service import deepseek_ocr_service

logger = logging.getLogger(__name__)


@dataclass(slots=True, kw_only=True)
class StoredAttachment:
    filename: str
    content_type: str
    storage_path: str
    size: Optional[int] = None
    text_content: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)


class ProjectRequestService:
    """Работа с входящими заявками: сохранение, отметка обработки и поиск."""

    def __init__(self, db: Session):
        self.db = db

    def register_request(self, request: IncomingRequest) -> ProjectRequest:
        attachments = [self._store_attachment(attachment) for attachment in request.attachments]

        entity = ProjectRequest(
            channel=request.channel.value,
            external_id=request.external_id,
            subject=request.subject,
            body=request.body,
            customer_name=request.customer_name,
            contact_email=request.contact_email,
            contact_phone=request.contact_phone,
            project_location=request.project_location,
            metadata=request.metadata,
            raw_payload=request.raw_payload,
            attachments=[attachment.__dict__ for attachment in attachments],
            status="received",
            processed=False,
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        logger.info("Registered project request %s from channel %s", entity.id, entity.channel)
        return entity

    def mark_processed(self, request_id: int, *, status: str = "processed") -> ProjectRequest:
        request = self.db.query(ProjectRequest).filter(ProjectRequest.id == request_id).one_or_none()
        if not request:
            raise ValueError(f"ProjectRequest {request_id} not found")
        request.processed = True
        request.status = status
        request.processed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(request)
        return request

    def list_pending(self, limit: int = 50) -> List[ProjectRequest]:
        return (
            self.db.query(ProjectRequest)
            .filter(ProjectRequest.processed.is_(False))
            .order_by(ProjectRequest.received_at.asc())
            .limit(limit)
            .all()
        )

    def _store_attachment(self, attachment: IncomingAttachment) -> StoredAttachment:
        storage_path = f"incoming/{uuid4().hex}/{attachment.filename}"
        text_content = attachment.text_content or self._perform_ocr(attachment)

        if attachment.content:
            minio_service.upload_file(
                bucket_name="documents",
                object_name=storage_path,
                data=attachment.content,
                content_type=attachment.content_type,
            )

        return StoredAttachment(
            filename=attachment.filename,
            content_type=attachment.content_type,
            storage_path=storage_path,
            size=attachment.size or (len(attachment.content) if attachment.content else None),
            text_content=text_content,
            metadata={**attachment.metadata, "ocr_performed": str(bool(text_content))},
        )

    def _perform_ocr(self, attachment: IncomingAttachment) -> Optional[str]:
        if not attachment.content or not attachment.content_type.startswith("image/"):
            return None
        try:
            text = deepseek_ocr_service.extract_text(attachment.content)
            return text or None
        except Exception as exc:  # noqa: BLE001
            logger.debug("DeepSeek OCR failed for %s: %s", attachment.filename, exc)
            return None


__all__ = ["ProjectRequestService"]

