"""
Handler for Telegram bot updates used for project requests.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests

from backend.config.settings import settings
from backend.services.intake.models import IncomingAttachment, IncomingRequest, RequestChannel

logger = logging.getLogger(__name__)


@dataclass(slots=True, kw_only=True)
class TelegramIntakeHandler:
    """Transforms Telegram updates into IncomingRequest objects."""

    bot_token: Optional[str] = None

    def parse_update(self, update: Dict[str, Any]) -> IncomingRequest:
        message = update.get("message") or update.get("channel_post") or {}
        contact_email = None
        contact_phone = None
        customer_name = None

        if "contact" in message:
            contact = message["contact"]
            contact_phone = contact.get("phone_number")
            customer_name = contact.get("first_name")
        if "from" in message:
            user = message["from"]
            customer_name = customer_name or user.get("first_name")
            contact_email = user.get("username")

        text = message.get("text") or message.get("caption")

        attachments = self._extract_attachments(message)
        metadata = {"message_id": message.get("message_id"), "chat_id": message.get("chat", {}).get("id")}

        return IncomingRequest(
            channel=RequestChannel.TELEGRAM,
            subject=text[:120] if text else "Telegram request",
            body=text,
            customer_name=customer_name,
            contact_email=contact_email,
            contact_phone=contact_phone,
            project_location=None,
            metadata=metadata,
            raw_payload=update,
            attachments=attachments,
            external_id=str(message.get("message_id")) if message.get("message_id") else None,
        )

    def _extract_attachments(self, message: Dict[str, Any]) -> List[IncomingAttachment]:
        attachments: List[IncomingAttachment] = []
        file_candidates: List[Dict[str, Any]] = []

        if photos := message.get("photo"):
            largest = sorted(photos, key=lambda item: item.get("file_size", 0))[-1]
            file_candidates.append({"type": "photo", **largest})
        if document := message.get("document"):
            file_candidates.append({"type": "document", **document})

        for candidate in file_candidates:
            file_id = candidate.get("file_id")
            filename = candidate.get("file_name") or f"telegram_{file_id}"
            mime_type = candidate.get("mime_type") or "application/octet-stream"
            content: Optional[bytes] = None

            if self.bot_token and file_id:
                try:
                    content = self._download_file(file_id)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Unable to download telegram file %s: %s", file_id, exc)

            attachments.append(
                IncomingAttachment(
                    filename=filename,
                    content_type=mime_type,
                    content=content,
                    size=candidate.get("file_size"),
                    metadata={"telegram_file_id": file_id, "type": candidate.get("type")},
                )
            )
        return attachments

    def _download_file(self, file_id: str) -> bytes:
        """Download actual file bytes via Telegram API (if token provided)."""
        if not self.bot_token:
            raise RuntimeError("Telegram bot token is not configured")

        file_info = requests.get(
            f"https://api.telegram.org/bot{self.bot_token}/getFile",
            params={"file_id": file_id},
            timeout=30,
        ).json()
        if not file_info.get("ok"):
            raise RuntimeError(f"Telegram API returned error: {file_info}")

        file_path = file_info["result"]["file_path"]
        response = requests.get(f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}", timeout=60)
        response.raise_for_status()
        return response.content


def telegram_handler_from_settings() -> TelegramIntakeHandler:
    return TelegramIntakeHandler(bot_token=settings.TELEGRAM_BOT_TOKEN)


__all__ = ["TelegramIntakeHandler", "telegram_handler_from_settings"]

