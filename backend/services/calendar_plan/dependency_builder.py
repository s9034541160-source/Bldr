"""
Формирование зависимостей между работами для календарного планирования.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from backend.services.calendar_plan.work_catalog_builder import WorkCatalog, WorkTask

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class DependencyEdge:
    """
    Ребро графа зависимостей.
    """

    predecessor_id: str
    successor_id: str
    relation: str = "FS"  # Finish-to-Start
    rationale: str = ""


@dataclass(slots=True)
class ScheduledTask:
    """
    Узел графа зависимостей.
    """

    task_id: str
    task: WorkTask
    predecessors: List[str] = field(default_factory=list)


@dataclass(slots=True)
class DependencyGraph:
    """
    Результирующий граф зависимостей.
    """

    tasks: List[ScheduledTask]
    edges: List[DependencyEdge]
    warnings: List[str]


class CalendarDependencyBuilder:
    """
    Создаёт граф зависимостей, используя иерархию и порядок работ.
    """

    def build(self, catalog: WorkCatalog) -> DependencyGraph:
        if not catalog.tasks:
            return DependencyGraph(tasks=[], edges=[], warnings=["Каталог работ пуст."])

        id_map: Dict[WorkTask, str] = {}
        edges: List[DependencyEdge] = []
        scheduled: List[ScheduledTask] = []
        warnings: List[str] = []
        last_by_level: Dict[int, WorkTask] = {}
        seen_ids: Dict[str, WorkTask] = {}

        def assign_id(task: WorkTask, index: int) -> str:
            base_id = (task.code or "").strip()
            if not base_id:
                base_id = f"T{index:04d}"
            if base_id not in seen_ids:
                seen_ids[base_id] = task
                return base_id
            suffix = 1
            while f"{base_id}_{suffix}" in seen_ids:
                suffix += 1
            final_id = f"{base_id}_{suffix}"
            seen_ids[final_id] = task
            warnings.append(
                f"Дубликат кода '{task.code}' обнаружен, назначен идентификатор {final_id}."
            )
            return final_id

        for idx, task in enumerate(catalog.tasks, start=1):
            task_id = assign_id(task, idx)
            id_map[task] = task_id

            predecessors: List[str] = []

            parent_candidate = self._find_parent(task, last_by_level)
            if parent_candidate:
                parent_id = id_map[parent_candidate]
                predecessors.append(parent_id)
                edges.append(
                    DependencyEdge(
                        predecessor_id=parent_id,
                        successor_id=task_id,
                        relation="FS",
                        rationale="Иерархический родитель",
                    )
                )

            same_level_prev = last_by_level.get(task.level)
            if same_level_prev and same_level_prev is not parent_candidate:
                predecessor_id = id_map[same_level_prev]
                predecessors.append(predecessor_id)
                edges.append(
                    DependencyEdge(
                        predecessor_id=predecessor_id,
                        successor_id=task_id,
                        relation="FS",
                        rationale="Последовательность работ на том же уровне",
                    )
                )

            scheduled.append(ScheduledTask(task_id=task_id, task=task, predecessors=predecessors))
            last_by_level[task.level] = task
            self._update_higher_levels(last_by_level, task.level)

        return DependencyGraph(tasks=scheduled, edges=edges, warnings=warnings)

    @staticmethod
    def _find_parent(task: WorkTask, stack: Dict[int, WorkTask]) -> Optional[WorkTask]:
        if not stack:
            return None
        parent_level = task.level - 1
        if parent_level < 0:
            return None
        return stack.get(parent_level)

    @staticmethod
    def _update_higher_levels(stack: Dict[int, WorkTask], current_level: int) -> None:
        to_delete = [level for level in stack.keys() if level > current_level]
        for level in to_delete:
            stack.pop(level, None)


__all__ = ["CalendarDependencyBuilder", "DependencyGraph", "DependencyEdge", "ScheduledTask"]


