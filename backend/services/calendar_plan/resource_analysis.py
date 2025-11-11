"""
Анализ загрузки ресурсов по результатам CPM.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from backend.services.calendar_plan.cpm_builder import CPMResult

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ResourceGroupSummary:
    """
    Сводная информация по одной группе ресурсов.
    """

    group: str
    planned_hours: float
    tasks: List[str]


@dataclass(slots=True)
class ResourceAnalysis:
    """
    Итог анализа ресурсов на основе CPM.
    """

    groups: List[ResourceGroupSummary]
    critical_tasks: List[str]


class ResourceLoadAnalyzer:
    """
    Разбирает ресурсы в CPM-узлах и агрегирует плановые объёмы.
    """

    def analyze(self, cpm_result: CPMResult) -> ResourceAnalysis:
        groups_map: Dict[str, ResourceGroupSummary] = {}
        critical_tasks: List[str] = []

        for node_id, node in cpm_result.nodes.items():
            resources = node.task.metadata.get("resources") or []
            if node.critical:
                critical_tasks.append(node_id)
            for resource in resources:
                group = str(resource.get("group") or resource.get("type") or "other").strip().lower()
                hours = self._extract_hours(resource)
                if group not in groups_map:
                    groups_map[group] = ResourceGroupSummary(group=group, planned_hours=0.0, tasks=[])
                groups_map[group].planned_hours += hours
                groups_map[group].tasks.append(node_id)

        groups = sorted(groups_map.values(), key=lambda item: item.group)
        return ResourceAnalysis(groups=groups, critical_tasks=critical_tasks)

    @staticmethod
    def _extract_hours(resource: Dict[str, object]) -> float:
        value = resource.get("hours_total") or resource.get("planned_hours") or 0.0
        try:
            return max(0.0, float(value))
        except (TypeError, ValueError):
            return 0.0


__all__ = ["ResourceLoadAnalyzer", "ResourceAnalysis", "ResourceGroupSummary"]


