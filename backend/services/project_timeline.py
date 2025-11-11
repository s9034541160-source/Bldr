"""
Оценка сроков выполнения проекта на основе объёмов работ и данных Neo4j.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from statistics import mean
from typing import Dict, Iterable, List, Optional

from sqlalchemy.orm import Session

from backend.services.neo4j_service import neo4j_service
from backend.services.work_volume_extractor import WorkVolumeEntry

logger = logging.getLogger(__name__)


class ProjectTimelineEstimator:
    """
    Оценивает предполагаемый срок проекта, исходя из объёмов работ.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def estimate(self, entries: List[WorkVolumeEntry], metadata: Dict[str, object]) -> Dict[str, object]:
        if not entries:
            raise ValueError("Work volume entries are required for timeline estimation.")

        heuristic_duration = self._heuristic_duration(entries)
        similar_duration = self._query_similar_projects(entries, metadata)

        durations = [value for value in [heuristic_duration, similar_duration] if value is not None]
        duration_days = max(7, int(mean(durations))) if durations else heuristic_duration or 14

        start = self._determine_start_date(metadata)
        completion = start + timedelta(days=duration_days)

        confidence = 0.5
        if similar_duration:
            confidence += 0.3
        confidence = min(confidence, 0.95)

        return {
            "estimated_duration_days": duration_days,
            "estimated_start": start.isoformat(),
            "estimated_completion": completion.isoformat(),
            "basis": {
                "heuristic_days": heuristic_duration,
                "similar_projects_days": similar_duration,
            },
            "confidence": round(confidence, 2),
        }

    def _heuristic_duration(self, entries: List[WorkVolumeEntry]) -> int:
        total_quantity = sum(max(entry.quantity, 0) for entry in entries)
        unique_codes = len({entry.code for entry in entries if entry.code})
        base = len(entries) * 3
        quantity_factor = int(total_quantity // 50)
        code_factor = unique_codes * 2
        duration = base + quantity_factor + code_factor
        return max(duration, 10)

    def _query_similar_projects(self, entries: List[WorkVolumeEntry], metadata: Dict[str, object]) -> Optional[int]:
        if not neo4j_service:
            return None
        primary_category = self._dominant_category(entries)
        try:
            records = neo4j_service.execute_query(
                """
                MATCH (p:Project)
                WHERE exists(p.plannedDurationDays)
                OPTIONAL MATCH (p)-[:HAS_CATEGORY]->(c:Category)
                WITH p, c
                WHERE $category IS NULL OR c.name = $category
                RETURN p.plannedDurationDays AS duration
                ORDER BY p.createdAt DESC
                LIMIT 10
                """,
                {"category": primary_category},
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug("Neo4j timeline query failed: %s", exc)
            return None

        durations = [
            record.get("duration")
            for record in records or []
            if isinstance(record.get("duration"), (int, float))
        ]
        if not durations:
            return None
        return int(mean(durations))

    def _dominant_category(self, entries: List[WorkVolumeEntry]) -> Optional[str]:
        counts: Dict[str, int] = {}
        for entry in entries:
            category = entry.category or "Прочее"
            counts[category] = counts.get(category, 0) + 1
        if not counts:
            return None
        return max(counts.items(), key=lambda item: item[1])[0]

    def _determine_start_date(self, metadata: Dict[str, object]) -> date:
        for key in ("planned_start", "expected_start", "start_date"):
            value = metadata.get(key)
            if isinstance(value, str):
                try:
                    return datetime.fromisoformat(value).date()
                except ValueError:
                    continue
        return datetime.utcnow().date()


__all__ = ["ProjectTimelineEstimator"]


