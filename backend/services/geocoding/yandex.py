"""
Yandex Geocoder integration utilities.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import requests
from requests import Response

from backend.config.settings import settings

logger = logging.getLogger(__name__)

CADASTRAL_PATTERN = re.compile(r"^\d{2}:\d{2}:[0-9]{6,}:\d+$")


@dataclass(slots=True)
class GeocodeResult:
    """Normalized representation of Yandex geocode response."""

    latitude: float
    longitude: float
    precision: Optional[str] = None
    address_text: Optional[str] = None
    postal_code: Optional[str] = None
    components: List[Dict[str, Any]] = field(default_factory=list)
    bounding_box: Optional[Dict[str, List[float]]] = None
    source: Dict[str, Any] = field(default_factory=dict)

    @property
    def cadastral_number(self) -> Optional[str]:
        for component in self.components:
            kind = component.get("kind")
            name = component.get("name")
            if kind == "other" and isinstance(name, str) and CADASTRAL_PATTERN.match(name):
                return name
        return None

    def to_metadata(self) -> Dict[str, Any]:
        result = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "precision": self.precision,
            "address_text": self.address_text,
            "postal_code": self.postal_code,
            "cadastral_number": self.cadastral_number,
            "components": self.components,
        }
        if self.bounding_box:
            result["bounding_box"] = self.bounding_box
        return result


@dataclass(slots=True)
class YandexGeocoder:
    """Client for Yandex Geocoder API."""

    api_key: str
    base_url: str = settings.YANDEX_GEOCODER_URL
    lang: str = settings.YANDEX_GEOCODER_LANG
    session: requests.Session = field(default_factory=requests.Session)

    def geocode(self, query: str, *, kind: Optional[str] = None) -> Optional[GeocodeResult]:
        params = {
            "apikey": self.api_key,
            "geocode": query,
            "format": "json",
            "lang": self.lang,
            "results": 1,
        }
        if kind:
            params["kind"] = kind

        logger.debug("Requesting Yandex geocoder for %s", query)
        response = self.session.get(self.base_url, params=params, timeout=10)
        response.raise_for_status()
        return self._parse_response(response)

    def _parse_response(self, response: Response) -> Optional[GeocodeResult]:
        payload = response.json()
        collection = payload.get("response", {}).get("GeoObjectCollection", {})
        members = collection.get("featureMember") or []
        if not members:
            return None

        geo_object = members[0].get("GeoObject", {})
        meta = geo_object.get("metaDataProperty", {}).get("GeocoderMetaData", {})
        address = meta.get("Address", {})
        components = address.get("Components", [])

        point = geo_object.get("Point", {}).get("pos")
        if not point:
            return None

        lon_str, lat_str = point.split()
        latitude = float(lat_str)
        longitude = float(lon_str)

        bounded_by = geo_object.get("boundedBy", {}).get("Envelope")
        bbox = None
        if bounded_by:
            try:
                lower = [float(x) for x in bounded_by["lowerCorner"].split()]
                upper = [float(x) for x in bounded_by["upperCorner"].split()]
                bbox = {"lower_corner": lower, "upper_corner": upper}
            except (KeyError, ValueError):
                bbox = None

        return GeocodeResult(
            latitude=latitude,
            longitude=longitude,
            precision=meta.get("precision"),
            address_text=meta.get("text"),
            postal_code=address.get("postal_code"),
            components=components,
            bounding_box=bbox,
            source=geo_object,
        )


def _build_client() -> Optional[YandexGeocoder]:
    if not settings.YANDEX_GEOCODER_API_KEY:
        logger.info("YANDEX_GEOCODER_API_KEY is not configured; geocoding disabled.")
        return None
    return YandexGeocoder(api_key=settings.YANDEX_GEOCODER_API_KEY)


yandex_geocoder = _build_client()

__all__ = ["GeocodeResult", "YandexGeocoder", "yandex_geocoder"]


