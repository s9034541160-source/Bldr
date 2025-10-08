#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STRUCTURED LOGGING FOR Bldr Empire
==================================

Структурированное логирование в формате JSON для анализа производительности
на основе паттернов из agents-towards-production.
"""

import json
import logging
import traceback
from typing import Dict, Any, Optional, Union
from datetime import datetime
from pathlib import Path
import sys


class StructuredFormatter(logging.Formatter):
    """Форматтер для структурированного логирования в JSON"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Форматирование записи в JSON"""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Добавляем контекст если есть
        if hasattr(record, 'context'):
            log_entry["context"] = record.context
        
        # Добавляем метрики если есть
        if hasattr(record, 'metrics'):
            log_entry["metrics"] = record.metrics
        
        # Добавляем трассировку для ошибок
        if record.levelno >= logging.ERROR and record.exc_info:
            log_entry["traceback"] = traceback.format_exception(*record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False, indent=None)


class BldrLogger:
    """Структурированный логгер для Bldr Empire"""
    
    def __init__(self, name: str, log_file: Optional[str] = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Убираем существующие обработчики
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Консольный вывод
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(console_handler)
        
        # Файловый вывод
        if log_file:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(StructuredFormatter())
            self.logger.addHandler(file_handler)
    
    def log_tool_execution(self, tool_name: str, status: str, duration_ms: float, 
                          context: Optional[Dict[str, Any]] = None):
        """Логирование выполнения инструмента"""
        self.logger.info(
            f"Tool execution: {tool_name}",
            extra={
                "context": {
                    "tool_name": tool_name,
                    "status": status,
                    "duration_ms": duration_ms,
                    **(context or {})
                }
            }
        )
    
    def log_agent_activity(self, agent_name: str, action: str, 
                           query: str, result_status: str, 
                           context: Optional[Dict[str, Any]] = None):
        """Логирование активности агента"""
        self.logger.info(
            f"Agent activity: {agent_name} - {action}",
            extra={
                "context": {
                    "agent_name": agent_name,
                    "action": action,
                    "query": query[:100] + "..." if len(query) > 100 else query,
                    "result_status": result_status,
                    **(context or {})
                }
            }
        )
    
    def log_rag_query(self, query: str, results_count: int, 
                     execution_time_ms: float, context: Optional[Dict[str, Any]] = None):
        """Логирование запроса к RAG системе"""
        self.logger.info(
            f"RAG query executed",
            extra={
                "context": {
                    "query": query[:100] + "..." if len(query) > 100 else query,
                    "results_count": results_count,
                    "execution_time_ms": execution_time_ms,
                    **(context or {})
                }
            }
        )
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Логирование ошибки с контекстом"""
        self.logger.error(
            f"Error occurred: {str(error)}",
            extra={
                "context": {
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                    **(context or {})
                }
            },
            exc_info=True
        )
    
    def log_performance_metric(self, metric_name: str, value: Union[int, float], 
                              unit: str, context: Optional[Dict[str, Any]] = None):
        """Логирование метрики производительности"""
        self.logger.info(
            f"Performance metric: {metric_name}",
            extra={
                "metrics": {
                    "metric_name": metric_name,
                    "value": value,
                    "unit": unit,
                    **(context or {})
                }
            }
        )
    
    def log_benchmark_result(self, test_name: str, success: bool, 
                            execution_time: float, accuracy: float,
                            context: Optional[Dict[str, Any]] = None):
        """Логирование результата бенчмарка"""
        self.logger.info(
            f"Benchmark result: {test_name}",
            extra={
                "context": {
                    "test_name": test_name,
                    "success": success,
                    "execution_time": execution_time,
                    "accuracy": accuracy,
                    **(context or {})
                }
            }
        )


# Глобальные логгеры для разных компонентов
coordinator_logger = BldrLogger("coordinator", "logs/coordinator.json")
tools_logger = BldrLogger("tools", "logs/tools.json")
rag_logger = BldrLogger("rag", "logs/rag.json")
benchmark_logger = BldrLogger("benchmark", "logs/benchmark.json")


def get_logger(component: str) -> BldrLogger:
    """Получение логгера для компонента"""
    loggers = {
        "coordinator": coordinator_logger,
        "tools": tools_logger,
        "rag": rag_logger,
        "benchmark": benchmark_logger
    }
    return loggers.get(component, BldrLogger(component))
