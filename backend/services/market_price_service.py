"""
Market price lookup with Redis caching (F1.02).
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Dict, Iterable, List, Optional

from backend.services.redis_service import redis_service

logger = logging.getLogger(__name__)

DEFAULT_CURRENCY = "RUB"
CACHE_PREFIX = "market_price"


@dataclass(slots=True)
class MaterialPrice:
    name: str
    unit: str
    price_per_unit: Decimal
    currency: str = DEFAULT_CURRENCY
    source: str = "stub"
    updated_at: datetime = datetime.utcnow()

    def to_dict(self) -> Dict[str, str]:
        data = asdict(self)
        data["price_per_unit"] = str(self.price_per_unit)
        data["updated_at"] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "MaterialPrice":
        return cls(
            name=data["name"],
            unit=data["unit"],
            price_per_unit=Decimal(data["price_per_unit"]),
            currency=data.get("currency", DEFAULT_CURRENCY),
            source=data.get("source", "stub"),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if data.get("updated_at")
            else datetime.utcnow(),
        )


class MarketPriceService:
    """Stubbed market price service with Redis cache."""

    def __init__(self, ttl_hours: int = 24) -> None:
        self.ttl = int(timedelta(hours=ttl_hours).total_seconds())

    def get_price(self, material: str, *, unit: Optional[str] = None) -> Optional[MaterialPrice]:
        material_norm = self._normalize(material)
        unit_norm = (unit or "").lower()
        cache_key = self._cache_key(material_norm, unit_norm)

        cached = redis_service.get(cache_key)
        if cached:
            try:
                return MaterialPrice.from_dict(cached)
            except Exception as exc:  # noqa: BLE001
                logger.debug("Failed to deserialize cached price for %s: %s", material_norm, exc)

        price = self._lookup_stub(material_norm, unit_norm)
        if price:
            redis_service.set(cache_key, price.to_dict(), ex=self.ttl)
        return price

    def get_prices_batch(self, materials: Iterable[str]) -> Dict[str, Optional[MaterialPrice]]:
        result: Dict[str, Optional[MaterialPrice]] = {}
        for name in materials:
            result[name] = self.get_price(name)
        return result

    def invalidate_cache(self, material: str, unit: Optional[str] = None) -> None:
        redis_service.delete(self._cache_key(self._normalize(material), (unit or "").lower()))

    # ------------------------------------------------------------------ #
    # Stub data
    # ------------------------------------------------------------------ #
    def _lookup_stub(self, material: str, unit: str) -> Optional[MaterialPrice]:
        database = self._stub_database()
        key = (material, unit or "шт")
        if key not in database:
            logger.info("Material price not found in stub database: %s (%s)", material, unit)
            return None

        price_value = database[key]
        return MaterialPrice(
            name=material,
            unit=unit or "шт",
            price_per_unit=price_value,
            source="stub_database",
        )

    def _stub_database(self) -> Dict[tuple[str, str], Decimal]:
        return {
            ("бетон м300", "м³"): Decimal("6200"),
            ("арматура a500", "т"): Decimal("82000"),
            ("кирпич керамический", "шт"): Decimal("28"),
            ("цемент м500", "т"): Decimal("9700"),
            ("щебень фракция 20-40", "м³"): Decimal("1450"),
            ("песок", "м³"): Decimal("650"),
            ("пвх труба 110мм", "м"): Decimal("210"),
            ("кабель ввгнг 3x2.5", "м"): Decimal("75"),
        }

    # ------------------------------------------------------------------ #
    # Utilities
    # ------------------------------------------------------------------ #
    def _cache_key(self, material: str, unit: str) -> str:
        return f"{CACHE_PREFIX}:{material}:{unit or 'шт'}"

    def _normalize(self, value: str) -> str:
        return value.strip().lower()


market_price_service = MarketPriceService()

__all__ = ["MaterialPrice", "MarketPriceService", "market_price_service"]


