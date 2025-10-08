#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ASYNC EXECUTOR FOR Bldr Empire
==============================

Асинхронная система выполнения инструментов с таймаутами
на основе паттернов из agents-towards-production.
"""

import asyncio
import time
from typing import Dict, Any, Optional, Callable, Union
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass
import logging

from core.exceptions import ToolExecutionTimeoutError, ToolResourceError
from core.structured_logging import get_logger

logger = get_logger("async_executor")

@dataclass
class ExecutionConfig:
    """Конфигурация выполнения инструмента"""
    timeout_seconds: int = 30
    max_retries: int = 2
    retry_delay: float = 1.0
    use_thread_pool: bool = True
    thread_pool_size: int = 4

class AsyncToolExecutor:
    """Асинхронный исполнитель инструментов с таймаутами"""
    
    def __init__(self, config: Optional[ExecutionConfig] = None):
        self.config = config or ExecutionConfig()
        self.thread_pool = ThreadPoolExecutor(max_workers=self.config.thread_pool_size)
        self.logger = get_logger("async_executor")
    
    async def execute_with_timeout(self, 
                                 tool_func: Callable, 
                                 tool_name: str,
                                 kwargs: Dict[str, Any],
                                 timeout_seconds: Optional[int] = None) -> Any:
        """
        🚀 АСИНХРОННОЕ ВЫПОЛНЕНИЕ С ТАЙМАУТОМ
        
        Args:
            tool_func: Функция инструмента
            tool_name: Имя инструмента
            kwargs: Параметры
            timeout_seconds: Таймаут (по умолчанию из конфигурации)
        
        Returns:
            Результат выполнения инструмента
        
        Raises:
            ToolExecutionTimeoutError: При превышении таймаута
        """
        timeout = timeout_seconds or self.config.timeout_seconds
        start_time = time.time()
        
        try:
            self.logger.log_tool_execution(
                tool_name=tool_name,
                status="started",
                duration_ms=0,
                context={"timeout_seconds": timeout}
            )
            
            if self.config.use_thread_pool:
                # Выполняем в отдельном потоке
                result = await asyncio.wait_for(
                    self._run_in_thread(tool_func, kwargs),
                    timeout=timeout
                )
            else:
                # Выполняем напрямую (для простых функций)
                result = await asyncio.wait_for(
                    self._run_async(tool_func, kwargs),
                    timeout=timeout
                )
            
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_tool_execution(
                tool_name=tool_name,
                status="completed",
                duration_ms=execution_time,
                context={"result_type": type(result).__name__}
            )
            
            return result
            
        except asyncio.TimeoutError:
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_tool_execution(
                tool_name=tool_name,
                status="timeout",
                duration_ms=execution_time,
                context={"timeout_seconds": timeout}
            )
            raise ToolExecutionTimeoutError(tool_name, timeout)
        
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_tool_execution(
                tool_name=tool_name,
                status="error",
                duration_ms=execution_time,
                context={"error": str(e)}
            )
            raise
    
    async def _run_in_thread(self, func: Callable, kwargs: Dict[str, Any]) -> Any:
        """Запуск функции в отдельном потоке"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.thread_pool, func, **kwargs)
    
    async def _run_async(self, func: Callable, kwargs: Dict[str, Any]) -> Any:
        """Запуск асинхронной функции"""
        if asyncio.iscoroutinefunction(func):
            return await func(**kwargs)
        else:
            # Синхронная функция в асинхронном контексте
            return func(**kwargs)
    
    async def execute_with_retries(self,
                                 tool_func: Callable,
                                 tool_name: str,
                                 kwargs: Dict[str, Any],
                                 timeout_seconds: Optional[int] = None) -> Any:
        """
        🚀 ВЫПОЛНЕНИЕ С ПОВТОРНЫМИ ПОПЫТКАМИ
        
        Args:
            tool_func: Функция инструмента
            tool_name: Имя инструмента
            kwargs: Параметры
            timeout_seconds: Таймаут
        
        Returns:
            Результат выполнения
        
        Raises:
            ToolExecutionTimeoutError: При исчерпании попыток
        """
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                if attempt > 0:
                    # Задержка перед повтором
                    await asyncio.sleep(self.config.retry_delay * attempt)
                    self.logger.log_tool_execution(
                        tool_name=tool_name,
                        status="retry",
                        duration_ms=0,
                        context={"attempt": attempt + 1, "max_retries": self.config.max_retries}
                    )
                
                return await self.execute_with_timeout(
                    tool_func, tool_name, kwargs, timeout_seconds
                )
                
            except ToolExecutionTimeoutError as e:
                last_exception = e
                if attempt == self.config.max_retries:
                    self.logger.log_tool_execution(
                        tool_name=tool_name,
                        status="failed_after_retries",
                        duration_ms=0,
                        context={"attempts": attempt + 1, "max_retries": self.config.max_retries}
                    )
                    raise e
            
            except Exception as e:
                last_exception = e
                if attempt == self.config.max_retries:
                    self.logger.log_tool_execution(
                        tool_name=tool_name,
                        status="failed_after_retries",
                        duration_ms=0,
                        context={"attempts": attempt + 1, "error": str(e)}
                    )
                    raise e
        
        # Этот код не должен выполняться, но на всякий случай
        if last_exception:
            raise last_exception
    
    async def execute_multiple_tools(self,
                                   tool_calls: list,
                                   max_concurrent: int = 3) -> Dict[str, Any]:
        """
        🚀 ПАРАЛЛЕЛЬНОЕ ВЫПОЛНЕНИЕ НЕСКОЛЬКИХ ИНСТРУМЕНТОВ
        
        Args:
            tool_calls: Список вызовов инструментов
            max_concurrent: Максимальное количество одновременных выполнений
        
        Returns:
            Словарь с результатами выполнения
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results = {}
        
        async def execute_single_tool(tool_call):
            async with semaphore:
                tool_name = tool_call["name"]
                tool_func = tool_call["func"]
                kwargs = tool_call.get("kwargs", {})
                timeout = tool_call.get("timeout")
                
                try:
                    result = await self.execute_with_retries(
                        tool_func, tool_name, kwargs, timeout
                    )
                    return tool_name, {"status": "success", "result": result}
                except Exception as e:
                    return tool_name, {"status": "error", "error": str(e)}
        
        # Запускаем все инструменты параллельно
        tasks = [execute_single_tool(tool_call) for tool_call in tool_calls]
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Собираем результаты
        for task_result in completed_tasks:
            if isinstance(task_result, Exception):
                self.logger.log_error(task_result, {"context": "parallel_execution"})
            else:
                tool_name, result = task_result
                results[tool_name] = result
        
        return results
    
    def close(self):
        """Закрытие пула потоков"""
        self.thread_pool.shutdown(wait=True)


# Глобальный экземпляр исполнителя
_global_executor: Optional[AsyncToolExecutor] = None

def get_async_executor() -> AsyncToolExecutor:
    """Получение глобального асинхронного исполнителя"""
    global _global_executor
    if _global_executor is None:
        _global_executor = AsyncToolExecutor()
    return _global_executor

def close_async_executor():
    """Закрытие глобального исполнителя"""
    global _global_executor
    if _global_executor:
        _global_executor.close()
        _global_executor = None
