"""
Сервис извлечения адресов из произвольного текста заявок.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Optional

from backend.services.llm_interface import get_llm_client, LLMProviderError

logger = logging.getLogger(__name__)

ADDRESS_PATTERN = re.compile(
    r"(?P<city>(?:г\.|город)\s*[А-ЯЁA-Z][\w\-]+)"
    r"(?:,\s*(?P<street>(?:ул\.|улица)\s*[А-ЯЁA-Z0-9][^,;]+))?"
    r"(?:,\s*(?P<house>(?:д\.|дом)\s*\d+[А-Яа-яA-Za-z0-9\-]*))?",
    re.IGNORECASE,
)


@dataclass(slots=True)
class AddressExtractionResult:
    address: Optional[str]
    method: str


class AddressExtractor:
    """
    Извлекает адрес из текстового описания заявки.
    """

    def extract(self, *, text: Optional[str], fallback_prompt: bool = True) -> AddressExtractionResult:
        if not text:
            return AddressExtractionResult(address=None, method="empty")

        match = ADDRESS_PATTERN.search(text)
        if match:
            address = ", ".join(filter(None, match.groups()))
            return AddressExtractionResult(address=address, method="regex")

        if not fallback_prompt:
            return AddressExtractionResult(address=None, method="none")

        try:
            client = get_llm_client()
            prompt = (
                "Определи адрес строительного объекта в тексте заявки.\n"
                "Верни только адрес, без пояснений. Если адреса нет, верни 'NULL'.\n"
                f"Заявка:\n{text}"
            )
            response = client.generate(prompt, max_tokens=128, temperature=0.0)
            cleaned = response.strip()
            if cleaned and cleaned.upper() != "NULL":
                return AddressExtractionResult(address=cleaned, method="llm")
        except LLMProviderError as exc:
            logger.debug("LLM address extraction failed: %s", exc)

        return AddressExtractionResult(address=None, method="none")


address_extractor = AddressExtractor()

__all__ = ["address_extractor", "AddressExtractor", "AddressExtractionResult"]


