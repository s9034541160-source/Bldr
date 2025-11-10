"""
Handlers for processing incoming requests via email (IMAP).
"""

from __future__ import annotations

import email
import imaplib
import logging
from contextlib import contextmanager
from email.policy import default as default_policy
from typing import Generator, List, Optional

from backend.config.settings import settings
from backend.services.intake.base import BaseIntakeHandler
from backend.services.intake.models import IncomingAttachment, IncomingRequest, RequestChannel

logger = logging.getLogger(__name__)


class EmailIntakeHandler(BaseIntakeHandler):
    """IMAP-based handler for project initiation requests."""

    def __init__(
        self,
        *,
        host: str,
        username: str,
        password: str,
        port: int = 993,
        use_ssl: bool = True,
        mailbox: str = "INBOX",
    ) -> None:
        super().__init__(RequestChannel.EMAIL)
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.use_ssl = use_ssl
        self.mailbox = mailbox

    @classmethod
    def from_settings(cls) -> "EmailIntakeHandler":
        if not settings.IMAP_HOST or not settings.IMAP_USERNAME or not settings.IMAP_PASSWORD:
            raise RuntimeError("IMAP credentials are not configured in settings")
        return cls(
            host=settings.IMAP_HOST,
            username=settings.IMAP_USERNAME,
            password=settings.IMAP_PASSWORD,
            port=settings.IMAP_PORT,
            use_ssl=settings.IMAP_USE_SSL,
            mailbox=settings.IMAP_MAILBOX,
        )

    @contextmanager
    def _connect(self) -> Generator[imaplib.IMAP4, None, None]:
        connection: imaplib.IMAP4
        if self.use_ssl:
            connection = imaplib.IMAP4_SSL(self.host, self.port)
        else:
            connection = imaplib.IMAP4(self.host, self.port)
        try:
            connection.login(self.username, self.password)
            connection.select(self.mailbox)
            yield connection
        finally:
            try:
                connection.logout()
            except Exception:  # noqa: BLE001
                logger.debug("IMAP logout failed", exc_info=True)

    def fetch_unseen(self, *, limit: int = 25) -> List[IncomingRequest]:
        """Fetch unseen messages, mark them as seen and convert to IncomingRequest list."""
        requests: List[IncomingRequest] = []
        try:
            with self._connect() as client:
                status, data = client.search(None, "UNSEEN")
                if status != "OK":
                    logger.warning("IMAP search failed with status %s", status)
                    return []
                message_ids = data[0].split()
                for message_id in message_ids[:limit]:
                    status, payload = client.fetch(message_id, "(RFC822)")
                    if status != "OK" or not payload:
                        logger.warning("Failed to fetch message %s (status=%s)", message_id, status)
                        continue
                    raw_email = payload[0][1]
                    request = self._parse_email(raw_email)
                    request.external_id = message_id.decode()
                    requests.append(request)
                    client.store(message_id, "+FLAGS", "\\Seen")
        except imaplib.IMAP4.error as exc:
            logger.error("IMAP error: %s", exc, exc_info=True)
        return requests

    def _parse_email(self, raw_message: bytes) -> IncomingRequest:
        message = email.message_from_bytes(raw_message, policy=default_policy)
        subject = self.decode_mime_words(message.get("Subject"))
        sender = message.get("From")

        body_text: Optional[str] = None
        attachments: List[IncomingAttachment] = []

        for part in message.walk():
            if part.is_multipart():
                continue
            content_disposition = part.get_content_disposition()
            content_type = part.get_content_type()
            payload = part.get_payload(decode=True)

            if content_disposition == "attachment":
                filename = self.decode_mime_words(part.get_filename()) or "attachment.bin"
                attachments.append(
                    IncomingAttachment(
                        filename=filename,
                        content_type=content_type,
                        content=payload,
                        size=len(payload or b""),
                        metadata={"content_id": part.get("Content-ID")},
                    )
                )
            elif content_type.startswith("text/") and body_text is None:
                try:
                    body_text = payload.decode(part.get_content_charset() or "utf-8", errors="ignore") if payload else None
                except (LookupError, AttributeError):
                    body_text = (payload or b"").decode("utf-8", errors="ignore")

        metadata = self.message_to_dict(message)
        return IncomingRequest(
            channel=RequestChannel.EMAIL,
            subject=subject,
            body=body_text,
            customer_name=None,
            contact_email=sender,
            contact_phone=None,
            project_location=None,
            metadata={"headers": metadata.get("headers")},
            raw_payload=metadata,
            attachments=attachments,
        )


__all__ = ["EmailIntakeHandler"]

