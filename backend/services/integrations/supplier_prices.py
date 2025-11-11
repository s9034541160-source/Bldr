"""
Simulated supplier price APIs for F1.02 market price lookup.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Iterable, List, Optional

from backend.services.work_volume_extractor import WorkVolumeEntry

SUPPLIERS = ("supplier_a", "supplier_b", "supplier_c")


@dataclass(slots=True)
class SupplierPrice:
    material: str
    unit: str
    price_per_unit: Decimal
    currency: str
    supplier: str
    delivery_days: int
    validity_days: int

    def to_dict(self) -> Dict[str, str]:
        return {
            "name": self.material,
            "unit": self.unit,
            "price_per_unit": str(self.price_per_unit),
            "currency": self.currency,
            "supplier": self.supplier,
            "delivery_days": str(self.delivery_days),
            "validity_days": str(self.validity_days),
        }


BASE_DATABASE: Dict[str, Dict[str, Decimal]] = {
    "бетон м300": {"м³": Decimal("6100")},
    "арматура a500": {"т": Decimal("81500")},
    "кирпич керамический": {"шт": Decimal("26")},
    "цемент м500": {"т": Decimal("9500")},
    "щебень фракция 20-40": {"м³": Decimal("1400")},
    "песок": {"м³": Decimal("630")},
    "пвх труба 110мм": {"м": Decimal("205")},
    "кабель ввгнг 3x2.5": {"м": Decimal("72")},
    "стеклопакет 4-16-4": {"м²": Decimal("6200")},
    "сетка сварная 100x100": {"м²": Decimal("190")},
}


SUPPLIER_MARKUP: Dict[str, float] = {
    "supplier_a": 0.05,
    "supplier_b": 0.08,
    "supplier_c": 0.03,
}

SUPPLIER_DELIVERY_DAYS: Dict[str, int] = {
    "supplier_a": 5,
    "supplier_b": 7,
    "supplier_c": 4,
}


def fetch_supplier_prices(
    supplier_id: str,
    *,
    material: str,
    unit: str,
    country: str = "ru",
) -> List[Dict[str, str]]:
    material_norm = material.strip().lower()
    unit_norm = unit.strip().lower() or "шт"
    if supplier_id not in SUPPLIER_MARKUP:
        return []
    base_price = BASE_DATABASE.get(material_norm, {}).get(unit_norm)
    if base_price is None:
        return []

    margin = SUPPLIER_MARKUP[supplier_id]
    variability = Decimal(str(random.uniform(-0.02, 0.02)))
    final_price = base_price * (Decimal(str(1 + margin)) + variability)
    final_price = final_price.quantize(Decimal("0.01"))

    offer = SupplierPrice(
        material=material_norm,
        unit=unit_norm,
        price_per_unit=final_price,
        currency="RUB" if country == "ru" else "USD",
        supplier=supplier_id,
        delivery_days=SUPPLIER_DELIVERY_DAYS[supplier_id],
        validity_days=14,
    )
    return [offer.to_dict()]


def enrich_missing_entries(entries: Iterable[WorkVolumeEntry]) -> List[str]:
    materials = set()
    for entry in entries:
        materials.add(entry.name.strip().lower())
    return sorted(materials)


__all__ = ["SUPPLIERS", "fetch_supplier_prices", "SupplierPrice", "enrich_missing_entries"]


