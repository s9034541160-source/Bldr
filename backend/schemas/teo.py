"""
Pydantic схемы для эндпоинтов предварительного ТЭО.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel, Field


class TEORequestSchema(BaseModel):
    """Параметры запуска конвейера ТЭО."""

    file_path: str = Field(..., description="Путь к документу с исходными данными.")
    top_k: int = Field(5, ge=1, le=10, description="Количество кандидатов ГЭСН для передачи в LLM.")


class WorkVolumeSchema(BaseModel):
    """Описание позиции ведомости объёмов работ."""

    name: str
    quantity: Decimal
    unit: str
    source_line: str
    code: Optional[str] = None
    category: Optional[str] = None


class MatchedNormSchema(BaseModel):
    """Результат сопоставления позиции и нормы ГЭСН."""

    volume: WorkVolumeSchema
    norm_code: str
    reasoning: str
    candidate_scores: Dict[str, float]


class CostEntrySchema(BaseModel):
    """Сметная запись."""

    name: str
    quantity: Decimal
    unit: str
    cost: Decimal
    material_price: Optional[Dict[str, Decimal]] = Field(
        None,
        description="Информация о цене материалов (если найдена).",
    )
    warnings: List[str] = []


class CostSummarySchema(BaseModel):
    """Сводка по стоимости."""

    total_cost: Decimal
    by_category: Dict[str, Decimal]
    missing_prices: List[str]


class LaborEntrySchema(BaseModel):
    """Позиция трудозатрат."""

    volume_name: str
    norm_code: str
    labor_hours: float
    worker_equivalent: float
    resources: List[Dict[str, Any]] = []


class LaborSummarySchema(BaseModel):
    """Итог по трудозатратам."""

    total_labor_hours: float
    total_worker_equivalent: float
    worker_days: float
    schedules: Dict[str, Dict[str, float]]
    entries: List[LaborEntrySchema]


class TravelSummarySchema(BaseModel):
    """Командировочные и СИЗ."""

    total_travel: float
    tickets: float
    lodging: float
    per_diem: float
    ppe: float
    total_before_coeff: float
    total_with_coeff: float
    coefficient: float
    worker_count: int
    worker_days: float


class FinancialRiskSchema(BaseModel):
    """Риск-профиль."""

    score: float
    level: str
    factors: List[str]


class FinancialSummarySchema(BaseModel):
    """Финансовые метрики проекта."""

    npv: float
    irr_percent: Optional[float]
    payback_months: Optional[int]
    assumptions: Dict[str, float]
    risk: FinancialRiskSchema


class TEOResponseSchema(BaseModel):
    """Итоговый ответ конвейера предварительного ТЭО."""

    warnings: List[str]
    volumes: List[WorkVolumeSchema]
    matches: List[MatchedNormSchema]
    cost_entries: List[CostEntrySchema]
    cost_summary: CostSummarySchema
    labor_summary: Optional[LaborSummarySchema] = None
    travel_summary: Optional[TravelSummarySchema] = None
    financial_summary: Optional[FinancialSummarySchema] = None


class TEOApprovalDecisionSchema(BaseModel):
    """Запрос на фиксацию решения по согласованию ТЭО."""

    role: str
    decision: Literal["approved", "rejected"]
    actor: Optional[str] = None
    comment: Optional[str] = None


class TEOApprovalStatusSchema(BaseModel):
    """Статус согласования ТЭО."""

    status: str
    route: List[Dict[str, Any]]
    history: List[Dict[str, Any]]


