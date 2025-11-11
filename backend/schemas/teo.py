"""
Pydantic схемы для эндпоинтов предварительного ТЭО.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Dict, List, Optional

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


class TEOResponseSchema(BaseModel):
    """Итоговый ответ конвейера предварительного ТЭО."""

    warnings: List[str]
    volumes: List[WorkVolumeSchema]
    matches: List[MatchedNormSchema]
    cost_entries: List[CostEntrySchema]
    cost_summary: CostSummarySchema


