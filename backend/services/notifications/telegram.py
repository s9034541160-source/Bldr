"""
Сервис уведомлений менеджеров через Telegram.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

import requests

from backend.config.settings import settings
from backend.models.auth import User

logger = logging.getLogger(__name__)


class ManagerNotificationService:
    """
    Отправляет уведомления менеджерам при назначении проектов.
    """

    def __init__(self, bot_token: Optional[str] = None) -> None:
        self.bot_token = bot_token or settings.TELEGRAM_BOT_TOKEN

    def notify_assignment(self, manager: User, *, project_code: str, project_name: str) -> None:
        if not self.bot_token:
            logger.debug("Telegram bot token not configured; skipping notification.")
            return
        chat_id = getattr(manager, "telegram_chat_id", None)
        if not chat_id:
            logger.debug("Manager %s has no telegram_chat_id; skipping notification.", manager.id)
            return
        message = (
            f"📂 Назначен новый проект {project_code}\n"
            f"Название: {project_name}\n"
            "Откройте карточку проекта для деталей."
        )
        self._send_message(chat_id=chat_id, text=message)

    def notify_procurement(self, *, materials: list[str], context: Optional[str] = None) -> None:
        if not self.bot_token:
            logger.debug("Telegram bot token not configured; skipping procurement notification.")
            return
        chat_id = settings.TELEGRAM_PRICE_REQUEST_CHAT_ID
        if not chat_id:
            logger.debug("TELEGRAM_PRICE_REQUEST_CHAT_ID not configured; skipping procurement notification.")
            return
        if not materials:
            return
        body_lines = ["⚠️ Требуются цены на материалы:", ""]
        body_lines.extend(f"• {name}" for name in materials)
        if context:
            body_lines.extend(["", context])
        message = "\n".join(body_lines)
        self._send_message(chat_id=chat_id, text=message)

    def notify_teo_approval(
        self,
        *,
        chat_id: str,
        project_code: str,
        project_name: str,
        role: str,
        approver_name: Optional[str],
        summary: str,
        documents: Dict[str, str],
    ) -> None:
        """
        Отправляет сообщение об этапах согласования ТЭО.
        """
        if not chat_id:
            logger.debug("Approval chat id is not provided; skipping TEO approval notification.")
            return
        lines = [
            "📑 Предварительное ТЭО — требуется согласование",
            f"Проект {project_code} — {project_name}",
            f"Ответственный этап: {role}{f' ({approver_name})' if approver_name else ''}",
            "",
            summary,
        ]
        if documents:
            lines.append("")
            lines.append("Файлы отчёта:")
            for label, path in documents.items():
                lines.append(f"• {label.upper()}: {path}")
        message = "\n".join(lines)
        self._send_message(chat_id=chat_id, text=message)

    def _send_message(self, *, chat_id: str, text: str) -> None:
        if not self.bot_token:
            logger.debug("Telegram bot token not configured; skipping message send.")
            return
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
                json={"chat_id": chat_id, "text": text},
                timeout=10,
            )
            response.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to send Telegram message to %s: %s", chat_id, exc)


manager_notification_service = ManagerNotificationService()

__all__ = ["manager_notification_service", "ManagerNotificationService"]


