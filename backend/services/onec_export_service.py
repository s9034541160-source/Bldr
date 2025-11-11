"""
Интеграция с 1С: экспорт карточки проекта и предварительного ТЭО.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional
from xml.etree.ElementTree import Element, SubElement, tostring

import requests

from backend.config.settings import settings
from backend.models.project import Project

logger = logging.getLogger(__name__)


class OneCExportService:
    """
    Готовит данные проекта и передаёт их в 1С.
    """

    def __init__(self, base_url: Optional[str], token: Optional[str]) -> None:
        self.base_url = base_url
        self.token = token

    def build_payload(
        self,
        project: Project,
        metadata: Optional[Dict[str, Any]],
        analysis: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        volumes = (analysis or {}).get("work_volume", {})
        cost = (analysis or {}).get("cost", {})
        timeline = (analysis or {}).get("timeline", {})

        payload: Dict[str, Any] = {
            "project": {
                "code": project.code,
                "uuid": project.uuid,
                "name": project.name,
                "status": project.status,
                "expected_start": project.expected_start.isoformat() if project.expected_start else None,
                "expected_completion": project.expected_completion.isoformat() if project.expected_completion else None,
                "planned_duration_days": project.planned_duration_days,
                "preliminary_budget": float(project.preliminary_budget) if project.preliminary_budget else None,
                "development_zone": project.development_zone,
                "zone_allowed": project.zone_allowed,
            },
            "customer": {
                "name": metadata.get("customer_name") if metadata else None,
                "contact_email": metadata.get("contact_email") if metadata else None,
                "contact_phone": metadata.get("contact_phone") if metadata else None,
            },
            "location": {
                "address": metadata.get("project_location") if metadata else None,
                "latitude": float(project.geo_latitude) if project.geo_latitude else None,
                "longitude": float(project.geo_longitude) if project.geo_longitude else None,
                "cadastral_number": project.cadastral_number,
            },
            "work_volume": volumes,
            "cost": cost,
            "timeline": timeline,
        }
        return payload

    def build_xml(self, payload: Dict[str, Any]) -> str:
        root = Element("ProjectExport")
        project_node = SubElement(root, "Project")
        for key, value in payload.get("project", {}).items():
            node = SubElement(project_node, key)
            node.text = "" if value is None else str(value)

        customer_node = SubElement(root, "Customer")
        for key, value in payload.get("customer", {}).items():
            node = SubElement(customer_node, key)
            node.text = "" if value is None else str(value)

        location_node = SubElement(root, "Location")
        for key, value in payload.get("location", {}).items():
            node = SubElement(location_node, key)
            node.text = "" if value is None else str(value)

        vols = SubElement(root, "WorkVolume")
        for entry in payload.get("work_volume", {}).get("entries", [])[:50]:
            item = SubElement(vols, "Item")
            for key, value in entry.items():
                node = SubElement(item, key)
                node.text = "" if value is None else str(value)

        costs = SubElement(root, "Cost")
        for key, value in payload.get("cost", {}).items():
            node = SubElement(costs, key)
            node.text = "" if value is None else str(value)

        timeline = SubElement(root, "Timeline")
        for key, value in payload.get("timeline", {}).items():
            node = SubElement(timeline, key)
            node.text = "" if value is None else str(value)

        return tostring(root, encoding="utf-8").decode("utf-8")

    def export(
        self,
        project: Project,
        metadata: Optional[Dict[str, Any]],
        analysis: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        payload = self.build_payload(project, metadata, analysis)
        xml_payload = self.build_xml(payload)

        if not self.base_url:
            logger.info("ONEC_API_URL is not configured. Skipping export.")
            return {"status": "skipped", "reason": "url_not_configured", "payload": payload}

        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        try:
            response = requests.post(
                f"{self.base_url.rstrip('/')}/projects/import",
                json={"data": payload, "xml": xml_payload},
                headers=headers,
                timeout=15,
            )
            response.raise_for_status()
            result = response.json() if response.headers.get("Content-Type", "").startswith("application/json") else {}
            return {
                "status": "success",
                "response": result,
                "exported_at": datetime.utcnow().isoformat(),
            }
        except requests.RequestException as exc:
            logger.warning("Failed to export project %s to 1C: %s", project.code, exc)
            return {"status": "failed", "reason": str(exc), "payload": payload, "xml": xml_payload}


onec_export_service = OneCExportService(settings.ONEC_API_URL, settings.ONEC_API_TOKEN)

__all__ = ["onec_export_service", "OneCExportService"]


