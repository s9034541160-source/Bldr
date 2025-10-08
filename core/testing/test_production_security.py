#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TESTS FOR PRODUCTION SECURITY PATTERNS
======================================

Тесты для проверки production-ready паттернов безопасности Bldr Empire
на основе паттернов из agents-towards-production.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from typing import Dict, Any, List

from core.security.tool_auth import ToolAuthManager, ToolPermission, AuthType, UserContext
from core.memory.dual_memory import DualMemorySystem, MemoryEntry, InMemoryBackend
from core.testing.mocks import MockFactory

class TestToolAuthManager:
    """Тесты менеджера аутентификации инструментов"""
    
    def test_auth_manager_initialization(self):
        """Тест инициализации менеджера аутентификации"""
        auth_manager = ToolAuthManager()
        
        assert auth_manager.tool_permissions == {}
        assert auth_manager.user_sessions == {}
        assert auth_manager.rate_limits == {}
    
    def test_register_tool_permission(self):
        """Тест регистрации разрешения для инструмента"""
        auth_manager = ToolAuthManager()
        
        permission = ToolPermission(
            tool_name="test_tool",
            auth_type=AuthType.API_KEY,
            rate_limit=50
        )
        
        auth_manager.register_tool_permission(permission)
        
        assert "test_tool" in auth_manager.tool_permissions
        assert auth_manager.tool_permissions["test_tool"].auth_type == AuthType.API_KEY
        assert auth_manager.tool_permissions["test_tool"].rate_limit == 50
    
    def test_authenticate_user(self):
        """Тест аутентификации пользователя"""
        auth_manager = ToolAuthManager()
        
        user_context = auth_manager.authenticate_user(
            user_id="test_user",
            username="test_user",
            roles=["user"],
            permissions=["read", "write"],
            api_key="test_key"
        )
        
        assert user_context.user_id == "test_user"
        assert user_context.username == "test_user"
        assert "user" in user_context.roles
        assert "read" in user_context.permissions
        assert user_context.api_key == "test_key"
        assert "test_user" in auth_manager.user_sessions
    
    def test_check_tool_access_no_permission(self):
        """Тест проверки доступа к инструменту без ограничений"""
        auth_manager = ToolAuthManager()
        
        # Аутентифицируем пользователя
        auth_manager.authenticate_user(
            user_id="test_user",
            username="test_user",
            roles=["user"],
            permissions=["read"]
        )
        
        # Инструмент без ограничений должен быть доступен
        has_access = auth_manager.check_tool_access("test_user", "unrestricted_tool")
        assert has_access is True
    
    def test_check_tool_access_with_permission(self):
        """Тест проверки доступа к инструменту с ограничениями"""
        auth_manager = ToolAuthManager()
        
        # Регистрируем разрешение
        permission = ToolPermission(
            tool_name="restricted_tool",
            auth_type=AuthType.API_KEY,
            rate_limit=10
        )
        auth_manager.register_tool_permission(permission)
        
        # Аутентифицируем пользователя с API ключом
        auth_manager.authenticate_user(
            user_id="test_user",
            username="test_user",
            roles=["user"],
            permissions=["read"],
            api_key="test_key"
        )
        
        # Проверяем доступ
        has_access = auth_manager.check_tool_access("test_user", "restricted_tool")
        assert has_access is True
    
    def test_check_tool_access_admin_only(self):
        """Тест проверки доступа к инструменту только для администраторов"""
        auth_manager = ToolAuthManager()
        
        # Регистрируем разрешение только для админов
        permission = ToolPermission(
            tool_name="admin_tool",
            auth_type=AuthType.ADMIN_ONLY,
            rate_limit=10
        )
        auth_manager.register_tool_permission(permission)
        
        # Аутентифицируем обычного пользователя
        auth_manager.authenticate_user(
            user_id="regular_user",
            username="regular_user",
            roles=["user"],
            permissions=["read"]
        )
        
        # Проверяем доступ - должен быть запрещен
        with pytest.raises(Exception):  # ToolResourceError
            auth_manager.check_tool_access("regular_user", "admin_tool")
        
        # Аутентифицируем администратора
        auth_manager.authenticate_user(
            user_id="admin_user",
            username="admin_user",
            roles=["admin"],
            permissions=["admin"]
        )
        
        # Проверяем доступ - должен быть разрешен
        has_access = auth_manager.check_tool_access("admin_user", "admin_tool")
        assert has_access is True
    
    def test_rate_limiting(self):
        """Тест rate limiting"""
        auth_manager = ToolAuthManager()
        
        # Регистрируем разрешение с низким лимитом
        permission = ToolPermission(
            tool_name="rate_limited_tool",
            auth_type=AuthType.NONE,
            rate_limit=2  # Только 2 запроса в час
        )
        auth_manager.register_tool_permission(permission)
        
        # Аутентифицируем пользователя
        auth_manager.authenticate_user(
            user_id="test_user",
            username="test_user",
            roles=["user"],
            permissions=["read"]
        )
        
        # Первые два запроса должны пройти
        assert auth_manager.check_tool_access("test_user", "rate_limited_tool") is True
        assert auth_manager.check_tool_access("test_user", "rate_limited_tool") is True
        
        # Третий запрос должен быть заблокирован
        with pytest.raises(Exception):  # ToolResourceError
            auth_manager.check_tool_access("test_user", "rate_limited_tool")
    
    def test_revoke_user_session(self):
        """Тест отзыва пользовательской сессии"""
        auth_manager = ToolAuthManager()
        
        # Аутентифицируем пользователя
        auth_manager.authenticate_user(
            user_id="test_user",
            username="test_user",
            roles=["user"],
            permissions=["read"]
        )
        
        assert "test_user" in auth_manager.user_sessions
        
        # Отзываем сессию
        auth_manager.revoke_user_session("test_user")
        
        assert "test_user" not in auth_manager.user_sessions

class TestDualMemorySystem:
    """Тесты системы двойной памяти"""
    
    @pytest.mark.asyncio
    async def test_memory_system_initialization(self):
        """Тест инициализации системы памяти"""
        memory_system = DualMemorySystem()
        
        assert memory_system.short_term_backend is not None
        assert memory_system.long_term_backend is not None
        assert memory_system.short_term_max_size == 1000
        assert memory_system.long_term_importance_threshold == 0.7
    
    @pytest.mark.asyncio
    async def test_store_memory_short_term(self):
        """Тест сохранения в краткосрочную память"""
        memory_system = DualMemorySystem()
        
        entry_id = await memory_system.store_memory(
            content="Test content for short-term memory",
            metadata={"test": "data"},
            tags=["test", "short-term"],
            importance_score=0.3  # Низкая важность
        )
        
        assert entry_id is not None
        assert len(entry_id) == 16  # MD5 hash length
    
    @pytest.mark.asyncio
    async def test_store_memory_long_term(self):
        """Тест сохранения в долгосрочную память"""
        memory_system = DualMemorySystem()
        
        entry_id = await memory_system.store_memory(
            content="Important content for long-term memory",
            metadata={"important": "data"},
            tags=["test", "long-term"],
            importance_score=0.8  # Высокая важность
        )
        
        assert entry_id is not None
        assert len(entry_id) == 16
    
    @pytest.mark.asyncio
    async def test_retrieve_memory(self):
        """Тест поиска в памяти"""
        memory_system = DualMemorySystem()
        
        # Сохраняем несколько записей
        await memory_system.store_memory(
            content="First test content",
            tags=["test1"],
            importance_score=0.5
        )
        
        await memory_system.store_memory(
            content="Second test content",
            tags=["test2"],
            importance_score=0.6
        )
        
        # Ищем записи
        results = await memory_system.retrieve_memory("test", limit=5)
        
        assert len(results) >= 2
        assert any("First test content" in entry.content for entry in results)
        assert any("Second test content" in entry.content for entry in results)
    
    @pytest.mark.asyncio
    async def test_update_memory(self):
        """Тест обновления записи в памяти"""
        memory_system = DualMemorySystem()
        
        # Сохраняем запись
        entry_id = await memory_system.store_memory(
            content="Original content",
            tags=["original"],
            importance_score=0.5
        )
        
        # Обновляем запись
        updated = await memory_system.update_memory(
            entry_id=entry_id,
            content="Updated content",
            importance_score=0.8
        )
        
        assert updated is True
    
    @pytest.mark.asyncio
    async def test_memory_stats(self):
        """Тест получения статистики памяти"""
        memory_system = DualMemorySystem()
        
        stats = await memory_system.get_memory_stats()
        
        assert "short_term_backend" in stats
        assert "long_term_backend" in stats
        assert "short_term_max_size" in stats
        assert "long_term_threshold" in stats

class TestMemoryEntry:
    """Тесты записи памяти"""
    
    def test_memory_entry_creation(self):
        """Тест создания записи памяти"""
        entry = MemoryEntry(
            id="test_id",
            content="Test content",
            metadata={"test": "data"},
            tags=["test"]
        )
        
        assert entry.id == "test_id"
        assert entry.content == "Test content"
        assert entry.metadata["test"] == "data"
        assert "test" in entry.tags
        assert entry.access_count == 0
        assert entry.importance_score == 0.0
    
    def test_memory_entry_to_dict(self):
        """Тест конвертации записи в словарь"""
        entry = MemoryEntry(
            id="test_id",
            content="Test content",
            metadata={"test": "data"},
            tags=["test"]
        )
        
        data = entry.to_dict()
        
        assert data["id"] == "test_id"
        assert data["content"] == "Test content"
        assert data["metadata"]["test"] == "data"
        assert "test" in data["tags"]
        assert "timestamp" in data
    
    def test_memory_entry_from_dict(self):
        """Тест создания записи из словаря"""
        data = {
            "id": "test_id",
            "content": "Test content",
            "metadata": {"test": "data"},
            "timestamp": "2025-09-28T16:00:00",
            "access_count": 5,
            "importance_score": 0.8,
            "tags": ["test"]
        }
        
        entry = MemoryEntry.from_dict(data)
        
        assert entry.id == "test_id"
        assert entry.content == "Test content"
        assert entry.metadata["test"] == "data"
        assert entry.access_count == 5
        assert entry.importance_score == 0.8
        assert "test" in entry.tags

class TestIntegration:
    """Интеграционные тесты"""
    
    @pytest.mark.asyncio
    async def test_auth_and_memory_integration(self):
        """Тест интеграции аутентификации и памяти"""
        # Создаем менеджер аутентификации
        auth_manager = ToolAuthManager()
        
        # Регистрируем разрешение
        permission = ToolPermission(
            tool_name="memory_tool",
            auth_type=AuthType.USER_SESSION,
            rate_limit=10
        )
        auth_manager.register_tool_permission(permission)
        
        # Аутентифицируем пользователя
        auth_manager.authenticate_user(
            user_id="test_user",
            username="test_user",
            roles=["user"],
            permissions=["read"],
            session_token="test_session"
        )
        
        # Проверяем доступ
        has_access = auth_manager.check_tool_access("test_user", "memory_tool")
        assert has_access is True
        
        # Создаем систему памяти
        memory_system = DualMemorySystem()
        
        # Сохраняем информацию о выполнении
        entry_id = await memory_system.store_memory(
            content="Tool memory_tool executed by user test_user",
            metadata={
                "tool_name": "memory_tool",
                "user_id": "test_user",
                "timestamp": "2025-09-28T16:00:00"
            },
            tags=["tool_execution", "memory_tool"],
            importance_score=0.5
        )
        
        assert entry_id is not None
        
        # Ищем в памяти
        results = await memory_system.retrieve_memory("memory_tool", limit=5)
        assert len(results) >= 1
        assert any("memory_tool" in entry.content for entry in results)
    
    def test_permissions_summary(self):
        """Тест получения сводки по разрешениям"""
        auth_manager = ToolAuthManager()
        
        # Регистрируем несколько разрешений
        permission1 = ToolPermission(
            tool_name="tool1",
            auth_type=AuthType.API_KEY,
            rate_limit=50
        )
        permission2 = ToolPermission(
            tool_name="tool2",
            auth_type=AuthType.ADMIN_ONLY,
            rate_limit=10
        )
        
        auth_manager.register_tool_permission(permission1)
        auth_manager.register_tool_permission(permission2)
        
        # Получаем сводку
        summary = auth_manager.get_tool_permissions_summary()
        
        assert len(summary) == 2
        assert "tool1" in summary
        assert "tool2" in summary
        assert summary["tool1"]["auth_type"] == "api_key"
        assert summary["tool2"]["auth_type"] == "admin_only"

if __name__ == "__main__":
    # Запуск тестов
    pytest.main([__file__, "-v"])
