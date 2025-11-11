"""
Сервис проверки зоны застройки на основе координат.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from backend.config.settings import settings
from backend.services.geocoding.yandex import yandex_geocoder

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ZoneCheckResult:
    zone_name: Optional[str]
    allowed: Optional[bool]
    rationale: Optional[str] = None

    def to_metadata(self) -> dict:
        return {
            "zone_name": self.zone_name,
            "allowed": self.allowed,
            "rationale": self.rationale,
        }


class ConstructionZoneService:
    """
    Определяет, входит ли площадка в допустимую зону застройки.
    """

    def check(self, latitude: float, longitude: float) -> ZoneCheckResult:
        if not yandex_geocoder:
            logger.info("Yandex geocoder unavailable; zone check skipped.")
            return ZoneCheckResult(zone_name=None, allowed=None, rationale="geocoder_unavailable")

        query = f"{longitude},{latitude}"
        try:
            result = yandex_geocoder.geocode(query, kind="district")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to determine construction zone: %s", exc)
            return ZoneCheckResult(zone_name=None, allowed=None, rationale="geocoder_error")

        if not result or not result.address_text:
            return ZoneCheckResult(zone_name=None, allowed=None, rationale="no_data")

        zone_name = result.address_text
        normalized = zone_name.lower()
        allowed = None
        rationale = "no_policy"

        for pattern in settings.ALLOWED_DEVELOPMENT_ZONES:
            if pattern.lower() in normalized:
                allowed = True
                rationale = f"matched_policy:{pattern}"
                break

        if allowed is None:
            for pattern in settings.RESTRICTED_DEVELOPMENT_ZONES:
                if pattern.lower() in normalized:
                    allowed = False
                    rationale = f"restricted_policy:{pattern}"
                    break

        return ZoneCheckResult(zone_name=zone_name, allowed=allowed, rationale=rationale)


construction_zone_service = ConstructionZoneService()

__all__ = ["construction_zone_service", "ConstructionZoneService", "ZoneCheckResult"]


