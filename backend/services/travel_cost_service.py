"""
Расчёт командировочных расходов и затрат на СИЗ для F1.02.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class TravelCostResult:
    """Структурированное представление оценки командировочных затрат."""

    total_travel: Decimal
    tickets: Decimal
    lodging: Decimal
    per_diem: Decimal
    ppe: Decimal
    total_before_coeff: Decimal
    total_with_coeff: Decimal
    coefficient: float
    worker_count: int
    worker_days: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_travel": float(self.total_travel),
            "tickets": float(self.tickets),
            "lodging": float(self.lodging),
            "per_diem": float(self.per_diem),
            "ppe": float(self.ppe),
            "total_before_coeff": float(self.total_before_coeff),
            "total_with_coeff": float(self.total_with_coeff),
            "coefficient": self.coefficient,
            "worker_count": self.worker_count,
            "worker_days": self.worker_days,
        }


class TravelCostService:
    """
    Рассчитывает затраты на командировки и СИЗ.
    """

    TICKET_COST = Decimal("20000")  # в обе стороны
    LODGING_PER_DAY = Decimal("3200")
    PER_DIEM_PER_DAY = Decimal("1800")
    PPE_PER_WORKER = Decimal("12000")

    def estimate(
        self,
        labor_summary: Optional[Dict[str, Any]],
        metadata: Dict[str, Any],
    ) -> Optional[TravelCostResult]:
        """
        Рассчитывает ориентировочные затраты на командировки и СИЗ.

        Пояснения:
        - `labor_summary` передаётся из конвейера ТЭО и содержит оценку трудозатрат.
        - На основе общего эквивалента работников считаем необходимое количество людей.
        - Применяем фиксированные нормативы стоимости, чтобы обеспечить воспроизводимость расчётов.
        - Северные коэффициенты определяются по метаданным заявки (если присутствует зона).
        """
        if not labor_summary:
            return None

        worker_eq = float(labor_summary.get("total_worker_equivalent") or 0.0)
        worker_days = float(labor_summary.get("worker_days") or (worker_eq * 8))
        if worker_eq <= 0 or worker_days <= 0:
            return None

        worker_count = max(1, math.ceil(worker_eq))

        tickets = (self.TICKET_COST * Decimal(worker_count)).quantize(Decimal("0.01"))
        worker_days_decimal = Decimal(str(worker_days))
        lodging = (self.LODGING_PER_DAY * worker_days_decimal).quantize(Decimal("0.01"))
        per_diem = (self.PER_DIEM_PER_DAY * worker_days_decimal).quantize(Decimal("0.01"))
        ppe = (self.PPE_PER_WORKER * Decimal(worker_count)).quantize(Decimal("0.01"))

        total_travel = tickets + lodging + per_diem
        total_before_coeff = total_travel + ppe

        coefficient = self._determine_coefficient(metadata)
        total_with_coeff = (total_before_coeff * Decimal(str(coefficient))).quantize(Decimal("0.01"))

        total_travel = total_travel.quantize(Decimal("0.01"))
        total_before_coeff = total_before_coeff.quantize(Decimal("0.01"))

        return TravelCostResult(
            total_travel=total_travel,
            tickets=tickets,
            lodging=lodging,
            per_diem=per_diem,
            ppe=ppe,
            total_before_coeff=total_before_coeff,
            total_with_coeff=total_with_coeff,
            coefficient=coefficient,
            worker_count=worker_count,
            worker_days=worker_days,
        )

    def _determine_coefficient(self, metadata: Dict[str, Any]) -> float:
        """
        Возвращает коэффициент корректировки затрат для северных территорий.
        Логика простая: если в метаданных указана северная зона — применяем коэффициент 1.2.
        В дальнейшем коэффициенты можно расширить и хранить в настройках.
        """
        zone = (metadata.get("development_zone") or "").lower()
        rationale = (metadata.get("zone_check_rationale") or "").lower()
        if any(token in zone for token in ["север", "sever", "north"]) or any(
            token in rationale for token in ["север", "north"]
        ):
            return 1.2
        return 1.0


travel_cost_service = TravelCostService()

__all__ = ["travel_cost_service", "TravelCostService", "TravelCostResult"]


