"""
System-level Celery tasks (health checks, scheduled maintenance).
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="system.health_check")
def health_check() -> Dict[str, str]:
    """Simple task to verify that Celery workers are responsive."""
    timestamp = datetime.utcnow().isoformat()
    logger.debug("Celery health check executed at %s", timestamp)
    return {"status": "ok", "timestamp": timestamp}


__all__ = ["health_check"]

