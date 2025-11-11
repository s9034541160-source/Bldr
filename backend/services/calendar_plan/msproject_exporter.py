"""
Экспорт сетевого графика в формат Microsoft Project (MSPDI XML).
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Iterable, Optional
from xml.etree.ElementTree import Element, ElementTree, SubElement

import networkx as nx

from backend.services.calendar_plan.cpm_builder import CPMResult
from backend.services.calendar_plan.resource_leveler import LevelingResult

MSP_NAMESPACE = "http://schemas.microsoft.com/project"


class MSProjectExporter:
    """
    Формирует XML-файл, совместимый с MS Project (MSPDI schema).
    Использует ранние даты из CPM. При наличии результатов выравнивания берет смещенные даты.
    """

    def __init__(self, *, base_date: Optional[dt.date] = None, hours_per_day: int = 8) -> None:
        self.base_date = base_date or dt.date.today()
        self.hours_per_day = hours_per_day

    def export(
        self,
        cpm_result: CPMResult,
        output_path: str | Path,
        *,
        leveled: Optional[LevelingResult] = None,
        project_name: str = "BLDR Calendar Plan",
    ) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        project = Element("Project", xmlns=MSP_NAMESPACE)
        SubElement(project, "Name").text = project_name
        SubElement(project, "CreationDate").text = self._format_datetime(dt.datetime.utcnow())
        SubElement(project, "StartDate").text = self._format_datetime(self._calc_datetime(0.0))
        SubElement(project, "FinishDate").text = self._format_datetime(
            self._calc_datetime(cpm_result.project_duration)
        )

        tasks_el = SubElement(project, "Tasks")
        leveled_map = {task.task_id: task for task in leveled.tasks} if leveled else {}

        ordered_nodes = list(self._topological_order(cpm_result))
        uid_map: dict[str, int] = {}

        for index, node_id in enumerate(ordered_nodes, start=1):
            node = cpm_result.nodes[node_id]
            uid_map[node_id] = index
            leveled_task = leveled_map.get(node_id)
            start = leveled_task.new_early_start if leveled_task else node.early_start
            finish = leveled_task.new_early_finish if leveled_task else node.early_finish
            duration_days = max(finish - start, 0.0)

            task_el = SubElement(tasks_el, "Task")
            SubElement(task_el, "UID").text = str(index)
            SubElement(task_el, "ID").text = str(index)
            SubElement(task_el, "Name").text = node.task.name
            SubElement(task_el, "Type").text = "1"  # Fixed Duration
            SubElement(task_el, "IsNull").text = "0"
            SubElement(task_el, "WBS").text = node.task.code or f"T{index:04d}"
            SubElement(task_el, "OutlineLevel").text = str(node.task.level + 1)
            SubElement(task_el, "DurationFormat").text = "39"
            SubElement(task_el, "Critical").text = "1" if node.critical else "0"
            SubElement(task_el, "Duration").text = self._format_duration(duration_days)
            SubElement(task_el, "Start").text = self._format_datetime(self._calc_datetime(start))
            SubElement(task_el, "Finish").text = self._format_datetime(self._calc_datetime(finish))
            SubElement(task_el, "EarlyStart").text = self._format_datetime(self._calc_datetime(node.early_start))
            SubElement(task_el, "EarlyFinish").text = self._format_datetime(self._calc_datetime(node.early_finish))
            SubElement(task_el, "LateStart").text = self._format_datetime(self._calc_datetime(node.late_start))
            SubElement(task_el, "LateFinish").text = self._format_datetime(self._calc_datetime(node.late_finish))
            SubElement(task_el, "TotalSlack").text = str(int(round(node.slack * self.hours_per_day * 60)))

            for pred in cpm_result.graph.predecessors(node_id):
                link_el = SubElement(task_el, "PredecessorLink")
                SubElement(link_el, "PredecessorUID").text = str(uid_map[pred])
                SubElement(link_el, "Type").text = "1"  # Finish-to-Start
                SubElement(link_el, "LinkLag").text = "0"
                SubElement(link_el, "LagFormat").text = "7"

        assignments_el = SubElement(project, "Assignments")
        for node in ordered_nodes:
            task = cpm_result.nodes[node].task
            resources = task.metadata.get("resources") or []
            for res_idx, resource in enumerate(resources, start=1):
                assignment = SubElement(assignments_el, "Assignment")
                SubElement(assignment, "UID").text = f"{uid_map[node]}{res_idx}"
                SubElement(assignment, "TaskUID").text = str(uid_map[node])
                SubElement(assignment, "ResourceUID").text = str(res_idx)
                SubElement(assignment, "Units").text = "1"

        ElementTree(project).write(path, encoding="utf-8", xml_declaration=True)
        return path

    def _calc_datetime(self, project_days: float) -> dt.datetime:
        return dt.datetime.combine(self.base_date, dt.time.min) + dt.timedelta(days=project_days)

    @staticmethod
    def _format_datetime(value: dt.datetime) -> str:
        return value.strftime("%Y-%m-%dT%H:%M:%S")

    def _format_duration(self, duration_days: float) -> str:
        hours = duration_days * self.hours_per_day
        return f"PT{int(round(hours))}H0M0S"

    @staticmethod
    def _topological_order(cpm_result: CPMResult) -> Iterable[str]:
        return list(nx.topological_sort(cpm_result.graph))


__all__ = ["MSProjectExporter"]


