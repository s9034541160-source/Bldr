#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MOCKS FOR TESTING Bldr Empire
==============================

Система моков для тестирования компонентов Bldr
на основе паттернов из agents-towards-production.
"""

from typing import Dict, Any, List, Optional, Callable
from unittest.mock import Mock, MagicMock, AsyncMock
import asyncio
from datetime import datetime

from core.agents.base_agent import Task, TaskResult
from core.unified_tools_system import ToolResult

class MockToolsSystem:
    """Мок системы инструментов для тестирования"""
    
    def __init__(self):
        self.tools_registry = {}
        self.tools_methods = {}
        self.execution_stats = {}
        self.performance_metrics = {}
        self.async_executor = None
    
    def register_tool(self, name: str, func: Callable, **kwargs):
        """Регистрация мокового инструмента"""
        self.tools_methods[name] = func
    
    async def execute_tool_async(self, tool_name: str, **kwargs) -> ToolResult:
        """Моковое выполнение инструмента"""
        if tool_name not in self.tools_methods:
            return ToolResult(
                status="error",
                error=f"Tool {tool_name} not found",
                tool_name=tool_name
            )
        
        try:
            # Симулируем выполнение
            await asyncio.sleep(0.1)  # Имитация работы
            result = self.tools_methods[tool_name](**kwargs)
            
            return ToolResult(
                status="success",
                data=result,
                tool_name=tool_name
            )
        except Exception as e:
            return ToolResult(
                status="error",
                error=str(e),
                tool_name=tool_name
            )
    
    def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """Синхронное выполнение мокового инструмента"""
        if tool_name not in self.tools_methods:
            return ToolResult(
                status="error",
                error=f"Tool {tool_name} not found",
                tool_name=tool_name
            )
        
        try:
            result = self.tools_methods[tool_name](**kwargs)
            return ToolResult(
                status="success",
                data=result,
                tool_name=tool_name
            )
        except Exception as e:
            return ToolResult(
                status="error",
                error=str(e),
                tool_name=tool_name
            )

class MockNeo4jClient:
    """Мок Neo4j клиента для тестирования"""
    
    def __init__(self):
        self.data = {}
        self.queries = []
    
    def run(self, query: str, parameters: Dict[str, Any] = None):
        """Моковое выполнение запроса"""
        self.queries.append({"query": query, "parameters": parameters})
        
        # Симулируем разные типы запросов
        if "MATCH" in query.upper():
            return MockNeo4jResult(self._mock_match_query(query))
        elif "CREATE" in query.upper():
            return MockNeo4jResult(self._mock_create_query(query))
        elif "COUNT" in query.upper():
            return MockNeo4jResult(self._mock_count_query(query))
        else:
            return MockNeo4jResult([])
    
    def _mock_match_query(self, query: str) -> List[Dict[str, Any]]:
        """Моковое выполнение MATCH запроса"""
        return [
            {
                "title": "Тестовый документ",
                "content": "Тестовое содержимое",
                "source": "test_source",
                "doc_type": "norms",
                "metadata": {"sp_number": "123.456.789"}
            }
        ]
    
    def _mock_create_query(self, query: str) -> List[Dict[str, Any]]:
        """Моковое выполнение CREATE запроса"""
        return [{"id": "test_id", "created": True}]
    
    def _mock_count_query(self, query: str) -> List[Dict[str, Any]]:
        """Моковое выполнение COUNT запроса"""
        return [{"count": 42}]

class MockNeo4jResult:
    """Мок результата Neo4j запроса"""
    
    def __init__(self, data: List[Dict[str, Any]]):
        self.data = data
        self.index = 0
    
    def single(self) -> Optional[Dict[str, Any]]:
        """Возвращает один результат"""
        if self.data:
            return self.data[0]
        return None
    
    def data(self) -> List[Dict[str, Any]]:
        """Возвращает все данные"""
        return self.data
    
    def __iter__(self):
        return iter(self.data)
    
    def __next__(self):
        if self.index < len(self.data):
            result = self.data[self.index]
            self.index += 1
            return result
        raise StopIteration

class MockQdrantClient:
    """Мок Qdrant клиента для тестирования"""
    
    def __init__(self):
        self.collections = {}
        self.vectors = {}
    
    def search(self, collection_name: str, query_vector: List[float], limit: int = 10) -> Dict[str, Any]:
        """Моковое выполнение поиска"""
        return {
            "points": [
                {
                    "id": "test_id_1",
                    "score": 0.95,
                    "payload": {
                        "title": "Тестовый документ 1",
                        "content": "Тестовое содержимое 1",
                        "source": "test_source_1"
                    }
                },
                {
                    "id": "test_id_2", 
                    "score": 0.87,
                    "payload": {
                        "title": "Тестовый документ 2",
                        "content": "Тестовое содержимое 2",
                        "source": "test_source_2"
                    }
                }
            ]
        }
    
    def upsert(self, collection_name: str, points: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Моковое выполнение upsert"""
        if collection_name not in self.collections:
            self.collections[collection_name] = []
        
        self.collections[collection_name].extend(points)
        return {"status": "ok", "operation_id": "test_operation_id"}

class MockModelManager:
    """Мок менеджера моделей для тестирования"""
    
    def __init__(self):
        self.models = {}
        self.responses = {}
    
    def generate_response(self, prompt: str, model_name: str = "test_model") -> str:
        """Моковая генерация ответа"""
        if model_name in self.responses:
            return self.responses[model_name]
        
        # Стандартные ответы для разных типов промптов
        if "привет" in prompt.lower():
            return "Привет! Как дела?"
        elif "расскажи" in prompt.lower():
            return "Я тестовый агент системы Bldr Empire."
        elif "поиск" in prompt.lower():
            return "Найдено 3 результата по вашему запросу."
        else:
            return "Тестовый ответ на ваш запрос."
    
    def set_response(self, model_name: str, response: str):
        """Установка мокового ответа для модели"""
        self.responses[model_name] = response

class MockAgent(BaseAgent):
    """Мок агента для тестирования"""
    
    def __init__(self, name: str = "mock_agent", specialization: str = "testing"):
        super().__init__(name, specialization)
        self.mock_responses = {}
        self.execution_count = 0
    
    async def process(self, task: Task) -> TaskResult:
        """Моковая обработка задачи"""
        self.execution_count += 1
        
        # Имитируем задержку
        await asyncio.sleep(0.1)
        
        # Возвращаем моковый результат
        if task.id in self.mock_responses:
            result_data = self.mock_responses[task.id]
        else:
            result_data = f"Моковый результат для задачи: {task.description}"
        
        return TaskResult(
            task_id=task.id,
            success=True,
            result_data=result_data,
            metadata={"agent": self.name, "execution_count": self.execution_count}
        )
    
    def can_handle(self, task: Task) -> bool:
        """Моковая проверка способности обработки"""
        return True  # Мок может обработать любую задачу
    
    def get_capabilities(self) -> List[str]:
        """Моковые способности"""
        return ["Тестирование", "Моковая обработка", "Симуляция работы"]
    
    def set_mock_response(self, task_id: str, response: Any):
        """Установка мокового ответа для конкретной задачи"""
        self.mock_responses[task_id] = response

class MockAsyncExecutor:
    """Мок асинхронного исполнителя для тестирования"""
    
    def __init__(self):
        self.execution_times = {}
        self.failures = set()
    
    async def execute_with_retries(self, tool_func: Callable, tool_name: str, 
                                 kwargs: Dict[str, Any], timeout_seconds: Optional[int] = None) -> Any:
        """Моковое выполнение с повторами"""
        # Имитируем задержку
        await asyncio.sleep(0.1)
        
        # Проверяем, должен ли инструмент "упасть"
        if tool_name in self.failures:
            raise Exception(f"Моковая ошибка для инструмента {tool_name}")
        
        # Выполняем функцию
        return tool_func(**kwargs)
    
    async def execute_multiple_tools(self, tool_calls: List[Dict[str, Any]], 
                                   max_concurrent: int = 3) -> Dict[str, Any]:
        """Моковое параллельное выполнение"""
        results = {}
        
        for call in tool_calls:
            tool_name = call["name"]
            tool_func = call["func"]
            kwargs = call.get("kwargs", {})
            
            try:
                result = await self.execute_with_retries(
                    tool_func, tool_name, kwargs
                )
                results[tool_name] = {"status": "success", "result": result}
            except Exception as e:
                results[tool_name] = {"status": "error", "error": str(e)}
        
        return results
    
    def set_failure(self, tool_name: str):
        """Установка мокового сбоя для инструмента"""
        self.failures.add(tool_name)
    
    def clear_failures(self):
        """Очистка моковых сбоев"""
        self.failures.clear()

# Фабрика моков для удобного создания тестовых объектов
class MockFactory:
    """Фабрика для создания моковых объектов"""
    
    @staticmethod
    def create_tools_system() -> MockToolsSystem:
        """Создание моковой системы инструментов"""
        mock_system = MockToolsSystem()
        
        # Регистрируем несколько моковых инструментов
        mock_system.register_tool("search_rag_database", lambda query: f"Результаты поиска для: {query}")
        mock_system.register_tool("search_norms", lambda query: f"Нормативные документы для: {query}")
        mock_system.register_tool("estimate_cost", lambda query: f"Смета для: {query}")
        
        return mock_system
    
    @staticmethod
    def create_neo4j_client() -> MockNeo4jClient:
        """Создание мокового Neo4j клиента"""
        return MockNeo4jClient()
    
    @staticmethod
    def create_qdrant_client() -> MockQdrantClient:
        """Создание мокового Qdrant клиента"""
        return MockQdrantClient()
    
    @staticmethod
    def create_model_manager() -> MockModelManager:
        """Создание мокового менеджера моделей"""
        return MockModelManager()
    
    @staticmethod
    def create_agent(name: str = "mock_agent") -> MockAgent:
        """Создание мокового агента"""
        return MockAgent(name)
    
    @staticmethod
    def create_async_executor() -> MockAsyncExecutor:
        """Создание мокового асинхронного исполнителя"""
        return MockAsyncExecutor()
