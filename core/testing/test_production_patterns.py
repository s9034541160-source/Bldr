#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TESTS FOR PRODUCTION PATTERNS
==============================

Тесты для проверки production-ready паттернов Bldr Empire
на основе паттернов из agents-towards-production.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from typing import Dict, Any, List

from core.agents.base_agent import Task, TaskResult
from core.agents.specialized_agents import ChiefEngineerAgent, AnalystAgent, CoordinatorAgent
from core.agents.agent_manager import AgentManager
from core.exceptions import ToolValidationError, AgentExecutionError
from core.testing.mocks import MockFactory, MockToolsSystem, MockAsyncExecutor
from core.async_executor import AsyncToolExecutor, ExecutionConfig

class TestCustomExceptions:
    """Тесты кастомных исключений"""
    
    def test_tool_validation_error(self):
        """Тест ошибки валидации инструмента"""
        from core.exceptions import ToolValidationError
        
        error = ToolValidationError(
            tool_name="test_tool",
            parameter="query",
            value=123,
            expected_type="str"
        )
        
        assert error.tool_name == "test_tool"
        assert error.parameter == "query"
        assert error.value == 123
        assert error.expected_type == "str"
        assert "test_tool" in str(error)
    
    def test_agent_execution_error(self):
        """Тест ошибки выполнения агента"""
        from core.exceptions import AgentExecutionError
        
        error = AgentExecutionError(
            agent_name="test_agent",
            task="test_task",
            reason="Test reason"
        )
        
        assert error.agent_name == "test_agent"
        assert error.task == "test_task"
        assert error.reason == "Test reason"
        assert "test_agent" in str(error)

class TestAsyncExecutor:
    """Тесты асинхронного исполнителя"""
    
    @pytest.mark.asyncio
    async def test_execute_with_timeout_success(self):
        """Тест успешного выполнения с таймаутом"""
        executor = AsyncToolExecutor()
        
        async def test_func(x: int) -> int:
            await asyncio.sleep(0.1)
            return x * 2
        
        result = await executor.execute_with_timeout(
            tool_func=test_func,
            tool_name="test_tool",
            kwargs={"x": 5},
            timeout_seconds=1
        )
        
        assert result == 10
    
    @pytest.mark.asyncio
    async def test_execute_with_timeout_failure(self):
        """Тест сбоя по таймауту"""
        executor = AsyncToolExecutor()
        
        async def slow_func() -> str:
            await asyncio.sleep(2)  # Долгая операция
            return "done"
        
        with pytest.raises(Exception):  # ToolExecutionTimeoutError
            await executor.execute_with_timeout(
                tool_func=slow_func,
                tool_name="slow_tool",
                kwargs={},
                timeout_seconds=0.1
            )
    
    @pytest.mark.asyncio
    async def test_execute_with_retries(self):
        """Тест выполнения с повторами"""
        config = ExecutionConfig(max_retries=2, retry_delay=0.1)
        executor = AsyncToolExecutor(config)
        
        call_count = 0
        
        async def flaky_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        result = await executor.execute_with_retries(
            tool_func=flaky_func,
            tool_name="flaky_tool",
            kwargs={}
        )
        
        assert result == "success"
        assert call_count == 3  # 2 неудачи + 1 успех

class TestSpecializedAgents:
    """Тесты специализированных агентов"""
    
    @pytest.mark.asyncio
    async def test_chief_engineer_agent(self):
        """Тест агента главного инженера"""
        mock_tools = MockFactory.create_tools_system()
        agent = ChiefEngineerAgent(mock_tools)
        
        task = Task(
            id="test_1",
            description="Найди СП по земляным работам",
            input_data={"query": "земляные работы"}
        )
        
        result = await agent.execute_task(task)
        
        assert result.success
        assert result.task_id == "test_1"
        assert "agent" in result.metadata
    
    @pytest.mark.asyncio
    async def test_analyst_agent(self):
        """Тест агента аналитика"""
        mock_tools = MockFactory.create_tools_system()
        agent = AnalystAgent(mock_tools)
        
        task = Task(
            id="test_2",
            description="Рассчитай стоимость строительства",
            input_data={"query": "стоимость строительства"}
        )
        
        result = await agent.execute_task(task)
        
        assert result.success
        assert result.task_id == "test_2"
        assert "analyst" in result.metadata["agent"]
    
    @pytest.mark.asyncio
    async def test_coordinator_agent(self):
        """Тест агента координатора"""
        agent = CoordinatorAgent()
        
        task = Task(
            id="test_3",
            description="Привет, как дела?",
            input_data={}
        )
        
        result = await agent.execute_task(task)
        
        assert result.success
        assert result.task_id == "test_3"
        assert "Привет" in str(result.result_data)
    
    def test_agent_capabilities(self):
        """Тест способностей агентов"""
        mock_tools = MockFactory.create_tools_system()
        
        chief_engineer = ChiefEngineerAgent(mock_tools)
        analyst = AnalystAgent(mock_tools)
        coordinator = CoordinatorAgent()
        
        # Проверяем способности главного инженера
        assert "норма" in " ".join(chief_engineer.get_capabilities()).lower()
        assert "расчет" in " ".join(chief_engineer.get_capabilities()).lower()
        
        # Проверяем способности аналитика
        assert "смета" in " ".join(analyst.get_capabilities()).lower()
        assert "финанс" in " ".join(analyst.get_capabilities()).lower()
        
        # Проверяем способности координатора
        assert "планирование" in " ".join(coordinator.get_capabilities()).lower()
        assert "координация" in " ".join(coordinator.get_capabilities()).lower()

class TestAgentManager:
    """Тесты менеджера агентов"""
    
    @pytest.mark.asyncio
    async def test_agent_manager_initialization(self):
        """Тест инициализации менеджера агентов"""
        mock_tools = MockFactory.create_tools_system()
        manager = AgentManager(mock_tools)
        
        assert len(manager.agents) == 3
        assert "chief_engineer" in manager.agents
        assert "analyst" in manager.agents
        assert "coordinator" in manager.agents
    
    @pytest.mark.asyncio
    async def test_task_routing(self):
        """Тест маршрутизации задач"""
        mock_tools = MockFactory.create_tools_system()
        manager = AgentManager(mock_tools)
        
        # Техническая задача должна идти к главному инженеру
        tech_task = Task(
            id="tech_1",
            description="Найди нормативы по бетону",
            input_data={"query": "бетон"}
        )
        
        agent = manager.find_best_agent(tech_task)
        assert agent.name == "chief_engineer"
        
        # Финансовая задача должна идти к аналитику
        finance_task = Task(
            id="finance_1",
            description="Рассчитай стоимость проекта",
            input_data={"query": "стоимость"}
        )
        
        agent = manager.find_best_agent(finance_task)
        assert agent.name == "analyst"
        
        # Общая задача должна идти к координатору
        general_task = Task(
            id="general_1",
            description="Привет, как дела?",
            input_data={}
        )
        
        agent = manager.find_best_agent(general_task)
        assert agent.name == "coordinator"
    
    @pytest.mark.asyncio
    async def test_task_execution(self):
        """Тест выполнения задач"""
        mock_tools = MockFactory.create_tools_system()
        manager = AgentManager(mock_tools)
        
        task = Task(
            id="exec_1",
            description="Найди СП по фундаментам",
            input_data={"query": "фундаменты"}
        )
        
        result = await manager.execute_task(task)
        
        assert result.success
        assert result.task_id == "exec_1"
    
    @pytest.mark.asyncio
    async def test_parallel_task_execution(self):
        """Тест параллельного выполнения задач"""
        mock_tools = MockFactory.create_tools_system()
        manager = AgentManager(mock_tools)
        
        tasks = [
            Task(id="parallel_1", description="Найди СП по стенам", input_data={"query": "стены"}),
            Task(id="parallel_2", description="Рассчитай стоимость", input_data={"query": "стоимость"}),
            Task(id="parallel_3", description="Привет", input_data={})
        ]
        
        results = await manager.execute_multiple_tasks(tasks, max_concurrent=2)
        
        assert len(results) == 3
        assert all(result.success for result in results.values())
    
    def test_system_status(self):
        """Тест статуса системы"""
        mock_tools = MockFactory.create_tools_system()
        manager = AgentManager(mock_tools)
        
        status = manager.get_system_status()
        
        assert status["total_agents"] == 3
        assert status["available_agents"] == 3
        assert "agents" in status
        
        for agent_name in ["chief_engineer", "analyst", "coordinator"]:
            assert agent_name in status["agents"]
            assert "status" in status["agents"][agent_name]
            assert "performance" in status["agents"][agent_name]

class TestMocks:
    """Тесты моковых объектов"""
    
    def test_mock_tools_system(self):
        """Тест моковой системы инструментов"""
        mock_system = MockFactory.create_tools_system()
        
        # Проверяем регистрацию инструментов
        assert "search_rag_database" in mock_system.tools_methods
        assert "search_norms" in mock_system.tools_methods
        assert "estimate_cost" in mock_system.tools_methods
    
    @pytest.mark.asyncio
    async def test_mock_async_execution(self):
        """Тест мокового асинхронного выполнения"""
        mock_system = MockFactory.create_tools_system()
        
        result = await mock_system.execute_tool_async(
            "search_rag_database",
            query="test query"
        )
        
        assert result.status == "success"
        assert "test query" in str(result.data)
    
    def test_mock_neo4j_client(self):
        """Тест мокового Neo4j клиента"""
        mock_client = MockFactory.create_neo4j_client()
        
        result = mock_client.run("MATCH (n) RETURN n LIMIT 1")
        data = result.single()
        
        assert data is not None
        assert "title" in data
        assert "content" in data
    
    def test_mock_qdrant_client(self):
        """Тест мокового Qdrant клиента"""
        mock_client = MockFactory.create_qdrant_client()
        
        result = mock_client.search("test_collection", [0.1, 0.2, 0.3])
        
        assert "points" in result
        assert len(result["points"]) == 2
        assert "score" in result["points"][0]
        assert "payload" in result["points"][0]

class TestIntegration:
    """Интеграционные тесты"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Тест полного рабочего процесса"""
        # Создаем моковые компоненты
        mock_tools = MockFactory.create_tools_system()
        manager = AgentManager(mock_tools)
        
        # Создаем задачу
        task = Task(
            id="integration_1",
            description="Найди нормативы по железобетону и рассчитай стоимость",
            input_data={"query": "железобетон стоимость"}
        )
        
        # Выполняем задачу
        result = await manager.execute_task(task)
        
        # Проверяем результат
        assert result.success
        assert result.task_id == "integration_1"
        
        # Проверяем статус системы
        status = manager.get_system_status()
        assert status["total_agents"] == 3
        assert status["available_agents"] == 3
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Тест обработки ошибок"""
        mock_tools = MockFactory.create_tools_system()
        manager = AgentManager(mock_tools)
        
        # Создаем задачу, которая может вызвать ошибку
        task = Task(
            id="error_1",
            description="Неизвестная задача",
            input_data={}
        )
        
        # Выполняем задачу
        result = await manager.execute_task(task)
        
        # Проверяем, что система обработала ошибку корректно
        assert result.task_id == "error_1"
        # Результат может быть успешным (координатор обработал) или неуспешным (ошибка)

if __name__ == "__main__":
    # Запуск тестов
    pytest.main([__file__, "-v"])
