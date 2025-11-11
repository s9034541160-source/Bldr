"""
Интеграция с 1С: экспорт данных проекта и синхронизация.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

import requests
from dicttoxml import dicttoxml  # type: ignore

from backend.config.settings import settings
from backend.models.project import Project
from backend.models.project_request import ProjectRequest

logger = logging.getLogger(__name__)


class OneCService:
    """
    Клиент для интеграции с 1С.
    """

    def __init__(self) -> None:
        self.api_url = settings.ONEC_API_URL
        self.api_token = settings.ONEC_API_TOKEN

    def is_configured(self) -> bool:
        return bool(self.api_url and self.api_token)

    def build_payload(
        self,
        *,
        project: Project,
        request: Optional[ProjectRequest] = None,
        analysis: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        analysis = analysis or {}
        cost = analysis.get("cost") or {}
        timeline = analysis.get("timeline") or {}
        work_volume = analysis.get("work_volume") or {}

        payload: Dict[str, Any] = {
            "project": {
                "id": project.id,
                "code": project.code,
                "name": project.name,
                "status": project.status,
                "teo_approval_status": getattr(project, "teo_approval_status", None),
                "teo_approved_at": project.teo_approved_at.isoformat() if project.teo_approved_at else None,
                "teo_approval_route": getattr(project, "teo_approval_route", None),
                "expected_start": project.expected_start.isoformat() if project.expected_start else None,
                "expected_completion": project.expected_completion.isoformat()
                if project.expected_completion
                else None,
                "planned_duration_days": project.planned_duration_days,
                "preliminary_budget": float(project.preliminary_budget or 0),
                "development_zone": project.development_zone,
                "zone_allowed": project.zone_allowed,
            },
            "cost": cost,
            "timeline": timeline,
            "work_volume": work_volume,
        }

        if request:
            payload["request"] = {
                "id": request.id,
                "channel": request.channel,
                "customer_name": request.customer_name,
                "contact_email": request.contact_email,
                "contact_phone": request.contact_phone,
                "project_location": request.project_location,
            }

        return payload

    def payload_to_xml(self, payload: Dict[str, Any]) -> str:
        xml_bytes = dicttoxml(payload, custom_root="ProjectTEO", attr_type=False)
        return xml_bytes.decode("utf-8")

    def send_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_configured():
            raise RuntimeError("1C API is not configured.")

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        response = requests.post(self.api_url, headers=headers, data=json.dumps(payload), timeout=30)
        response.raise_for_status()

        try:
            return response.json()
        except ValueError:
            return {"raw_response": response.text}


onec_service = OneCService()

__all__ = ["onec_service", "OneCService"]


