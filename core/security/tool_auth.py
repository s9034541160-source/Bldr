#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SECURE TOOL CALLING FOR Bldr Empire
===================================

Система безопасности для инструментов на основе паттернов Arcade
из agents-towards-production.
"""

from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum
import hashlib
import time
from datetime import datetime, timedelta

from core.exceptions import ToolResourceError, ToolValidationError
from core.structured_logging import get_logger

logger = get_logger("tool_auth")

class AuthType(Enum):
    """Типы аутентификации для инструментов"""
    NONE = "none"  # Без аутентификации
    API_KEY = "api_key"  # API ключ
    OAUTH2 = "oauth2"  # OAuth2 токен
    USER_SESSION = "user_session"  # Пользовательская сессия
    ADMIN_ONLY = "admin_only"  # Только администратор

@dataclass
class ToolPermission:
    """Разрешение для инструмента"""
    tool_name: str
    auth_type: AuthType
    required_scopes: List[str] = None
    rate_limit: int = 100  # Запросов в час
    user_whitelist: List[str] = None  # Белый список пользователей
    admin_only: bool = False
    
    def __post_init__(self):
        if self.required_scopes is None:
            self.required_scopes = []
        if self.user_whitelist is None:
            self.user_whitelist = []

@dataclass
class UserContext:
    """Контекст пользователя"""
    user_id: str
    username: str
    roles: List[str]
    permissions: List[str]
    session_token: Optional[str] = None
    oauth_token: Optional[str] = None
    api_key: Optional[str] = None

class ToolAuthManager:
    """
    🚀 МЕНЕДЖЕР АУТЕНТИФИКАЦИИ ИНСТРУМЕНТОВ
    
    Управляет безопасностью доступа к инструментам:
    - Проверка разрешений пользователя
    - Валидация токенов
    - Rate limiting
    - Audit logging
    """
    
    def __init__(self):
        self.tool_permissions: Dict[str, ToolPermission] = {}
        self.user_sessions: Dict[str, UserContext] = {}
        self.rate_limits: Dict[str, Dict[str, Any]] = {}  # user_id -> {tool_name: {count, reset_time}}
        self.logger = get_logger("tool_auth")
    
    def register_tool_permission(self, permission: ToolPermission):
        """Регистрация разрешения для инструмента"""
        self.tool_permissions[permission.tool_name] = permission
        self.logger.log_agent_activity(
            agent_name="tool_auth",
            action="permission_registered",
            query="",
            result_status="success",
            context={
                "tool_name": permission.tool_name,
                "auth_type": permission.auth_type.value,
                "rate_limit": permission.rate_limit
            }
        )
    
    def authenticate_user(self, user_id: str, username: str, 
                        roles: List[str], permissions: List[str],
                        session_token: Optional[str] = None,
                        oauth_token: Optional[str] = None,
                        api_key: Optional[str] = None) -> UserContext:
        """Аутентификация пользователя"""
        user_context = UserContext(
            user_id=user_id,
            username=username,
            roles=roles,
            permissions=permissions,
            session_token=session_token,
            oauth_token=oauth_token,
            api_key=api_key
        )
        
        self.user_sessions[user_id] = user_context
        
        self.logger.log_agent_activity(
            agent_name="tool_auth",
            action="user_authenticated",
            query="",
            result_status="success",
            context={
                "user_id": user_id,
                "username": username,
                "roles": roles,
                "permissions_count": len(permissions)
            }
        )
        
        return user_context
    
    def check_tool_access(self, user_id: str, tool_name: str, 
                         additional_context: Optional[Dict[str, Any]] = None) -> bool:
        """
        🎯 ПРОВЕРКА ДОСТУПА К ИНСТРУМЕНТУ
        
        Args:
            user_id: ID пользователя
            tool_name: Имя инструмента
            additional_context: Дополнительный контекст
        
        Returns:
            True если доступ разрешен
        
        Raises:
            ToolResourceError: При отказе в доступе
        """
        # Проверяем существование инструмента
        if tool_name not in self.tool_permissions:
            # Инструмент без ограничений - разрешаем
            return True
        
        permission = self.tool_permissions[tool_name]
        
        # Проверяем сессию пользователя
        if user_id not in self.user_sessions:
            raise ToolResourceError(
                tool_name, "user_session", "Пользователь не аутентифицирован"
            )
        
        user_context = self.user_sessions[user_id]
        
        # Проверяем тип аутентификации
        if permission.auth_type == AuthType.NONE:
            return True
        
        elif permission.auth_type == AuthType.ADMIN_ONLY:
            if "admin" not in user_context.roles:
                raise ToolResourceError(
                    tool_name, "admin_required", "Требуются права администратора"
                )
        
        elif permission.auth_type == AuthType.API_KEY:
            if not user_context.api_key:
                raise ToolResourceError(
                    tool_name, "api_key_required", "Требуется API ключ"
                )
        
        elif permission.auth_type == AuthType.OAUTH2:
            if not user_context.oauth_token:
                raise ToolResourceError(
                    tool_name, "oauth_required", "Требуется OAuth2 токен"
                )
        
        elif permission.auth_type == AuthType.USER_SESSION:
            if not user_context.session_token:
                raise ToolResourceError(
                    tool_name, "session_required", "Требуется пользовательская сессия"
                )
        
        # Проверяем белый список
        if permission.user_whitelist and user_id not in permission.user_whitelist:
            raise ToolResourceError(
                tool_name, "whitelist_required", "Пользователь не в белом списке"
            )
        
        # Проверяем rate limiting
        if not self._check_rate_limit(user_id, tool_name, permission.rate_limit):
            raise ToolResourceError(
                tool_name, "rate_limit_exceeded", "Превышен лимит запросов"
            )
        
        # Логируем успешный доступ
        self.logger.log_agent_activity(
            agent_name="tool_auth",
            action="tool_access_granted",
            query=tool_name,
            result_status="success",
            context={
                "user_id": user_id,
                "tool_name": tool_name,
                "auth_type": permission.auth_type.value
            }
        )
        
        return True
    
    def _check_rate_limit(self, user_id: str, tool_name: str, rate_limit: int) -> bool:
        """Проверка rate limiting"""
        current_time = time.time()
        rate_key = f"{user_id}:{tool_name}"
        
        if rate_key not in self.rate_limits:
            self.rate_limits[rate_key] = {
                "count": 0,
                "reset_time": current_time + 3600  # Сброс через час
            }
        
        rate_data = self.rate_limits[rate_key]
        
        # Сброс счетчика если прошел час
        if current_time > rate_data["reset_time"]:
            rate_data["count"] = 0
            rate_data["reset_time"] = current_time + 3600
        
        # Проверяем лимит
        if rate_data["count"] >= rate_limit:
            return False
        
        # Увеличиваем счетчик
        rate_data["count"] += 1
        
        return True
    
    def get_user_permissions(self, user_id: str) -> List[str]:
        """Получение разрешений пользователя"""
        if user_id not in self.user_sessions:
            return []
        
        user_context = self.user_sessions[user_id]
        return user_context.permissions
    
    def revoke_user_session(self, user_id: str):
        """Отзыв пользовательской сессии"""
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
            self.logger.log_agent_activity(
                agent_name="tool_auth",
                action="session_revoked",
                query="",
                result_status="success",
                context={"user_id": user_id}
            )
    
    def get_tool_permissions_summary(self) -> Dict[str, Any]:
        """Получение сводки по разрешениям инструментов"""
        summary = {}
        
        for tool_name, permission in self.tool_permissions.items():
            summary[tool_name] = {
                "auth_type": permission.auth_type.value,
                "rate_limit": permission.rate_limit,
                "admin_only": permission.admin_only,
                "whitelist_size": len(permission.user_whitelist)
            }
        
        return summary

# Глобальный менеджер аутентификации
_global_auth_manager: Optional[ToolAuthManager] = None

def get_auth_manager() -> ToolAuthManager:
    """Получение глобального менеджера аутентификации"""
    global _global_auth_manager
    if _global_auth_manager is None:
        _global_auth_manager = ToolAuthManager()
    return _global_auth_manager
