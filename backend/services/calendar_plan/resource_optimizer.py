"""
Оптимизация графика после базового выравнивания ресурсов.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Iterable, List

from backend.services.calendar_plan.cpm_builder import CPMResult
from backend.services.calendar_plan.resource_leveler import (
    LeveledTask,
    LevelingResult,
    ResourceLeveler,
)

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class OptimizationResult(LevelingResult):
    iterations: int = 0
    peak_load: float = 0.0


class ResourceOptimizer:
    """
    Выполняет несколько итераций корректировки сдвигов задач, чтобы уменьшить пиковую нагрузку.
    """

    def __init__(self, max_iterations: int = 3) -> None:
        self.leveler = ResourceLeveler()
        self.max_iterations = max_iterations

    def optimize(self, cpm_result: CPMResult) -> OptimizationResult:
        baseline = self.leveler.level(cpm_result)
        adjustments: Dict[str, float] = {
            task.task_id: task.shift for task in baseline.tasks if task.shift > 0
        }

        best_tasks = baseline.tasks
        best_profile = baseline.resource_profile
        best_peak = self._compute_peak(best_profile)

        slack_map = {node_id: node.slack for node_id, node in cpm_result.nodes.items()}

        for iteration in range(self.max_iterations):
            improved = False
            for task_id in adjustments.keys():
                slack = slack_map.get(task_id, 0.0)
                if slack <= 0:
                    continue
                candidates = self._candidate_shifts(slack)
                best_local_shift = adjustments[task_id]
                local_best_peak = best_peak
                for shift in candidates:
                    adjustments[task_id] = shift
                    leveled = self._build_schedule(cpm_result, adjustments)
                    peak = self._compute_peak(leveled.resource_profile)
                    if peak < local_best_peak - 1e-6:
                        local_best_peak = peak
                        best_local_shift = shift
                        best_tasks = leveled.tasks
                        best_profile = leveled.resource_profile
                if abs(best_local_shift - adjustments[task_id]) > 1e-6:
                    adjustments[task_id] = best_local_shift
                    best_peak = local_best_peak
                    improved = True
            if not improved:
                break

        return OptimizationResult(
            tasks=best_tasks,
            resource_profile=best_profile,
            iterations=iteration + 1,
            peak_load=best_peak,
        )

    def _build_schedule(
        self,
        cpm_result: CPMResult,
        adjustments: Dict[str, float],
    ) -> LevelingResult:
        tasks: List[LeveledTask] = []
        profile: Dict[float, float] = {}

        for node_id, node in cpm_result.nodes.items():
            shift = min(max(adjustments.get(node_id, 0.0), 0.0), node.slack)
            start = node.early_start + shift
            finish = node.early_finish + shift
            leveled_task = LeveledTask(
                task_id=node_id,
                task=node.task,
                new_early_start=start,
                new_early_finish=finish,
                shift=shift,
            )
            tasks.append(leveled_task)
            self._apply_to_profile(profile, start, finish, node.task)

        return LevelingResult(tasks=tasks, resource_profile=profile)

    @staticmethod
    def _compute_peak(profile: Dict[float, float]) -> float:
        return max(profile.values()) if profile else 0.0

    @staticmethod
    def _candidate_shifts(slack: float) -> Iterable[float]:
        if slack <= 0:
            return [0.0]
        steps = max(2, min(5, int(slack) + 1))
        increment = slack / (steps - 1)
        return [round(increment * i, 3) for i in range(steps)]

    @staticmethod
    def _apply_to_profile(profile: Dict[float, float], start: float, finish: float, task) -> None:
        duration = finish - start
        if duration <= 0:
            return
        resources = task.metadata.get("resources", [])
        labor_hours = 0.0
        for resource in resources:
            resource_type = str(resource.get("type") or resource.get("group") or "").lower()
            if resource_type not in {"labor", "рабочие"}:
                continue
            try:
                labor_hours += float(resource.get("hours_total") or 0.0)
            except (TypeError, ValueError):
                continue
        if labor_hours <= 0:
            return
        hourly_load = labor_hours / duration
        time_point = start
        while time_point < finish:
            profile[time_point] = profile.get(time_point, 0.0) + hourly_load
            time_point += 1.0


__all__ = ["ResourceOptimizer", "OptimizationResult"]


