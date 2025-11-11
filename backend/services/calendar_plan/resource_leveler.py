""
"Выравнивание ресурсоёмкости графика (грубый алгоритм).
""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List

from backend.services.calendar_plan.cpm_builder import CPMResult
from backend.services.calendar_plan.work_catalog_builder import WorkTask

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class LeveledTask:
    task_id: str
    task: WorkTask
    new_early_start: float
    new_early_finish: float
    shift: float


@dataclass(slots=True)
class LevelingResult:
    tasks: List[LeveledTask]
    resource_profile: Dict[float, float]


class ResourceLeveler:
    """
    Простейший ресурсный левелинг, который пытается распределить задачи в пределах их запаса времени.
    """

    def level(self, cpm_result: CPMResult) -> LevelingResult:
        leveled: List[LeveledTask] = []
        profile: Dict[float, float] = {}

        for node_id, node in cpm_result.nodes.items():
            if node.critical or node.slack <= 0:
                leveled.append(
                    LeveledTask(
                        task_id=node_id,
                        task=node.task,
                        new_early_start=node.early_start,
                        new_early_finish=node.early_finish,
                        shift=0.0,
                    )
                )
                self._apply_to_profile(profile, node.early_start, node.early_finish, node.task)
                continue

            shift = min(node.slack / 2.0, 2.0)
            new_start = node.early_start + shift
            new_finish = node.early_finish + shift
            leveled.append(
                LeveledTask(
                    task_id=node_id,
                    task=node.task,
                    new_early_start=new_start,
                    new_early_finish=new_finish,
                    shift=shift,
                )
            )
            self._apply_to_profile(profile, new_start, new_finish, node.task)

        return LevelingResult(tasks=leveled, resource_profile=profile)

    @staticmethod
    def _apply_to_profile(profile: Dict[float, float], start: float, finish: float, task: WorkTask) -> None:
        duration = finish - start
        if duration <= 0:
            return
        labor_resources = [
            resource for resource in task.metadata.get("resources", [])
            if str(resource.get("type", "")).lower() in {"labor", "рабочие"}
        ]
        labor_hours = sum(
            float(resource.get("hours_total") or 0.0)
            for resource in labor_resources
        )
        if labor_hours <= 0:
            return
        hourly_load = labor_hours / duration
        time_point = start
        while time_point < finish:
            profile[time_point] = profile.get(time_point, 0.0) + hourly_load
            time_point += 1.0


__all__ = ["ResourceLeveler", "LeveledTask", "LevelingResult"]


