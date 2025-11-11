"""
Service for persisting and managing incoming project requests.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4
from decimal import Decimal
import tempfile
import os

from sqlalchemy.orm import Session

from backend.config.settings import settings
from backend.models.project import Project
from backend.models.project_request import ProjectRequest
from backend.services.geocoding import yandex_geocoder
from backend.services.project_service import ProjectService
from backend.services.intake.models import IncomingAttachment, IncomingRequest
from backend.services.minio_service import minio_service
from backend.services.ocr.deepseek_service import deepseek_ocr_service
from backend.services.address_extractor import address_extractor
from backend.services.construction_zone_service import construction_zone_service
from backend.services.work_volume_extractor import work_volume_extractor, WorkVolumeEntry
from backend.services.work_volume_sources import (
    spreadsheet_volume_extractor,
    word_volume_extractor,
    pdf_ocr_volume_extractor,
    cad_volume_extractor,
    WorkVolumeResult,
)
from backend.services.project_timeline import ProjectTimelineEstimator
from backend.services.teo_pipeline import PreliminaryTEOPipeline
from backend.services.notifications.email_service import email_notification_service
from backend.services.market_price_service import market_price_service
from backend.services.notifications.telegram import manager_notification_service
from backend.models.auth import User
from backend.services.project_manager_rotation import ProjectManagerRotation

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
        metadata = dict(request.metadata) if request.metadata else {}

        if not request.project_location:
            extraction = address_extractor.extract(text=request.body, fallback_prompt=True)
            if extraction.address:
                metadata.setdefault("address_extraction_method", extraction.method)
                request.project_location = extraction.address
                logger.info("Address extracted via %s: %s", extraction.method, extraction.address)
            else:
                metadata.setdefault("address_extraction_method", extraction.method)

        self._enrich_with_geocode(request, metadata)
        analysis = metadata.setdefault("analysis", {})
        work_volume_data, volume_entries = self._extract_work_volumes(request, attachments)
        pending_manual_prices: List[str] = []
        if work_volume_data:
            analysis["work_volume"] = work_volume_data
            timeline = self._estimate_timeline(volume_entries, metadata)
            if timeline:
                analysis["timeline"] = timeline
            bundle = self._estimate_preliminary_cost(volume_entries, metadata)
            if bundle:
                cost_info = bundle.get("cost")
                labor_info = bundle.get("labor")
                if cost_info:
                    analysis["cost"] = cost_info
                    pending_manual_prices = self._prefetch_market_prices(cost_info)
                    if pending_manual_prices:
                        analysis["cost"]["manual_price_requests"] = pending_manual_prices
                if labor_info:
                    analysis["labor"] = labor_info

        entity = ProjectRequest(
            channel=request.channel.value,
            external_id=request.external_id,
            subject=request.subject,
            body=request.body,
            customer_name=request.customer_name,
            contact_email=request.contact_email,
            contact_phone=request.contact_phone,
            project_location=request.project_location,
            metadata_json=metadata,
            raw_payload=request.raw_payload,
            attachments=[attachment.__dict__ for attachment in attachments],
            status="received",
            processed=False,
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        self._notify_parties(entity)
        if pending_manual_prices:
            self._notify_price_requests(entity, pending_manual_prices)
        logger.info("Registered project request %s from channel %s", entity.id, entity.channel)
        return entity

    def create_project_from_request(
        self,
        request_id: int,
        *,
        owner_id: Optional[int] = None,
        manager_id: Optional[int] = None,
        mark_processed: bool = True,
    ) -> Project:
        request = (
            self.db.query(ProjectRequest)
            .filter(ProjectRequest.id == request_id)
            .one_or_none()
        )
        if not request:
            raise ValueError(f"ProjectRequest {request_id} not found")

        project_service = ProjectService(self.db)
        project = project_service.create_project_from_request(
            request, owner_id=owner_id, manager_id=manager_id
        )

        if mark_processed:
            request.processed = True
            request.status = "project_created"
            request.processed_at = datetime.utcnow()
        metadata = request.metadata_json or {}
        metadata.setdefault("project_id", project.id)
        request.metadata_json = metadata

        self.db.commit()
        self.db.refresh(request)
        return project

    def _notify_parties(self, request: ProjectRequest) -> None:
        metadata = request.metadata_json or {}
        notifications_meta: Dict[str, Any] = {}

        summary = self._build_request_summary(request)

        client_results = []
        if request.contact_email:
            client_results = email_notification_service.send(
                [request.contact_email],
                subject=f"BLDR.EMPIRE — заявка #{request.id} получена",
                body=(
                    "Здравствуйте!\n\n"
                    "Мы получили вашу заявку и приступаем к первичной оценке.\n\n"
                    f"{summary}\n"
                    "Команда свяжется с вами после завершения анализа.\n\n"
                    "С уважением,\n"
                    "BLDR.EMPIRE"
                ),
            )
        notifications_meta["client"] = [result.__dict__ for result in client_results] or "not_sent"

        manager_emails = self._collect_manager_emails()
        manager_results = []
        if manager_emails:
            manager_results = email_notification_service.send(
                manager_emails,
                subject=f"Новая заявка #{request.id}",
                body=(
                    "Поступила новая заявка на проект:\n\n"
                    f"{summary}\n"
                    "Просьба подготовить предварительную оценку."
                ),
            )
        notifications_meta["managers"] = [result.__dict__ for result in manager_results] or "not_sent"

        leadership_emails = [email for email in settings.LEADERSHIP_NOTIFICATION_EMAILS if email.strip()]
        leadership_results = []
        if leadership_emails:
            leadership_results = email_notification_service.send(
                leadership_emails,
                subject=f"[BLDR.EMPIRE] Новая заявка #{request.id}",
                body=(
                    "Команда получила новую заявку. Краткое содержание:\n\n"
                    f"{summary}\n"
                    "Дальнейшие обновления будут предоставлены после первичной оценки."
                ),
            )
        notifications_meta["leadership"] = [result.__dict__ for result in leadership_results] or "not_sent"

        metadata["notifications"] = notifications_meta
        request.metadata_json = metadata
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)

    def _collect_manager_emails(self) -> List[str]:
        rotation = ProjectManagerRotation(self.db)
        managers = rotation._load_managers()  # pylint: disable=protected-access
        if not managers:
            return []
        emails: List[str] = []
        for assignment in managers:
            user = self.db.query(User).filter(User.id == assignment.manager_id).one_or_none()
            if user and user.email:
                emails.append(user.email)
        return sorted(set(emails))

    def _build_request_summary(self, request: ProjectRequest) -> str:
        parts = [
            f"ID заявки: {request.id}",
            f"Канал: {request.channel}",
        ]
        if request.customer_name:
            parts.append(f"Клиент: {request.customer_name}")
        if request.contact_email:
            parts.append(f"Email: {request.contact_email}")
        if request.contact_phone:
            parts.append(f"Телефон: {request.contact_phone}")
        if request.project_location:
            parts.append(f"Локация: {request.project_location}")
        if request.subject:
            parts.append(f"Тема: {request.subject}")
        if request.body:
            body_preview = request.body[:400].strip()
            parts.append(f"Описание: {body_preview}")
        return "\n".join(parts)

    def _notify_price_requests(self, request: ProjectRequest, materials: List[str]) -> None:
        if not materials:
            return
        context = f"Заявка #{request.id}: {request.subject or 'без темы'}"
        manager_notification_service.notify_procurement(materials=materials[:20], context=context)
        metadata = request.metadata_json or {}
        analysis = metadata.setdefault("analysis", {})
        cost_meta = analysis.setdefault("cost", {})
        cost_meta["manual_price_requests_notified_at"] = datetime.utcnow().isoformat()
        cost_meta["manual_price_requests_ack"] = materials[:20]
        request.metadata_json = metadata
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)

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

    def _enrich_with_geocode(self, request: IncomingRequest, metadata: Dict[str, Any]) -> None:
        if not request.project_location or not yandex_geocoder:
            return
        try:
            result = yandex_geocoder.geocode(request.project_location, kind="house")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Yandex geocoder failed for %s: %s", request.project_location, exc)
            return

        if not result:
            logger.info("Yandex geocoder returned no data for %s", request.project_location)
            return

        geocode_metadata = result.to_metadata()
        metadata.setdefault("geocoding", geocode_metadata)
        if geocode_metadata.get("cadastral_number"):
            metadata.setdefault("cadastral_number", geocode_metadata["cadastral_number"])
        metadata.setdefault("coordinates", {"lat": result.latitude, "lon": result.longitude})
        metadata.setdefault("geocoding_latitude", result.latitude)
        metadata.setdefault("geocoding_longitude", result.longitude)
        if result.cadastral_number:
            metadata.setdefault("geocoding_cadastral_number", result.cadastral_number)

        zone_result = construction_zone_service.check(result.latitude, result.longitude)
        metadata.setdefault("development_zone", zone_result.zone_name)
        metadata.setdefault("zone_check_allowed", zone_result.allowed)
        metadata.setdefault("zone_check_rationale", zone_result.rationale)

    def _extract_work_volumes(
        self,
        request: IncomingRequest,
        attachments: List["StoredAttachment"],
    ) -> tuple[Optional[Dict[str, Any]], List[WorkVolumeEntry]]:
        results: List[WorkVolumeResult] = []
        warnings: List[str] = []

        if request.body:
            body_result = work_volume_extractor.extract_from_text(request.body)
            if body_result.entries:
                results.append(body_result)
            warnings.extend(body_result.warnings)

        for stored in attachments:
            if stored.text_content:
                text_result = work_volume_extractor.extract_from_text(stored.text_content)
                if text_result.entries:
                    results.append(text_result)
                warnings.extend(text_result.warnings)

            ext = os.path.splitext(stored.filename)[1].lower()
            extractor = None
            if ext in {".csv", ".xlsx", ".xls", ".xlsm", ".xltx"}:
                extractor = spreadsheet_volume_extractor
            elif ext in {".docx", ".doc"}:
                extractor = word_volume_extractor
            elif ext in {".pdf"}:
                extractor = pdf_ocr_volume_extractor
            elif ext in {".dwg", ".ifc"}:
                extractor = cad_volume_extractor

            if extractor:
                temp_path = self._download_attachment_to_temp(stored, ext or ".tmp")
                if not temp_path:
                    continue
                try:
                    result = extractor.extract(temp_path)
                    if result.entries:
                        results.append(result)
                    warnings.extend(result.warnings)
                except Exception as exc:  # noqa: BLE001
                    logger.debug("Failed to extract work volumes from %s: %s", stored.filename, exc)
                finally:
                    try:
                        os.remove(temp_path)
                    except OSError:
                        pass

        if not results:
            return None, []

        aggregated_entries: List[WorkVolumeEntry] = []
        for result in results:
            aggregated_entries.extend(result.entries)

        if not aggregated_entries:
            return None, []

        summary = self._build_work_volume_summary(aggregated_entries)
        entries_payload = [self._serialize_volume_entry(entry) for entry in aggregated_entries]
        return (
            {
                "entries": entries_payload,
                "summary": summary,
                "warnings": warnings,
                "sources_analyzed": len(results),
            },
            aggregated_entries,
        )

    def _download_attachment_to_temp(self, stored: "StoredAttachment", suffix: str) -> Optional[str]:
        try:
            data = minio_service.download_file("documents", stored.storage_path)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Failed to download attachment %s: %s", stored.filename, exc)
            return None
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(data)
        tmp.close()
        return tmp.name

    def _build_work_volume_summary(self, entries: List[WorkVolumeEntry]) -> Dict[str, Any]:
        total_quantity = Decimal("0")
        categories: Dict[str, Decimal] = {}
        for entry in entries:
            total_quantity += entry.quantity
            category = entry.category or "Прочее"
            categories.setdefault(category, Decimal("0"))
            categories[category] += entry.quantity
        return {
            "total_items": len(entries),
            "total_quantity": float(total_quantity),
            "by_category": {key: float(value) for key, value in categories.items()},
        }

    def _serialize_volume_entry(self, entry: WorkVolumeEntry) -> Dict[str, Any]:
        return {
            "code": entry.code,
            "name": entry.name,
            "quantity": float(entry.quantity),
            "unit": entry.unit,
            "category": entry.category,
            "parameters": entry.parameters,
        }

    def _estimate_timeline(
        self,
        entries: List[WorkVolumeEntry],
        metadata: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        if not entries:
            return None
        estimator = ProjectTimelineEstimator(self.db)
        try:
            return estimator.estimate(entries, metadata)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Timeline estimation failed: %s", exc)
            return None

    def _estimate_preliminary_cost(
        self,
        entries: List[WorkVolumeEntry],
        metadata: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        if not entries:
            return None
        pipeline = PreliminaryTEOPipeline(session=self.db)
        try:
            result = pipeline.process_entries(entries, top_k=3)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Preliminary cost estimation failed: %s", exc)
            return None

        cost_summary = result.cost.summary
        matches_payload = [
            {
                "volume_name": match.volume.name,
                "norm_code": match.norm_code,
                "reasoning": match.reasoning,
                "confidence": max(match.candidate_scores.values(), default=0.0),
            }
            for match in result.matches[:10]
        ]

        cost_payload = {
            "total_cost": float(cost_summary.total_cost),
            "by_category": {category: float(value) for category, value in cost_summary.by_category.items()},
            "missing_prices": cost_summary.missing_prices,
            "warnings": result.warnings,
            "matches": matches_payload,
        }

        labor_payload: Optional[Dict[str, Any]] = None
        if result.labor:
            labor_payload = {
                "total_labor_hours": result.labor.total_labor_hours,
                "total_worker_equivalent": result.labor.total_worker_equivalent,
                "worker_days": result.labor.worker_days,
                "schedules": result.labor.schedules,
                "entries": [
                    {
                        "volume_name": entry.volume_name,
                        "norm_code": entry.norm_code,
                        "labor_hours": entry.labor_hours,
                        "worker_equivalent": entry.worker_equivalent,
                        "resources": entry.resources,
                    }
                    for entry in result.labor.entries
                ],
                "assumptions": {"shift_hours": 8},
            }

        entries_payload = [
            {
                "name": e.name,
                "quantity": float(e.quantity),
                "unit": e.unit,
                "cost": float(e.cost),
                "category": e.category,
                "group": e.group,
                "price_per_unit": float(e.material_price.price_per_unit) if e.material_price else None,
                "source": e.material_price.source if e.material_price else None,
            }
            for e in result.cost.entries
        ]
        cost_payload["entries"] = entries_payload

        return {"cost": cost_payload, "labor": labor_payload}

    def _prefetch_market_prices(self, cost_analysis: Dict[str, Any]) -> List[str]:
        missing = cost_analysis.get("missing_prices") or cost_analysis.get("cost", {}).get("missing_prices") or []
        if not missing:
            return []
        unresolved: List[str] = []
        for name in missing[:20]:
            try:
                price = market_price_service.get_price(name)
                if price is None:
                    unresolved.append(name)
            except Exception as exc:  # noqa: BLE001
                logger.debug("Prefetch price failed for %s: %s", name, exc)
                unresolved.append(name)
        return unresolved


__all__ = ["ProjectRequestService"]

