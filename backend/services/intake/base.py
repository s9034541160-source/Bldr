"""
Base abstractions for intake handlers.
"""

from __future__ import annotations

import email
import logging
from dataclasses import dataclass
from email.header import decode_header, make_header
from typing import Any, Dict, Optional

from backend.services.intake.models import IncomingRequest, RequestChannel

logger = logging.getLogger(__name__)


@dataclass(slots=True, kw_only=True)
class IntakeContext:
    """Описание контекста обработки заявки."""

    channel: RequestChannel
    source_identifier: Optional[str] = None
    metadata: Dict[str, Any] = None


class BaseIntakeHandler:
    """Базовый класс обработчиков входящих заявок."""

    channel: RequestChannel

    def __init__(self, channel: RequestChannel) -> None:
        self.channel = channel

    @staticmethod
    def decode_mime_words(value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        try:
            return str(make_header(decode_header(value)))
        except Exception as exc:  # noqa: BLE001
            logger.debug("Failed to decode header %s: %s", value, exc)
            return value

    @staticmethod
    def message_to_dict(message: email.message.Message) -> Dict[str, Any]:
        """Преобразование email.message в сериализуемый словарь."""
        serialized: Dict[str, Any] = {
            "subject": message.get("Subject"),
            "from": message.get("From"),
            "to": message.get("To"),
            "date": message.get("Date"),
            "headers": dict(message.items()),
            "parts": [],
        }
        for part in message.walk():
            if part.is_multipart():
                continue
            serialized["parts"].append(
                {
                    "content_type": part.get_content_type(),
                    "content_disposition": part.get_content_disposition(),
                    "filename": part.get_filename(),
                    "size": len(part.get_payload(decode=True) or b""),
                }
            )
        return serialized

    def build_request(self, data: Dict[str, Any]) -> IncomingRequest:
        raise NotImplementedError("build_request must be implemented by subclasses")


__all__ = ["BaseIntakeHandler", "IntakeContext"]

