"""
Authentication middleware.

Извлекает Bearer токен из заголовка Authorization, валидирует его
и сохраняет текущего пользователя в `request.state.user`. Используется
для логирования и трейсинга, а также для удобного доступа к данным
пользователя в обработчиках.
"""

from __future__ import annotations

from typing import Callable, Iterable, Optional, Set

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from backend.models import SessionLocal
from backend.services.auth_service import verify_token, get_user_by_username

import logging

logger = logging.getLogger("bldr.auth")


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware, заполняющее request.state.user."""

    def __init__(self, app, exclude_paths: Optional[Iterable[str]] = None):
        super().__init__(app)
        self.exclude_paths: Set[str] = set(exclude_paths or [])

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        if self._is_excluded(path):
            return await call_next(request)

        token = self._extract_token(request)
        if not token:
            # Нет токена — просто пропускаем. Проверка прав будет в Depends.
            return await call_next(request)

        db = SessionLocal()
        try:
            token_data = verify_token(token)
            if token_data is None or not token_data.username:
                logger.warning(
                    "Invalid token received",
                    extra={"Path": path, "CorrelationId": getattr(request.state, "correlation_id", None)},
                )
                response = await call_next(request)
                response.headers["WWW-Authenticate"] = "Bearer"
                return response

            user = get_user_by_username(db, token_data.username)
            if user and user.is_active:
                request.state.user = user
                request.state.token_data = token_data
            else:
                logger.warning(
                    "Inactive or missing user for token",
                    extra={
                        "Path": path,
                        "Username": token_data.username,
                        "CorrelationId": getattr(request.state, "correlation_id", None),
                    },
                )
        finally:
            db.close()

        return await call_next(request)

    def _is_excluded(self, path: str) -> bool:
        return any(path.startswith(prefix) for prefix in self.exclude_paths)

    @staticmethod
    def _extract_token(request: Request) -> Optional[str]:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None
        if not auth_header.lower().startswith("bearer "):
            return None
        return auth_header[7:].strip()


