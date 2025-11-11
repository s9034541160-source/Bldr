"""
Финансовый анализ для предварительного ТЭО.

Задачи:
- Расчёт NPV и IRR на основе прогнозных денежных потоков.
- Оценка срока окупаемости.
- Формирование простого профиля рисков.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

import numpy_financial as npf  # type: ignore

from backend.config.settings import settings


@dataclass(slots=True)
class FinancialInputs:
    """Нормализованные входы для финансового расчёта."""

    initial_investment: Decimal
    construction_months: int
    operation_months: int
    monthly_revenue: Decimal
    monthly_operating_cost: Decimal
    discount_rate_annual: float


class FinancialAnalysisService:
    """
    Комплексный модуль расчёта финансовых показателей.
    """

    def evaluate(
        self,
        *,
        cost_summary: Dict[str, Any],
        timeline: Optional[Dict[str, Any]],
        travel_summary: Optional[Dict[str, Any]],
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Основная точка входа.

        Ожидает на вход:
        - `cost_summary`: результат PreliminaryCostService.summary.
        - `timeline`: блок анализа сроков (если доступен).
        - `travel_summary`: рассчитанные командировочные / СИЗ.
        - `metadata`: исходные метаданные заявки/проекта.
        """
        inputs = self._prepare_inputs(cost_summary, timeline, travel_summary, metadata)
        cashflow = self._build_cashflow(inputs)
        npv_value = self._calculate_npv(inputs, cashflow)
        irr_value = self._calculate_irr(cashflow)
        payback = self._calculate_payback(cashflow)
        risk_profile = self._assess_risk(metadata, cost_summary, travel_summary, inputs)

        return {
            "npv": npv_value,
            "irr_percent": irr_value * 100 if irr_value is not None else None,
            "payback_months": payback,
            "cashflow": {
                "periods": cashflow,
                "construction_months": inputs.construction_months,
                "operation_months": inputs.operation_months,
                "monthly_revenue": float(inputs.monthly_revenue),
                "monthly_operating_cost": float(inputs.monthly_operating_cost),
            },
            "assumptions": {
                "initial_investment": float(inputs.initial_investment),
                "discount_rate_annual": inputs.discount_rate_annual,
                "discount_rate_monthly": self._monthly_rate(inputs.discount_rate_annual),
            },
            "risk": risk_profile,
        }

    def _prepare_inputs(
        self,
        cost_summary: Dict[str, Any],
        timeline: Optional[Dict[str, Any]],
        travel_summary: Optional[Dict[str, Any]],
        metadata: Dict[str, Any],
    ) -> FinancialInputs:
        # 1. Инвестиции = сметная стоимость + командировочные (если есть)
        initial_investment = self._to_decimal(cost_summary.get("grand_total") or cost_summary.get("total_cost") or 0)
        if travel_summary:
            initial_investment += self._to_decimal(travel_summary.get("total_with_coeff", 0))

        financial_meta: Dict[str, Any] = {}
        for key in ("financial_plan", "financial", "analysis_financial"):
            candidate = metadata.get(key)
            if isinstance(candidate, dict):
                financial_meta = candidate
                break

        # 2. Длительность строительства
        construction_days = 0
        if timeline:
            try:
                construction_days = float(timeline.get("estimated_duration_days") or 0)
            except (TypeError, ValueError):
                construction_days = 0
        construction_months = max(1, math.ceil(construction_days / 30)) if construction_days else 3

        # 3. Горизонт эксплуатации
        operation_months = int(
            financial_meta.get("operation_months") or settings.FINANCIAL_OPERATION_PERIOD_MONTHS
        )
        operation_months = max(operation_months, 1)

        # 4. Денежный поток
        monthly_revenue = financial_meta.get("monthly_revenue")
        monthly_operating_cost = financial_meta.get("monthly_operating_cost")

        default_margin_rate = settings.FINANCIAL_DEFAULT_MARGIN_RATE
        default_operating_rate = settings.FINANCIAL_DEFAULT_OPERATING_COST_RATE

        if monthly_revenue is None:
            revenue_base = initial_investment * Decimal(default_margin_rate)
            monthly_revenue = revenue_base / Decimal(operation_months)
        else:
            monthly_revenue = self._to_decimal(monthly_revenue)

        if monthly_operating_cost is None:
            monthly_operating_cost = initial_investment * Decimal(default_operating_rate) / Decimal(operation_months)
        else:
            monthly_operating_cost = self._to_decimal(monthly_operating_cost)

        # 5. Ставка дисконтирования
        discount_rate_annual = float(
            financial_meta.get("discount_rate") or settings.FINANCIAL_DISCOUNT_RATE
        )

        return FinancialInputs(
            initial_investment=initial_investment.quantize(Decimal("0.01")),
            construction_months=construction_months,
            operation_months=operation_months,
            monthly_revenue=monthly_revenue.quantize(Decimal("0.01")),
            monthly_operating_cost=monthly_operating_cost.quantize(Decimal("0.01")),
            discount_rate_annual=discount_rate_annual,
        )

    def _build_cashflow(self, inputs: FinancialInputs) -> List[float]:
        net_cash = float(inputs.monthly_revenue - inputs.monthly_operating_cost)
        construction_period = [0.0] * inputs.construction_months
        operation_period = [net_cash] * inputs.operation_months
        return [-float(inputs.initial_investment)] + construction_period + operation_period

    def _calculate_npv(self, inputs: FinancialInputs, cashflow: List[float]) -> float:
        rate = self._monthly_rate(inputs.discount_rate_annual)
        return float(npf.npv(rate, cashflow))

    def _calculate_irr(self, cashflow: List[float]) -> Optional[float]:
        try:
            result = float(npf.irr(cashflow))
        except (ZeroDivisionError, ValueError, OverflowError):
            return None
        if math.isnan(result):
            return None
        return result

    def _calculate_payback(self, cashflow: List[float]) -> Optional[int]:
        cumulative = 0.0
        for idx, value in enumerate(cashflow):
            cumulative += value
            if cumulative >= 0:
                return idx
        return None

    def _assess_risk(
        self,
        metadata: Dict[str, Any],
        cost_summary: Dict[str, Any],
        travel_summary: Optional[Dict[str, Any]],
        inputs: FinancialInputs,
    ) -> Dict[str, Any]:
        score = 40.0
        factors: List[str] = []

        zone_allowed = metadata.get("zone_check_allowed")
        if zone_allowed is False:
            score += 25
            factors.append("Локация в запрещённой зоне развития.")

        if cost_summary.get("missing_prices"):
            score += 10
            factors.append("Не найдены цены для части материалов.")

        if travel_summary and travel_summary.get("coefficient", 1.0) > 1.0:
            score += 5
            factors.append("Повышающие коэффициенты для северных регионов.")

        if inputs.operation_months < 12:
            score += 5
            factors.append("Короткий горизонт эксплуатации.")

        factors = factors or ["Существенных рисков не выявлено."]
        score = min(100.0, score)
        level = "low"
        if score >= 70:
            level = "high"
        elif score >= 50:
            level = "medium"

        return {
            "score": score,
            "level": level,
            "factors": factors,
        }

    @staticmethod
    def _monthly_rate(annual_rate: float) -> float:
        return math.pow(1 + annual_rate, 1 / 12) - 1

    @staticmethod
    def _to_decimal(value: Any) -> Decimal:
        if isinstance(value, Decimal):
            return value
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            return Decimal("0")


financial_analysis_service = FinancialAnalysisService()

__all__ = ["financial_analysis_service", "FinancialAnalysisService"]


