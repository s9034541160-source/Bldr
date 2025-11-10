"""Инструменты для логирования действий агентов."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Any, Dict, Optional

LOG_DIR = Path("logs/agents")
LOG_DIR.mkdir(parents=True, exist_ok=True)


class AgentLogger:
    """Структурированное логирование действий агента."""

    _locks: Dict[str, RLock] = {}

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.logger = logging.getLogger(f"agent.{agent_id}")
        self.logger.setLevel(logging.INFO)
        self._lock = self._locks.setdefault(agent_id, RLock())
        self.log_file = LOG_DIR / f"{agent_id}.log"

    def log(
        self,
        action: str,
        status: str = "success",
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Записывает действие агента в структурированном виде."""
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": self.agent_id,
            "action": action,
            "status": status,
            "message": message,
            "metadata": metadata or {},
        }

        self.logger.info("Agent action", extra={"agent_action": record})
        with self._lock:
            with self.log_file.open("a", encoding="utf-8") as file:
                file.write(json.dumps(record, ensure_ascii=False) + "\n")


def log_agent_action(
    agent_id: str,
    action: str,
    status: str = "success",
    message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Утилита для логирования действия агентом без создания экземпляра."""
    AgentLogger(agent_id).log(action, status=status, message=message, metadata=metadata)
