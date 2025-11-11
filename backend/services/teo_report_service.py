"""
Генерация документов предварительного ТЭО.
"""

from __future__ import annotations

import logging
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, Optional

from docx import Document

from backend.models.project import Project

logger = logging.getLogger(__name__)


class TEOReportService:
    """
    Формирует DOCX-отчёт по предварительному ТЭО.
    """

    def build_preliminary_report(self, project: Project, analysis: Optional[Dict[str, Any]]) -> bytes:
        document = Document()

        document.add_heading("Предварительное ТЭО", level=1)
        document.add_paragraph(f"Проект: {project.name} ({project.code})")
        document.add_paragraph(f"Дата формирования: {datetime.utcnow():%d.%m.%Y %H:%M}")

        document.add_heading("Общая информация", level=2)
        table = document.add_table(rows=0, cols=2)
        rows = [
            ("UUID", project.uuid),
            ("Статус", project.status),
            ("Ожидаемое начало", project.expected_start or ""),
            ("Ожидаемое завершение", project.expected_completion or ""),
            ("Плановая длительность (дн.)", project.planned_duration_days or ""),
        ]
        for title, value in rows:
            cells = table.add_row().cells
            cells[0].text = str(title)
            cells[1].text = str(value)

        if analysis:
            work_volume = analysis.get("work_volume")
            if isinstance(work_volume, dict):
                document.add_heading("Объёмы работ", level=2)
                summary = work_volume.get("summary") or {}
                document.add_paragraph(f"Позиции: {summary.get('total_items', 0)}")
                document.add_paragraph(
                    f"Суммарный объём: {summary.get('total_quantity', 0)} {self._detect_unit(work_volume)}"
                )

            cost = analysis.get("cost")
            if isinstance(cost, dict):
                document.add_heading("Стоимость", level=2)
                document.add_paragraph(f"Предварительная стоимость: {cost.get('total_cost', 0):,.2f} руб.")
                missing = cost.get("missing_prices") or []
                if missing:
                    document.add_paragraph("Позиции без цены:", style="List Bullet")
                    for item in missing:
                        document.add_paragraph(str(item), style="List Bullet")

            timeline = analysis.get("timeline")
            if isinstance(timeline, dict):
                document.add_heading("Сроки", level=2)
                document.add_paragraph(f"Оценка длительности: {timeline.get('estimated_duration_days')} дн.")
                document.add_paragraph(f"Confidence: {timeline.get('confidence', 0)}")

        stream = BytesIO()
        document.save(stream)
        stream.seek(0)
        return stream.read()

    def _detect_unit(self, work_volume: Dict[str, Any]) -> str:
        entries = work_volume.get("entries") or []
        if entries:
            unit = entries[0].get("unit")
            if unit:
                return unit
        return ""


teo_report_service = TEOReportService()

__all__ = ["teo_report_service", "TEOReportService"]


