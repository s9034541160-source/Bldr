"""
Экспорт календарного плана в PNG-диаграмму Ганта.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Optional

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator

from backend.services.calendar_plan.cpm_builder import CPMResult
from backend.services.calendar_plan.resource_leveler import LevelingResult


class GanttPNGExporter:
    """
    Строит диаграмму Ганта в PNG.

    Использует скорректированные даты (после выравнивания), если они переданы.
    """

    def __init__(self, *, base_date: Optional[dt.date] = None) -> None:
        self.base_date = base_date or dt.date.today()

    def export(
        self,
        cpm_result: CPMResult,
        output_path: str | Path,
        *,
        leveled: Optional[LevelingResult] = None,
        title: str = "BLDR Calendar Plan",
    ) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        leveled_map = {task.task_id: task for task in (leveled.tasks if leveled else [])}
        tasks = list(cpm_result.graph.nodes)
        fig, ax = plt.subplots(figsize=(14, max(6, len(tasks) * 0.4)))

        y_positions = range(len(tasks))
        yticks = []
        ylabels = []

        for idx, node_id in enumerate(tasks):
            node = cpm_result.nodes[node_id]
            leveled_task = leveled_map.get(node_id)
            start = leveled_task.new_early_start if leveled_task else node.early_start
            finish = leveled_task.new_early_finish if leveled_task else node.early_finish
            start_dt = self._calc_datetime(start)
            duration = finish - start
            color = "#1f77b4" if node.critical else "#7fb3d5"
            edge_color = "#0b3c68" if node.critical else "#336b87"

            ax.barh(
                idx,
                width=duration,
                left=start_dt,
                height=0.35,
                align="center",
                color=color,
                edgecolor=edge_color,
            )

            ax.text(
                start_dt + dt.timedelta(days=duration / 2),
                idx,
                node.task.name,
                ha="center",
                va="center",
                fontsize=8,
                color="white" if node.critical else "black",
            )

            yticks.append(idx)
            ylabels.append(node.task.code or node_id)

        ax.set_yticks(list(yticks))
        ax.set_yticklabels(ylabels, fontsize=8)
        ax.set_xlabel("Дата")
        ax.set_title(title, fontsize=12, fontweight="bold")

        start_xlim = self._calc_datetime(0)
        end_xlim = self._calc_datetime(cpm_result.project_duration + 1)
        ax.set_xlim(start_xlim, end_xlim)

        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, int(cpm_result.project_duration // 15) or 1)))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
        ax.xaxis.set_minor_locator(AutoMinorLocator())
        fig.autofmt_xdate(rotation=45)
        ax.invert_yaxis()
        ax.grid(axis="x", linestyle="--", alpha=0.3)
        ax.grid(axis="y", linestyle="--", alpha=0.1)

        plt.tight_layout()
        fig.savefig(path, dpi=200)
        plt.close(fig)
        return path

    def _calc_datetime(self, project_days: float) -> dt.datetime:
        return dt.datetime.combine(self.base_date, dt.time.min) + dt.timedelta(days=project_days)


__all__ = ["GanttPNGExporter"]


