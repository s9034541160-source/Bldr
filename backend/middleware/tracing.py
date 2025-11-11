"""
Tracing middleware for FastAPI application.

Добавляет correlation ID (X-Request-ID) для входящих запросов,
сохраняет его в state и добавляет в ответы. Также логирует
основные метрики запроса.
"""

from __future__ import annotations

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

import logging

logger = logging.getLogger("bldr.tracing")


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """Middleware добавляющее correlation ID и базовый трейсинг."""

    header_name = "X-Request-ID"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        correlation_id = request.headers.get(self.header_name, str(uuid.uuid4()))

        request.state.correlation_id = correlation_id
        start_time = time.perf_counter()

        logger.info(
            "Request started",
            extra={
                "CorrelationId": correlation_id,
                "Method": request.method,
                "Path": request.url.path,
                "Client": request.client.host if request.client else None,
            },
        )

        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(
                "Request failed",
                extra={
                    "CorrelationId": correlation_id,
                    "Method": request.method,
                    "Path": request.url.path,
                    "ElapsedMs": round(elapsed_ms, 2),
                },
            )
            raise

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        response.headers[self.header_name] = correlation_id

        logger.info(
            "Request completed",
            extra={
                "CorrelationId": correlation_id,
                "Method": request.method,
                "Path": request.url.path,
                "StatusCode": response.status_code,
                "ElapsedMs": round(elapsed_ms, 2),
            },
        )

        return response


