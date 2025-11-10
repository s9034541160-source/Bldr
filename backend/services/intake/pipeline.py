"""
Unified pipeline for intake channels.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict

from backend.config.settings import settings
from backend.services.intake.email_handler import EmailIntakeHandler
from backend.services.intake.google_forms import GoogleFormsIntakeParser
from backend.services.intake.models import IncomingRequest, RequestChannel
from backend.services.intake.telegram_handler import telegram_handler_from_settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class IntakePipeline:
    """Routes raw payloads to concrete handlers."""

    email_handler: EmailIntakeHandler
    forms_parser: GoogleFormsIntakeParser
    telegram_handler = telegram_handler_from_settings()

    @classmethod
    def from_settings(cls) -> "IntakePipeline":
        email_handler = EmailIntakeHandler.from_settings()
        forms_parser = GoogleFormsIntakeParser()
        return cls(email_handler=email_handler, forms_parser=forms_parser)

    def parse_payload(self, payload: Dict[str, Any]) -> IncomingRequest:
        channel_value = payload.get("channel")
        if channel_value is None:
            raise ValueError("Payload must contain 'channel'")
        channel = RequestChannel(channel_value)

        match channel:
            case RequestChannel.EMAIL:
                raw_bytes = payload.get("raw")
                if not isinstance(raw_bytes, (bytes, bytearray)):
                    raise ValueError("Email payload expects raw bytes under 'raw'")
                return self.email_handler._parse_email(bytes(raw_bytes))
            case RequestChannel.GOOGLE_FORMS:
                submission = payload.get("submission")
                if not isinstance(submission, dict):
                    raise ValueError("Google Forms payload expects dict under 'submission'")
                return self.forms_parser.parse_submission(submission)
            case RequestChannel.TELEGRAM:
                update = payload.get("update")
                if not isinstance(update, dict):
                    raise ValueError("Telegram payload expects dict under 'update'")
                handler = self.telegram_handler
                return handler.parse_update(update)
        raise ValueError(f"Unsupported channel {channel}")


__all__ = ["IntakePipeline"]

