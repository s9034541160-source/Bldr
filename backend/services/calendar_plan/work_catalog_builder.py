"""
Агрегатор работ для построения календарного плана на основе сметных данных.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, Iterable, List, Optional

from backend.services.calendar_plan.excel_estimate_parser import EstimateItem


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class WorkTask:
    """
    Базовая единица для календарного планирования.
    """

    code: Optional[str]
    name: str
    quantity: Optional[Decimal]
    unit: Optional[str]
    duration_days: Optional[float]
    start_date: Optional[str]
    finish_date: Optional[str]
    level: int
    parent_code: Optional[str]
    group_path: List[str]
    metadata: Dict[str, Any]


@dataclass(slots=True)
class WorkCatalog:
    """
    Итоговое представление списка работ.
    """

    tasks: List[WorkTask]
    totals: Dict[str, Any]
    warnings: List[str]


class WorkCatalogBuilder:
    """
    Преобразует результаты парсинга сметы в каталог работ, пригодный для календарного планирования.
    """

    def __init__(self, *, enable_parent_lookup: bool = True) -> None:
        self.enable_parent_lookup = enable_parent_lookup

    def build(self, items: Iterable[EstimateItem]) -> WorkCatalog:
        tasks: List[WorkTask] = []
        warnings: List[str] = []
        parent_stack: List[EstimateItem] = []
        name_stack: List[str] = []
        totals = {
            "count": 0,
            "sum_quantity": Decimal("0"),
            "with_duration": 0,
        }

        for entry in items:
            while parent_stack and parent_stack[-1].level >= entry.level:
                parent_stack.pop()
                if name_stack:
                    name_stack.pop()

            parent_code = parent_stack[-1].code if parent_stack else None
            group_path = list(name_stack)

            task = WorkTask(
                code=entry.code,
                name=entry.name,
                quantity=entry.quantity,
                unit=entry.unit,
                duration_days=entry.duration_days,
                start_date=entry.start_date.isoformat() if entry.start_date else None,
                finish_date=entry.finish_date.isoformat() if entry.finish_date else None,
                level=entry.level,
                parent_code=parent_code,
                group_path=group_path,
                metadata=entry.raw_row,
            )
            tasks.append(task)

            totals["count"] += 1
            if entry.quantity is not None:
                totals["sum_quantity"] += entry.quantity
            if entry.duration_days:
                totals["with_duration"] += 1

            parent_stack.append(entry)
            name_stack.append(entry.name)

        return WorkCatalog(tasks=tasks, totals=totals, warnings=warnings)


__all__ = ["WorkCatalogBuilder", "WorkCatalog", "WorkTask"]


