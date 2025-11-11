"""
Извлечение объемов работ (ВоМ) для процесса F1.02.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Dict, Iterable, List, Optional

from backend.services.document_parser import get_document_parser

logger = logging.getLogger(__name__)

CODE_PATTERN = re.compile(r"(?P<code>(?:ГЭСН|ФЕР|ТЕР)\s*[\d\-\.\/]+)", re.IGNORECASE)
QUANTITY_PATTERN = re.compile(
    r"(?P<quantity>\d+(?:[.,]\d+)?)\s*(?P<unit>м3|м²|м2|м|шт|т|кг|л|чел\.?ч|ч(?:ас)?|дн\.?|м\.п\.|пог\.м|м³|м²|%)",
    re.IGNORECASE,
)
SPLITTER_PATTERN = re.compile(r"[–—\-:;]+")

CATEGORY_HINTS: Dict[str, str] = {
    "01": "Земляные работы",
    "02": "Фундаменты",
    "03": "Каменные конструкции",
    "04": "Бетонные конструкции",
    "05": "Металлические конструкции",
    "06": "Деревянные конструкции",
    "07": "Кровли",
    "08": "Изоляционные работы",
    "09": "Отделочные работы",
    "10": "Санитарно-технические работы",
    "11": "Отопление",
    "12": "Вентиляция и кондиционирование",
    "13": "Электротехнические работы",
    "14": "Автоматизация",
    "15": "Связь и сигнализация",
}


@dataclass(slots=True)
class WorkVolumeEntry:
    """Описание единицы объема работ."""

    name: str
    quantity: Decimal
    unit: str
    source_line: str
    code: Optional[str] = None
    category: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class WorkVolumeSummary:
    """Сводная информация по категориям."""

    totals: Dict[str, Decimal] = field(default_factory=dict)
    total_quantity: Decimal = Decimal("0")


@dataclass(slots=True)
class WorkVolumeResult:
    """Результат обработки документа."""

    entries: List[WorkVolumeEntry]
    summary: WorkVolumeSummary
    warnings: List[str] = field(default_factory=list)


class WorkVolumeExtractor:
    """Извлекает объемы работ из произвольного текста или файлов."""

    def __init__(self) -> None:
        self.parser = get_document_parser()

    # ------------------------------------------------------------------ #
    # Публичные методы
    # ------------------------------------------------------------------ #
    def extract_from_file(self, file_path: str) -> WorkVolumeResult:
        text = self.parser.extract_plain_text(file_path)
        return self.extract_from_text(text)

    def extract_from_text(self, text: str) -> WorkVolumeResult:
        entries: List[WorkVolumeEntry] = []
        warnings: List[str] = []

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or len(line) < 6:
                continue

            entry = self._parse_line(line)
            if entry:
                entries.append(entry)

        if not entries:
            warnings.append("Не удалось извлечь объемы работ — проверьте формат документа.")

        summary = self._build_summary(entries)
        return WorkVolumeResult(entries=entries, summary=summary, warnings=warnings)

    # ------------------------------------------------------------------ #
    # Внутренние методы
    # ------------------------------------------------------------------ #
    def _parse_line(self, line: str) -> Optional[WorkVolumeEntry]:
        code_match = CODE_PATTERN.search(line)
        code = None
        remainder = line
        if code_match:
            code = self._normalize_code(code_match.group("code"))
            remainder = line[code_match.end() :].strip()

        quantity_match = QUANTITY_PATTERN.search(remainder)
        if not quantity_match:
            # Попытка учитывать строки с разделителями (табличный формат)
            tokens = [token.strip() for token in SPLITTER_PATTERN.split(remainder) if token.strip()]
            quantity_match = self._find_quantity_in_tokens(tokens)
            if quantity_match is None:
                return None
            quantity, unit, name = quantity_match
        else:
            quantity = self._parse_decimal(quantity_match.group("quantity"))
            unit = self._normalize_unit(quantity_match.group("unit"))
            name = remainder[: quantity_match.start()].strip(" -–—;:") or "Без названия"

        if quantity is None or quantity <= 0:
            return None

        category = self._detect_category(code)

        return WorkVolumeEntry(
            name=name,
            quantity=quantity,
            unit=unit,
            source_line=line,
            code=code,
            category=category,
            metadata={"source": "regex"},
        )

    def _find_quantity_in_tokens(
        self, tokens: Iterable[str]
    ) -> Optional[tuple[Decimal, str, str]]:
        if not tokens:
            return None

        for idx, token in enumerate(tokens):
            match = QUANTITY_PATTERN.fullmatch(token)
            if not match:
                continue
            quantity = self._parse_decimal(match.group("quantity"))
            unit = self._normalize_unit(match.group("unit"))
            if quantity is None or quantity <= 0:
                continue
            name_parts = list(tokens)
            del name_parts[idx]
            name = ", ".join(name_parts).strip()
            return quantity, unit, name or "Без названия"
        return None

    def _parse_decimal(self, value: str) -> Optional[Decimal]:
        try:
            normalized = value.replace(",", ".")
            return Decimal(normalized)
        except (InvalidOperation, AttributeError):
            logger.debug("Не удалось преобразовать значение %s в Decimal", value)
            return None

    def _normalize_unit(self, unit: str) -> str:
        normalized = unit.lower().replace(" ", "")
        mapping = {
            "м3": "м³",
            "м²": "м²",
            "м2": "м²",
            "м.п.": "пог.м",
            "ч": "ч",
            "час": "ч",
            "часов": "ч",
            "чел.ч": "чел·ч",
            "чел.": "чел·ч",
            "дн.": "дн",
        }
        return mapping.get(normalized, normalized)

    def _normalize_code(self, code: str) -> str:
        normalized = re.sub(r"\s+", "", code.upper())
        normalized = normalized.replace("–", "-").replace("—", "-")
        return normalized

    def _detect_category(self, code: Optional[str]) -> Optional[str]:
        if not code:
            return None
        digits = re.sub(r"\D", "", code)
        if len(digits) < 2:
            return None
        prefix = digits[:2]
        return CATEGORY_HINTS.get(prefix)

    def _build_summary(self, entries: List[WorkVolumeEntry]) -> WorkVolumeSummary:
        totals: Dict[str, Decimal] = {}
        total_quantity = Decimal("0")
        for entry in entries:
            total_quantity += entry.quantity
            category = entry.category or "Прочее"
            totals.setdefault(category, Decimal("0"))
            totals[category] += entry.quantity
        return WorkVolumeSummary(totals=totals, total_quantity=total_quantity)


# Глобальный экземпляр
work_volume_extractor = WorkVolumeExtractor()

__all__ = ["WorkVolumeExtractor", "WorkVolumeEntry", "WorkVolumeSummary", "WorkVolumeResult", "work_volume_extractor"]


