"""
Service for creating and managing projects derived from incoming requests.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from backend.config.settings import settings
from backend.models.auth import User
from backend.models.project import Project
from backend.models.project_request import ProjectRequest
from backend.services.minio_service import minio_service
from backend.services.neo4j_service import neo4j_service
from backend.services.notifications.telegram import manager_notification_service
from backend.services.project_manager_rotation import ProjectManagerRotation
from backend.services.teo_report_service import teo_report_service
from backend.services.onec_export_service import onec_export_service
from backend.services.integrations.onec_service import onec_service

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ProjectService:
    """Создание карточек проектов и синхронизация с Neo4j."""

    db: Session

    def create_project_from_request(
        self,
        request: ProjectRequest,
        *,
        owner_id: Optional[int] = None,
        manager_id: Optional[int] = None,
    ) -> Project:
        owner = owner_id or self._extract_owner(request)
        if owner is None:
            raise ValueError("Owner ID is required to create a project.")

        manager = manager_id or self._extract_manager(request)
        metadata = request.metadata_json or {}

        project_code = self._generate_project_code()
        project_name = self._determine_project_name(request)
        description = request.body or self._extract_metadata_value(request, "description")
        project_uuid = str(uuid4())
        storage_path = f"projects/{project_uuid}"

        project = Project(
            name=project_name,
            description=description,
            code=project_code,
            uuid=project_uuid,
            storage_path=storage_path,
            owner_id=owner,
            manager_id=manager,
            status="planning",
        )

        self._apply_dates(project, request)
        self._apply_budget(project, request)
        self._apply_geodata(project, request)
        analysis = metadata.get("analysis") if isinstance(metadata.get("analysis"), dict) else None
        if analysis:
            self._apply_analysis(project, analysis)

        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)

        try:
            minio_service.ensure_project_structure(project.storage_path)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to create project storage structure for %s: %s", project.code, exc)

        integration_updates: Dict[str, Any] = {}

        if analysis:
            try:
                report_bytes = teo_report_service.build_preliminary_report(project, analysis)
                report_object = f"{project.storage_path}/reports/preliminary_teo_{project.code}.docx"
                minio_service.upload_file(
                    bucket_name="exports",
                    object_name=report_object,
                    data=report_bytes,
                    content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
                project.preliminary_teo_path = report_object
                integration_updates["teo_report"] = {
                    "path": report_object,
                    "generated_at": datetime.utcnow().isoformat(),
                }
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to generate preliminary TEO report for %s: %s", project.code, exc)

        try:
            export_result = onec_export_service.export(project, metadata, analysis)
            integration_updates["onec_export"] = export_result
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to export project %s to 1C: %s", project.code, exc)

        if integration_updates:
            metadata.setdefault("analysis", {})
            metadata["analysis"].update({k: v for k, v in integration_updates.items() if v})
            request.metadata_json = metadata
            self.db.add(request)
            self.db.add(project)
            self.db.commit()
            self.db.refresh(project)

        if project.manager_id:
            manager = self.db.query(User).filter(User.id == project.manager_id).one_or_none()
            if manager:
                manager_notification_service.notify_assignment(
                    manager,
                    project_code=project.code,
                    project_name=project.name,
                )

        self._sync_with_neo4j(project, request)
        logger.info("Created project %s (%s) from request %s", project.id, project.code, request.id)
        return project

    # --------------------------------------------------------------------- #
    # Helpers
    # --------------------------------------------------------------------- #

    def _generate_project_code(self) -> str:
        prefix = settings.PROJECT_CODE_PREFIX
        year = datetime.utcnow().year
        like_pattern = f"{prefix}-{year}-%"

        last_project = (
            self.db.query(Project)
            .filter(Project.code.like(like_pattern))
            .order_by(Project.code.desc())
            .first()
        )

        next_index = 1
        if last_project:
            try:
                next_index = int(last_project.code.split("-")[-1]) + 1
            except (ValueError, AttributeError):
                logger.warning("Failed to parse project code %s; restarting counter.", last_project.code)

        return f"{prefix}-{year}-{next_index:04d}"

    def _determine_project_name(self, request: ProjectRequest) -> str:
        if request.subject:
            return request.subject.strip()
        metadata = request.metadata_json or {}
        for key in ("project_name", "name", "title"):
            value = metadata.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return f"Project {datetime.utcnow():%Y-%m-%d %H:%M}"

    def _extract_owner(self, request: ProjectRequest) -> Optional[int]:
        metadata = request.metadata_json or {}
        owner = metadata.get("owner_id")
        if isinstance(owner, int):
            return owner
        return settings.DEFAULT_PROJECT_OWNER_ID

    def _extract_manager(self, request: ProjectRequest) -> Optional[int]:
        metadata = request.metadata_json or {}
        manager = metadata.get("manager_id")
        if isinstance(manager, int):
            return manager

        rotation = ProjectManagerRotation(self.db)
        return rotation.assign_next_manager()

    def _apply_dates(self, project: Project, request: ProjectRequest) -> None:
        metadata = request.metadata_json or {}
        for attr, key in (("start_date", "planned_start"), ("planned_end_date", "planned_end")):
            value = metadata.get(key)
            if isinstance(value, str):
                try:
                    parsed = datetime.fromisoformat(value).date()
                except ValueError:
                    logger.debug("Unable to parse date %s for %s", value, key)
                else:
                    setattr(project, attr, parsed)

    def _apply_budget(self, project: Project, request: ProjectRequest) -> None:
        metadata = request.metadata_json or {}
        budget = metadata.get("budget")
        if budget is None:
            return
        try:
            project.budget = Decimal(str(budget))
        except (InvalidOperation, TypeError):
            logger.debug("Invalid budget value %s for request %s", budget, request.id)

    def _apply_geodata(self, project: Project, request: ProjectRequest) -> None:
        metadata = request.metadata_json or {}
        geocode = metadata.get("geocode") or {}
        latitude = metadata.get("geocoding_latitude") or geocode.get("latitude")
        longitude = metadata.get("geocoding_longitude") or geocode.get("longitude")
        project.geo_latitude = self._to_decimal(latitude)
        project.geo_longitude = self._to_decimal(longitude)
        cadastral_number = metadata.get("geocoding_cadastral_number") or geocode.get("cadastral_number")
        if cadastral_number:
            project.cadastral_number = str(cadastral_number)
        zone_name = metadata.get("development_zone")
        if isinstance(zone_name, str):
            project.development_zone = zone_name
        allowed = metadata.get("zone_check_allowed")
        if isinstance(allowed, bool):
            project.zone_allowed = allowed

    def _extract_metadata_value(self, request: ProjectRequest, key: str) -> Optional[str]:
        metadata = request.metadata_json or {}
        value = metadata.get(key)
        if isinstance(value, str):
            return value
        return None

    def _apply_analysis(self, project: Project, analysis: Dict[str, Any]) -> None:
        if not analysis:
            return

        timeline = analysis.get("timeline")
        if isinstance(timeline, dict):
            duration = timeline.get("estimated_duration_days")
            if isinstance(duration, (int, float)):
                project.planned_duration_days = int(duration)
            start = self._parse_iso_date(timeline.get("estimated_start"))
            if start:
                project.expected_start = start
            completion = self._parse_iso_date(timeline.get("estimated_completion"))
            if completion:
                project.expected_completion = completion

        cost_data = analysis.get("cost")
        if isinstance(cost_data, dict):
            total_cost = cost_data.get("total_cost")
            if total_cost is not None:
                try:
                    project.preliminary_budget = Decimal(str(total_cost))
                except (InvalidOperation, TypeError):
                    logger.debug("Invalid preliminary cost %s for project %s", total_cost, project.code)

    def _to_decimal(self, value: Any) -> Optional[Decimal]:
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError):
            return None

    def _parse_iso_date(self, value: Any) -> Optional[date]:
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value).date()
            except ValueError:
                logger.debug("Unable to parse ISO date: %s", value)
                return None
        return None

    def _sync_with_neo4j(self, project: Project, request: ProjectRequest) -> None:
        if not neo4j_service:
            return
        metadata = request.metadata_json or {}
        geocoding: Dict[str, Any] = metadata.get("geocoding") or {}
        coords = metadata.get("coordinates") or geocoding.get("coordinates") or {}

        params = {
            "id": project.id,
            "uuid": project.uuid,
            "code": project.code,
            "name": project.name,
            "status": project.status,
            "description": project.description,
            "receivedAt": request.received_at.isoformat() if request.received_at else None,
            "createdAt": project.created_at.isoformat() if project.created_at else None,
            "customerName": request.customer_name,
            "location": request.project_location,
            "latitude": float(project.geo_latitude) if project.geo_latitude is not None else coords.get("lat"),
            "longitude": float(project.geo_longitude) if project.geo_longitude is not None else coords.get("lon"),
            "cadastralNumber": project.cadastral_number or metadata.get("cadastral_number"),
            "storagePath": project.storage_path,
            "developmentZone": project.development_zone,
            "zoneAllowed": project.zone_allowed,
            "plannedDurationDays": project.planned_duration_days,
            "expectedStart": project.expected_start.isoformat() if project.expected_start else None,
            "expectedCompletion": project.expected_completion.isoformat() if project.expected_completion else None,
            "preliminaryBudget": float(project.preliminary_budget) if project.preliminary_budget is not None else None,
            "preliminaryTeoPath": project.preliminary_teo_path,
        }

        query = """
        MERGE (p:Project {id: $id})
        SET p.code = $code,
            p.name = $name,
            p.status = $status,
            p.description = $description,
            p.receivedAt = $receivedAt,
            p.createdAt = $createdAt,
            p.customerName = $customerName,
            p.location = $location,
            p.latitude = $latitude,
            p.longitude = $longitude,
            p.cadastralNumber = $cadastralNumber,
            p.storagePath = $storagePath,
            p.uuid = $uuid,
            p.developmentZone = $developmentZone,
            p.zoneAllowed = $zoneAllowed,
            p.plannedDurationDays = $plannedDurationDays,
            p.expectedStart = $expectedStart,
            p.expectedCompletion = $expectedCompletion,
            p.preliminaryBudget = $preliminaryBudget,
            p.preliminaryTeoPath = $preliminaryTeoPath
        """
        try:
            neo4j_service.execute_query(query, params)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to sync project %s with Neo4j: %s", project.id, exc)


