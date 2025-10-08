#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CUSTOM EXCEPTIONS FOR Bldr Empire
=================================

Иерархия кастомных исключений для умной обработки ошибок
на основе паттернов из agents-towards-production.
"""

from typing import Optional, Dict, Any
from datetime import datetime


class BldrBaseException(Exception):
    """Базовое исключение для всех ошибок Bldr"""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для логирования"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "context": self.context,
            "timestamp": self.timestamp
        }


# === ИСКЛЮЧЕНИЯ ДЛЯ ИНСТРУМЕНТОВ ===

class ToolException(BldrBaseException):
    """Базовое исключение для ошибок инструментов"""
    pass


class ToolValidationError(ToolException):
    """Ошибка валидации параметров инструмента"""
    
    def __init__(self, tool_name: str, parameter: str, value: Any, expected_type: str):
        message = f"Некорректный параметр '{parameter}' для инструмента '{tool_name}': ожидается {expected_type}, получен {type(value).__name__}"
        context = {
            "tool_name": tool_name,
            "parameter": parameter,
            "value": str(value),
            "expected_type": expected_type
        }
        super().__init__(message, context)


class ToolDependencyError(ToolException):
    """Ошибка зависимостей инструмента"""
    
    def __init__(self, tool_name: str, dependency: str, reason: str):
        message = f"Инструмент '{tool_name}' недоступен: {dependency} - {reason}"
        context = {
            "tool_name": tool_name,
            "dependency": dependency,
            "reason": reason
        }
        super().__init__(message, context)


class ToolExecutionTimeoutError(ToolException):
    """Таймаут выполнения инструмента"""
    
    def __init__(self, tool_name: str, timeout_seconds: int):
        message = f"Инструмент '{tool_name}' превысил лимит времени {timeout_seconds}с"
        context = {
            "tool_name": tool_name,
            "timeout_seconds": timeout_seconds
        }
        super().__init__(message, context)


class ToolResourceError(ToolException):
    """Ошибка ресурсов для инструмента"""
    
    def __init__(self, tool_name: str, resource: str, reason: str):
        message = f"Инструмент '{tool_name}' не может получить доступ к ресурсу '{resource}': {reason}"
        context = {
            "tool_name": tool_name,
            "resource": resource,
            "reason": reason
        }
        super().__init__(message, context)


# === ИСКЛЮЧЕНИЯ ДЛЯ АГЕНТОВ ===

class AgentException(BldrBaseException):
    """Базовое исключение для ошибок агентов"""
    pass


class AgentPlanningError(AgentException):
    """Ошибка планирования агента"""
    
    def __init__(self, agent_name: str, query: str, reason: str):
        message = f"Агент '{agent_name}' не может спланировать выполнение запроса: {reason}"
        context = {
            "agent_name": agent_name,
            "query": query,
            "reason": reason
        }
        super().__init__(message, context)


class AgentExecutionError(AgentException):
    """Ошибка выполнения агента"""
    
    def __init__(self, agent_name: str, task: str, reason: str):
        message = f"Агент '{agent_name}' не может выполнить задачу '{task}': {reason}"
        context = {
            "agent_name": agent_name,
            "task": task,
            "reason": reason
        }
        super().__init__(message, context)


class AgentCommunicationError(AgentException):
    """Ошибка коммуникации между агентами"""
    
    def __init__(self, from_agent: str, to_agent: str, reason: str):
        message = f"Ошибка коммуникации от '{from_agent}' к '{to_agent}': {reason}"
        context = {
            "from_agent": from_agent,
            "to_agent": to_agent,
            "reason": reason
        }
        super().__init__(message, context)


# === ИСКЛЮЧЕНИЯ ДЛЯ RAG СИСТЕМЫ ===

class RAGException(BldrBaseException):
    """Базовое исключение для ошибок RAG системы"""
    pass


class RAGQueryError(RAGException):
    """Ошибка запроса к RAG системе"""
    
    def __init__(self, query: str, reason: str):
        message = f"Ошибка обработки запроса к RAG: {reason}"
        context = {
            "query": query,
            "reason": reason
        }
        super().__init__(message, context)


class RAGIndexError(RAGException):
    """Ошибка индекса RAG системы"""
    
    def __init__(self, operation: str, reason: str):
        message = f"Ошибка индекса RAG при операции '{operation}': {reason}"
        context = {
            "operation": operation,
            "reason": reason
        }
        super().__init__(message, context)


# === ИСКЛЮЧЕНИЯ ДЛЯ БАЗ ДАННЫХ ===

class DatabaseException(BldrBaseException):
    """Базовое исключение для ошибок баз данных"""
    pass


class Neo4jConnectionError(DatabaseException):
    """Ошибка подключения к Neo4j"""
    
    def __init__(self, reason: str):
        message = f"Не удается подключиться к Neo4j: {reason}"
        context = {"reason": reason}
        super().__init__(message, context)


class QdrantConnectionError(DatabaseException):
    """Ошибка подключения к Qdrant"""
    
    def __init__(self, reason: str):
        message = f"Не удается подключиться к Qdrant: {reason}"
        context = {"reason": reason}
        super().__init__(message, context)


# === ИСКЛЮЧЕНИЯ ДЛЯ LLM ===

class LLMException(BldrBaseException):
    """Базовое исключение для ошибок LLM"""
    pass


class LLMTimeoutError(LLMException):
    """Таймаут LLM запроса"""
    
    def __init__(self, model: str, timeout_seconds: int):
        message = f"LLM '{model}' превысил лимит времени {timeout_seconds}с"
        context = {
            "model": model,
            "timeout_seconds": timeout_seconds
        }
        super().__init__(message, context)


class LLMResponseError(LLMException):
    """Ошибка ответа LLM"""
    
    def __init__(self, model: str, reason: str):
        message = f"LLM '{model}' вернул некорректный ответ: {reason}"
        context = {
            "model": model,
            "reason": reason
        }
        super().__init__(message, context)


# === УТИЛИТЫ ДЛЯ ОБРАБОТКИ ИСКЛЮЧЕНИЙ ===

def get_error_category(exception: Exception) -> str:
    """Определяем категорию ошибки для умной обработки"""
    if isinstance(exception, ToolValidationError):
        return "validation_error"
    elif isinstance(exception, ToolDependencyError):
        return "dependency_error"
    elif isinstance(exception, ToolExecutionTimeoutError):
        return "timeout_error"
    elif isinstance(exception, ToolResourceError):
        return "resource_error"
    elif isinstance(exception, AgentPlanningError):
        return "planning_error"
    elif isinstance(exception, AgentExecutionError):
        return "execution_error"
    elif isinstance(exception, AgentCommunicationError):
        return "communication_error"
    elif isinstance(exception, RAGQueryError):
        return "rag_query_error"
    elif isinstance(exception, RAGIndexError):
        return "rag_index_error"
    elif isinstance(exception, (Neo4jConnectionError, QdrantConnectionError)):
        return "database_error"
    elif isinstance(exception, (LLMTimeoutError, LLMResponseError)):
        return "llm_error"
    else:
        return "unknown_error"


def get_user_friendly_message(exception: Exception) -> str:
    """Получаем понятное пользователю сообщение об ошибке"""
    category = get_error_category(exception)
    
    messages = {
        "validation_error": "Проверьте правильность введенных параметров",
        "dependency_error": "Недоступен необходимый сервис, попробуйте позже",
        "timeout_error": "Операция заняла слишком много времени, попробуйте еще раз",
        "resource_error": "Недоступен необходимый ресурс, попробуйте позже",
        "planning_error": "Не удается спланировать выполнение запроса, попробуйте переформулировать",
        "execution_error": "Ошибка выполнения задачи, попробуйте еще раз",
        "communication_error": "Ошибка связи между компонентами системы",
        "rag_query_error": "Ошибка поиска в базе знаний, попробуйте другой запрос",
        "rag_index_error": "Ошибка индекса базы знаний, обратитесь к администратору",
        "database_error": "Ошибка базы данных, попробуйте позже",
        "llm_error": "Ошибка обработки запроса, попробуйте еще раз",
        "unknown_error": "Произошла неизвестная ошибка, попробуйте еще раз"
    }
    
    return messages.get(category, "Произошла ошибка, попробуйте еще раз")
