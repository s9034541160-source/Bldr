"""
Высокоуровневый анализ CPM-результатов:
возвращает критический путь, продолжительность проекта и подробности узлов.
"""

from __future__ import annotations

from typing import Any, Dict, List

from backend.services.calendar_plan.cpm_builder import CPMBuilder, CPMResult
from backend.services.calendar_plan.dependency_builder import DependencyGraph
from backend.services.calendar_plan.work_catalog_builder import WorkCatalog


class CPMAnalyzer:
    """
    Фасад над CPMBuilder, который подготавливает удобный для API вывод.
    """

    def __init__(self) -> None:
        self._builder = CPMBuilder()

    def analyze(self, catalog: WorkCatalog, dependencies: DependencyGraph) -> Dict[str, Any]:
        result = self._builder.build(catalog, dependencies)
        return self._serialize(result)

    def _serialize(self, result: CPMResult) -> Dict[str, Any]:
        nodes_payload: List[Dict[str, Any]] = []
        slack_total = 0.0
        slack_nonzero = 0
        critical_count = 0
        for node_id, node in result.nodes.items():
            slack_total += node.slack
            if node.critical:
                critical_count += 1
            elif node.slack > 0:
                slack_nonzero += 1
            nodes_payload.append(
                {
                    "id": node_id,
                    "name": node.task.name,
                    "code": node.task.code,
                    "level": node.task.level,
                    "duration_days": node.task.duration_days,
                    "early_start": node.early_start,
                    "early_finish": node.early_finish,
                    "late_start": node.late_start,
                    "late_finish": node.late_finish,
                    "slack": node.slack,
                    "critical": node.critical,
                }
            )
        return {
            "critical_path": result.critical_path,
            "project_duration_days": result.project_duration,
            "nodes": nodes_payload,
            "slack_summary": {
                "total_slack": slack_total,
                "critical_tasks": critical_count,
                "tasks_with_slack": slack_nonzero,
                "total_tasks": len(nodes_payload),
            },
        }


__all__ = ["CPMAnalyzer"]


