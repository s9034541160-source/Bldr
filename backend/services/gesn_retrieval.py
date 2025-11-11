"""
Поисковый сервис для работы с каталогом ГЭСН.

Сочетает нечеткий поиск, семантические эмбеддинги и матчинг по параметрам.
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable, List, Optional, Sequence, Tuple

import numpy as np
from fuzzywuzzy import fuzz
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.gesn import GESNNorm

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# Эмбеддинги
# ------------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _load_sentence_model():
    from sentence_transformers import SentenceTransformer

    logger.info("Загрузка модели SentenceTransformer для каталога ГЭСН")
    return SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")


def _encode_sentences(sentences: Sequence[str]) -> np.ndarray:
    if not sentences:
        return np.empty((0, 384))
    model = _load_sentence_model()
    return np.asarray(model.encode(sentences, batch_size=32, convert_to_numpy=True, normalize_embeddings=True))


# ------------------------------------------------------------------------------
# Структуры данных
# ------------------------------------------------------------------------------


@dataclass(slots=True)
class RetrievalCandidate:
    """
    Норматив-кандидат с весами различных метрик.
    """

    norm: GESNNorm
    fuzzy_score: float
    semantic_score: float
    unit_match: bool
    parameters_score: float

    @property
    def total_score(self) -> float:
        """
        Итоговая оценка — взвешенная сумма компонент.
        """
        weights = {
            "fuzzy": 0.35,
            "semantic": 0.45,
            "unit": 0.1,
            "parameters": 0.1,
        }
        unit_factor = 1.0 if self.unit_match else 0.5
        return (
            weights["fuzzy"] * self.fuzzy_score
            + weights["semantic"] * self.semantic_score
            + weights["unit"] * unit_factor
            + weights["parameters"] * self.parameters_score
        )


# ------------------------------------------------------------------------------
# Сервис
# ------------------------------------------------------------------------------


class GESNRetrievalService:
    """
    Сервис комбинированного поиска нормативов ГЭСН.
    """

    def __init__(self, session: Session):
        self.session = session

    # -- публичные методы ------------------------------------------------------

    def search(
        self,
        query: str,
        *,
        expected_unit: Optional[str] = None,
        top_k: int = 10,
        section_filter: Optional[Iterable[str]] = None,
    ) -> List[RetrievalCandidate]:
        """
        Основной метод: возвращает список кандидатов.

        Args:
            query: описание работы из ведомости объёмов.
            expected_unit: единица измерения, подсказка для фильтрации.
            top_k: максимальное значение результатов.
            section_filter: ограничение по кодам разделов (например, "16" для отопления).
        """
        norms = self._fetch_norms(section_filter)

        semantic_scores = self._semantic_scores(query, [norm.name for norm in norms])

        candidates: List[RetrievalCandidate] = []
        for norm, sem_score in zip(norms, semantic_scores):
            fuzzy_score = self._fuzzy_score(query, norm.name)
            unit_match = self._unit_matches(norm.unit, expected_unit)
            parameters_score = self._parameters_match(query, norm.parameters or {})

            candidate = RetrievalCandidate(
                norm=norm,
                fuzzy_score=fuzzy_score,
                semantic_score=sem_score,
                unit_match=unit_match,
                parameters_score=parameters_score,
            )
            candidates.append(candidate)

        candidates.sort(key=lambda c: c.total_score, reverse=True)
        return candidates[:top_k]

    # -- внутренние методы -----------------------------------------------------

    def _fetch_norms(self, section_filter: Optional[Iterable[str]]) -> List[GESNNorm]:
        stmt = select(GESNNorm)
        if section_filter:
            stmt = stmt.filter(GESNNorm.section.has(GESNNorm.section.has(code_in=list(section_filter))))  # type: ignore[attr-defined]
        return list(self.session.execute(stmt).scalars())

    def _semantic_scores(self, query: str, candidates: Sequence[str]) -> List[float]:
        if not candidates:
            return []
        query_emb = _encode_sentences([query])[0]
        cand_embs = _encode_sentences(candidates)
        scores = cand_embs @ query_emb
        scores = np.clip(scores, -1.0, 1.0)
        scores = (scores + 1.0) / 2.0  # приводим в диапазон [0,1]
        return scores.tolist()

    def _fuzzy_score(self, query: str, candidate: str) -> float:
        return fuzz.token_set_ratio(query, candidate) / 100.0

    def _unit_matches(self, norm_unit: str, expected_unit: Optional[str]) -> bool:
        if not expected_unit:
            return False
        normalized = self._normalize_unit(norm_unit)
        expected = self._normalize_unit(expected_unit)
        return normalized == expected

    def _normalize_unit(self, unit: str) -> str:
        unit_map = {
            "чел.ч": "чел·ч",
            "кв.м": "м²",
            "кв. м": "м²",
            "м2": "м²",
            "м3": "м³",
        }
        normalized = unit.lower().replace(" ", "")
        return unit_map.get(normalized, normalized)

    def _parameters_match(self, query: str, parameters: dict) -> float:
        """
        Простейшее сопоставление диаметров, массы, диапазонов. Возвращает 0..1.
        """
        if not parameters:
            return 0.5  # нет параметров — нейтральный вклад

        score = 0.5
        query = query.lower()

        diameter = parameters.get("diameter") or parameters.get("Диаметр")
        if diameter:
            if self._number_in_text(diameter, query):
                score += 0.25
            else:
                score -= 0.25

        weight = parameters.get("weight") or parameters.get("Масса")
        if weight:
            if self._number_in_text(weight, query):
                score += 0.25
            else:
                score -= 0.25

        return max(0.0, min(1.0, score))

    def _number_in_text(self, value: str, text: str) -> bool:
        try:
            value_float = float(str(value).replace(",", "."))
        except ValueError:
            return False

        pattern = re.compile(r"\d+(?:[,.]\d+)?")
        for match in pattern.finditer(text):
            try:
                number = float(match.group(0).replace(",", "."))
            except ValueError:
                continue
            if math.isclose(number, value_float, rel_tol=0.05):
                return True
        return False


