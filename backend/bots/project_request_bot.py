"""
Telegram bot entrypoint (aiogram) for collecting project initiation requests.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from aiogram import Bot, Dispatcher, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.types import Message

from backend.config.settings import settings
from backend.services.task_queue import task_queue

logger = logging.getLogger(__name__)

dispatcher = Dispatcher()


async def _enqueue_update(message: Message) -> None:
    update_payload: dict[str, Any] = message.model_dump(mode="json")
    task_queue.enqueue(
        task_name="processes.ingest_telegram_update",
        queue=settings.CELERY_PROCESS_QUEUE,
        kwargs={"update": {"message": update_payload}},
    )


@dispatcher.message(CommandStart())
async def handle_start(message: Message) -> None:
    await message.answer(
        "Привет! Я бот BLDR.EMPIRE. Отправьте заявку или документ, чтобы команда могла её обработать."
    )


@dispatcher.message(F.text | F.photo | F.document)
async def handle_request(message: Message) -> None:
    await _enqueue_update(message)
    try:
        await message.answer(
            "✅ Заявка получена и поставлена в очередь. Мы сообщим, когда обработка завершится."
        )
    except TelegramBadRequest as exc:
        logger.warning("Unable to send acknowledgement: %s", exc)


async def _run() -> None:
    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")
    bot = Bot(settings.TELEGRAM_BOT_TOKEN)
    await dispatcher.start_polling(bot, allowed_updates=dispatcher.resolve_used_update_types())


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_run())


if __name__ == "__main__":
    main()

