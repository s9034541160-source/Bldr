"""
Dataclasses and enums describing intake requests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class RequestChannel(str, Enum):
    """Источники поступления заявок."""

    EMAIL = "email"
    GOOGLE_FORMS = "google_forms"
    TELEGRAM = "telegram"


@dataclass(slots=True, kw_only=True)
class IncomingAttachment:
    """Описание вложения, полученного вместе с заявкой."""

    filename: str
    content_type: str
    content: Optional[bytes] = None
    size: Optional[int] = None
    text_content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, kw_only=True)
class IncomingRequest:
    """Унифицированное представление заявки из любого канала."""

    channel: RequestChannel
    subject: Optional[str]
    body: Optional[str]
    customer_name: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    project_location: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_payload: Dict[str, Any] = field(default_factory=dict)
    attachments: List[IncomingAttachment] = field(default_factory=list)
    external_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "channel": self.channel.value,
            "subject": self.subject,
            "body": self.body,
            "customer_name": self.customer_name,
            "contact_email": self.contact_email,
            "contact_phone": self.contact_phone,
            "project_location": self.project_location,
            "metadata": self.metadata,
            "raw_payload": self.raw_payload,
            "attachments": [
                {
                    "filename": attachment.filename,
                    "content_type": attachment.content_type,
                    "size": attachment.size,
                    "text_content": attachment.text_content,
                    "metadata": attachment.metadata,
                }
                for attachment in self.attachments
            ],
            "external_id": self.external_id,
        }


__all__ = ["RequestChannel", "IncomingAttachment", "IncomingRequest"]

