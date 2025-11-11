"""
SMTP email notification service.
"""

from __future__ import annotations

import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Iterable, Optional

from backend.config.settings import settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class EmailDeliveryResult:
    recipient: str
    status: str
    error: Optional[str] = None


class EmailNotificationService:
    """
    Simple SMTP client for sending plain-text notifications.
    """

    def __init__(self) -> None:
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME
        self.password = settings.SMTP_PASSWORD
        self.use_tls = settings.SMTP_USE_TLS
        self.sender = settings.EMAIL_FROM
        self.reply_to = settings.EMAIL_REPLY_TO

    def is_configured(self) -> bool:
        return bool(self.host and self.port and self.sender)

    def send(
        self,
        recipients: Iterable[str],
        *,
        subject: str,
        body: str,
    ) -> list[EmailDeliveryResult]:
        recipients_list = [email.strip() for email in recipients if email and email.strip()]
        if not recipients_list:
            return []

        if not self.is_configured():
            logger.info("SMTP service not configured; skipping email send.")
            return [EmailDeliveryResult(recipient=rcpt, status="skipped", error="not_configured") for rcpt in recipients_list]

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.sender
        message["To"] = ", ".join(recipients_list)
        if self.reply_to:
            message["Reply-To"] = self.reply_to
        message.set_content(body)

        results: list[EmailDeliveryResult] = []
        try:
            with smtplib.SMTP(self.host, self.port, timeout=10) as client:
                if self.use_tls:
                    client.starttls()
                if self.username and self.password:
                    client.login(self.username, self.password)
                client.send_message(message)
            for recipient in recipients_list:
                results.append(EmailDeliveryResult(recipient=recipient, status="sent"))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to send email notification: %s", exc)
            for recipient in recipients_list:
                results.append(EmailDeliveryResult(recipient=recipient, status="error", error=str(exc)))
        return results


email_notification_service = EmailNotificationService()

__all__ = ["email_notification_service", "EmailNotificationService", "EmailDeliveryResult"]


