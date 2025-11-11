"""
Сервис уведомлений менеджеров через Telegram.
"""

from __future__ import annotations

import logging
from typing import Optional

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
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
                json={"chat_id": chat_id, "text": message},
                timeout=10,
            )
            response.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to send Telegram notification to manager %s: %s", manager.id, exc)


manager_notification_service = ManagerNotificationService()

__all__ = ["manager_notification_service", "ManagerNotificationService"]


