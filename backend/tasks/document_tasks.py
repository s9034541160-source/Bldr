"""
Celery tasks related to document processing.
"""

from __future__ import annotations

import logging
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from celery import shared_task
from sqlalchemy.orm import Session

from backend.models import Document, DocumentVersion, SessionLocal
from backend.services.minio_service import minio_service
from backend.services.rag_service import rag_service

logger = logging.getLogger(__name__)


@dataclass(slots=True, kw_only=True)
class DocumentIndexingResult:
    """Structured response for document indexing tasks."""

    document_id: int
    version_number: Optional[int]
    status: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _resolve_document_version(session: Session, document_id: int, version_number: Optional[int]) -> DocumentVersion:
    if version_number is None:
        document = session.query(Document).filter(Document.id == document_id).one_or_none()
        if document is None:
            raise ValueError(f"Document {document_id} not found")
        version = session.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id,
            DocumentVersion.version_number == document.version,
        ).one_or_none()
        if version is None:
            raise ValueError(f"Active version for document {document_id} not found")
        return version

    version = session.query(DocumentVersion).filter(
        DocumentVersion.document_id == document_id,
        DocumentVersion.version_number == version_number,
    ).one_or_none()

    if version is None:
        raise ValueError(f"Version {version_number} for document {document_id} not found")
    return version


@shared_task(
    bind=True,
    name="documents.reindex_document",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def reindex_document(  # type: ignore[override]
    self,
    document_id: int,
    version_number: Optional[int] = None,
    *,
    reprocess_chunks: bool = True,
) -> Dict[str, Any]:
    """
    Индексация документа или выбранной версии в фоновом режиме.

    Args:
        document_id: идентификатор документа
        version_number: номер версии (если не указан - актуальная)
        reprocess_chunks: пересобрать чанки при индексации
    """
    session = SessionLocal()
    temp_path: Optional[Path] = None
    try:
        version = _resolve_document_version(session, document_id, version_number)
        document = session.query(Document).filter(Document.id == document_id).one_or_none()
        if document is None:
            raise ValueError(f"Document {document_id} not found")

        file_bytes = minio_service.download_file("documents", version.file_path)
        suffix = Path(version.file_path).suffix or ".bin"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(file_bytes)
            temp_path = Path(temp_file.name)

        metadata = {
            "document_id": document.id,
            "version": version.version_number,
            "project_id": document.project_id,
            "document_type": document.document_type,
            "title": document.title,
            "mime_type": document.mime_type,
        }

        success = rag_service.index_file(
            document_id=f"{document.id}::v{version.version_number}",
            file_path=str(temp_path),
            metadata=metadata,
            chunk=reprocess_chunks,
        )

        status = "indexed" if success else "failed"
        logger.info("Document %s v%s indexing finished with status=%s", document_id, version.version_number, status)
        return DocumentIndexingResult(
            document_id=document.id,
            version_number=version.version_number,
            status=status,
            metadata=metadata,
        ).to_dict()
    except Exception as exc:
        logger.error("Document indexing failed (doc=%s, version=%s): %s", document_id, version_number, exc, exc_info=True)
        raise
    finally:
        session.close()
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                logger.warning("Unable to remove temp file %s", temp_path)


__all__ = ["reindex_document"]

