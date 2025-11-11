"""
Конвейер предварительного ТЭО:
1. Извлекает ведомость объёмов.
2. Подбирает кандидатов ГЭСН и подтверждает их через LLM.
3. Считает предварительную стоимость.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from backend.models import SessionLocal
from backend.models.gesn import GESNNorm
from backend.services.gesn_retrieval import GESNRetrievalService, RetrievalCandidate
from backend.services.gesn_verification import GESNVerificationService, VerificationRequest, VerificationResult
from backend.services.preliminary_cost_service import PreliminaryCostResult, PreliminaryCostService
from backend.services.work_volume_extractor import WorkVolumeEntry, WorkVolumeResult, work_volume_extractor

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class MatchedNorm:
    """Связка между позицией объёма и утверждённой нормой."""

    volume: WorkVolumeEntry
    norm_code: str
    reasoning: str
    candidate_scores: Dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class LaborEntry:
    volume_name: str
    norm_code: str
    labor_hours: float
    worker_equivalent: float
    resources: List[Dict[str, float]] = field(default_factory=list)


@dataclass(slots=True)
class LaborSummary:
    entries: List[LaborEntry]
    total_labor_hours: float
    total_worker_equivalent: float
    worker_days: float
    schedules: Dict[str, Dict[str, float]]


@dataclass(slots=True)
class PipelineResult:
    """Комплексный итог работы конвейера."""

    volumes: List[WorkVolumeEntry]
    matches: List[MatchedNorm]
    cost: PreliminaryCostResult
    extraction: WorkVolumeResult
    labor: Optional[LaborSummary]
    warnings: List[str] = field(default_factory=list)


class PreliminaryTEOPipeline:
    """Основной класс конвейера предварительного ТЭО."""

    def __init__(self, session: Optional[Session] = None) -> None:
        self._session = session
        self._cost_service = PreliminaryCostService()
        self._verification_service = GESNVerificationService()

    @property
    def session(self) -> Session:
        """
        Возвращает активную сессию БД, создавая новую при необходимости.
        """
        if self._session is None:
            self._session = SessionLocal()
        return self._session

    def process_file(self, file_path: str, *, top_k: int = 5) -> PipelineResult:
        """
        Полный цикл обработки по файлу.
        """
        extraction = work_volume_extractor.extract_from_file(file_path)
        return self.process_entries(extraction.entries, extraction=extraction, top_k=top_k)

    def process_entries(
        self,
        entries: List[WorkVolumeEntry],
        *,
        extraction: Optional[WorkVolumeResult] = None,
        top_k: int = 5,
    ) -> PipelineResult:
        """
        Обработка заранее подготовленного списка объёмов.
        """
        retrieval_service = GESNRetrievalService(self.session)

        matches: List[MatchedNorm] = []
        warnings: List[str] = []

        for entry in entries:
            candidates = self._retrieve_candidates(retrieval_service, entry, top_k=top_k)
            if not candidates:
                warnings.append(f"Не найдено ни одного кандидата ГЭСН для: {entry.name}")
                continue

            try:
                verification = self._verify(entry, candidates)
                matches.append(
                    MatchedNorm(
                        volume=entry,
                        norm_code=verification.norm_code,
                        reasoning=verification.reasoning,
                        candidate_scores={cand.norm.code: cand.total_score for cand in candidates},
                    )
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Не удалось подтвердить кандидатов через LLM: %s", exc)
                best_candidate = max(candidates, key=lambda item: item.total_score)
                matches.append(
                    MatchedNorm(
                        volume=entry,
                        norm_code=best_candidate.norm.code,
                        reasoning="LLM недоступна, выбран лучший кандидат по скорингам.",
                        candidate_scores={cand.norm.code: cand.total_score for cand in candidates},
                    )
                )

        cost_result = self._cost_service.estimate_from_entries(entries, extraction)
        warnings.extend(cost_result.extraction.warnings)  # передаём предупреждения экстрактора
        labor_summary = self._calculate_labor(matches)

        return PipelineResult(
            volumes=entries,
            matches=matches,
            cost=cost_result,
            extraction=extraction or cost_result.extraction,
            labor=labor_summary,
            warnings=warnings,
        )

    def _retrieve_candidates(
        self,
        service: GESNRetrievalService,
        entry: WorkVolumeEntry,
        *,
        top_k: int,
    ) -> List[RetrievalCandidate]:
        """
        Получает top_k кандидатов для конкретной позиции объёмов.
        """
        return service.search(
            entry.name,
            expected_unit=entry.unit,
            top_k=top_k,
        )

    def _verify(
        self,
        entry: WorkVolumeEntry,
        candidates: List[RetrievalCandidate],
    ) -> VerificationResult:
        """
        Передаёт кандидатов в LLM для окончательного выбора.
        """
        request = VerificationRequest(
            work_description=entry.name,
            unit=entry.unit,
            candidates=[c.norm for c in candidates],
        )
        return self._verification_service.verify(request)

    def _calculate_labor(self, matches: List[MatchedNorm]) -> Optional[LaborSummary]:
        if not matches:
            return None
        session = self.session
        total_hours = 0.0
        total_workers = 0.0
        labor_entries: List[LaborEntry] = []
        shift_hours = 8.0

        for match in matches:
            norm = (
                session.query(GESNNorm)
                .options(selectinload(GESNNorm.resources))
                .filter(GESNNorm.code == match.norm_code)
                .one_or_none()
            )
            if not norm:
                continue
            labor_resources = [
                resource
                for resource in norm.resources
                if resource.resource_type.lower() in {"labor", "труд", "рабочие"}
                and resource.quantity is not None
            ]
            if not labor_resources:
                continue
            quantity = float(match.volume.quantity)
            entry_hours = 0.0
            resource_details: List[Dict[str, float]] = []
            for resource in labor_resources:
                hours = float(resource.quantity) * quantity
                entry_hours += hours
                resource_details.append(
                    {
                        "quantity_per_unit": float(resource.quantity),
                        "hours_total": hours,
                        "name": resource.name,
                    }
                )
            if entry_hours == 0.0:
                continue
            total_hours += entry_hours
            workers = entry_hours / shift_hours
            total_workers += workers
            labor_entries.append(
                LaborEntry(
                    volume_name=match.volume.name,
                    norm_code=match.norm_code,
                    labor_hours=entry_hours,
                    worker_equivalent=workers,
                    resources=resource_details,
                )
            )
        if not labor_entries:
            return None
        worker_days = total_hours / shift_hours
        schedules = {
            "45_15": {
                "cycle_days": 60,
                "work_days": 45,
                "required_workers": float(max(1, math.ceil(worker_days / 45))),
            },
            "30_15": {
                "cycle_days": 45,
                "work_days": 30,
                "required_workers": float(max(1, math.ceil(worker_days / 30))),
            },
        }
        return LaborSummary(
            entries=labor_entries,
            total_labor_hours=total_hours,
            total_worker_equivalent=total_workers,
            worker_days=worker_days,
            schedules=schedules,
        )

