"""
Preliminary cost estimation for F1.02 based on work volumes and market prices.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List, Optional

from backend.services.market_price_service import MaterialPrice, market_price_service
from backend.services.work_volume_extractor import (
    WorkVolumeEntry,
    WorkVolumeResult,
    WorkVolumeSummary,
    work_volume_extractor,
)

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class WorkCostEntry:
    name: str
    quantity: Decimal
    unit: str
    cost: Decimal
    material_price: Optional[MaterialPrice] = None
    source_line: Optional[str] = None
    code: Optional[str] = None
    category: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


@dataclass(slots=True)
class CostSummary:
    total_cost: Decimal
    by_category: Dict[str, Decimal] = field(default_factory=dict)
    missing_prices: List[str] = field(default_factory=list)


@dataclass(slots=True)
class PreliminaryCostResult:
    entries: List[WorkCostEntry]
    summary: CostSummary
    extraction: WorkVolumeResult


class PreliminaryCostService:
    """Compute preliminary estimate using work volumes and market prices."""

    def estimate_from_file(self, file_path: str) -> PreliminaryCostResult:
        extraction = work_volume_extractor.extract_from_file(file_path)
        return self.estimate_from_entries(extraction.entries, extraction)

    def estimate_from_entries(
        self,
        entries: List[WorkVolumeEntry],
        extraction: Optional[WorkVolumeResult] = None,
    ) -> PreliminaryCostResult:
        cost_entries: List[WorkCostEntry] = []
        total_cost = Decimal("0")
        cost_by_category: Dict[str, Decimal] = {}
        missing_prices: List[str] = []

        for entry in entries:
            material_name = entry.name.lower()
            price = market_price_service.get_price(material_name, unit=entry.unit)

            if not price:
                missing_prices.append(entry.name)
                cost_entries.append(
                    WorkCostEntry(
                        name=entry.name,
                        quantity=entry.quantity,
                        unit=entry.unit,
                        cost=Decimal("0"),
                        material_price=None,
                        source_line=entry.source_line,
                        code=entry.code,
                        category=entry.category,
                        warnings=["Цена не найдена в справочнике."],
                    )
                )
                continue

            cost = entry.quantity * price.price_per_unit
            total_cost += cost

            category = entry.category or "Прочее"
            cost_by_category.setdefault(category, Decimal("0"))
            cost_by_category[category] += cost

            cost_entries.append(
                WorkCostEntry(
                    name=entry.name,
                    quantity=entry.quantity,
                    unit=entry.unit,
                    cost=cost,
                    material_price=price,
                    source_line=entry.source_line,
                    code=entry.code,
                    category=entry.category,
                )
            )

        summary = CostSummary(
            total_cost=total_cost,
            by_category=cost_by_category,
            missing_prices=missing_prices,
        )

        result = PreliminaryCostResult(
            entries=cost_entries,
            summary=summary,
            extraction=extraction or self._make_result_stub(entries),
        )
        return result

    def _make_result_stub(self, entries: List[WorkVolumeEntry]) -> WorkVolumeResult:
        totals: Dict[str, Decimal] = {}
        total_quantity = Decimal("0")
        for entry in entries:
            total_quantity += entry.quantity
            category = entry.category or "Прочее"
            totals.setdefault(category, Decimal("0"))
            totals[category] += entry.quantity

        summary = WorkVolumeSummary(totals=totals, total_quantity=total_quantity)
        return WorkVolumeResult(entries=entries, summary=summary, warnings=[])


preliminary_cost_service = PreliminaryCostService()

__all__ = ["PreliminaryCostService", "PreliminaryCostResult", "preliminary_cost_service"]


