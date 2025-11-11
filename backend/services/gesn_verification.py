"""
LLM-подтверждение соответствия ВОР ↔ ГЭСН.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional

from backend.models.gesn import GESNNorm
from backend.services.llm_interface import LLMProviderError, get_llm_client

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class VerificationRequest:
    """
    Запрос на проверку: описание работы и список кандидатов.
    """

    work_description: str
    unit: Optional[str]
    candidates: List[GESNNorm]


@dataclass(slots=True)
class VerificationResult:
    """
    Результат проверки: выбранная норма и обоснование.
    """

    norm_code: str
    reasoning: str


class GESNVerificationService:
    """
    Сервис, использующий LLM для окончательной верификации соответствия.
    """

    PROMPT_TEMPLATE = """Ты опытный инженер-сметчик. Проверь соответствие работы и норм ГЭСН и выбери единственную подходящую.

[РАБОТА]: {description}
Единица измерения: {unit}

[КАНДИДАТЫ]:
{candidates}

Инструкция:
- Выбери ОДНУ норму.
- Объясни, почему она подходит и почему остальные отклоняются.
- Ответ верни строго в формате JSON: {{
  "norm_code": "...",
  "reasoning": "..."
}}
"""

    def verify(self, request: VerificationRequest) -> VerificationResult:
        if not request.candidates:
            raise ValueError("Нет кандидатов для проверки.")

        client = get_llm_client()
        candidates_text = self._render_candidates(request.candidates)
        prompt = self.PROMPT_TEMPLATE.format(
            description=request.work_description,
            unit=request.unit or "не указана",
            candidates=candidates_text,
        )

        schema = {
            "type": "object",
            "properties": {
                "norm_code": {"type": "string"},
                "reasoning": {"type": "string"},
            },
            "required": ["norm_code", "reasoning"],
        }

        try:
            response = client.generate_structured(prompt, schema=schema, max_tokens=1024)
            return VerificationResult(norm_code=response["norm_code"], reasoning=response["reasoning"])
        except LLMProviderError as exc:
            logger.error("LLM verification failed: %s", exc)
            raise

    def _render_candidates(self, candidates: List[GESNNorm]) -> str:
        parts = []
        for norm in candidates:
            parts.append(
                f"- Код: {norm.code}\n"
                f"  Название: {norm.name}\n"
                f"  Ед. изм.: {norm.unit}\n"
                f"  Раздел: {norm.section.code if norm.section else 'не указан'}\n"
                f"  Параметры: {norm.parameters or 'нет'}\n"
                f"  Состав работ: {norm.composition or 'нет'}\n"
            )
        return "\n".join(parts)


