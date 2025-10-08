#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BENCHMARK API FOR Bldr
======================

API endpoints для запуска бенчмарков и получения метрик производительности.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
import logging

# Импорты для интеграции с основной системой
try:
    from core.agents.benchmark_integration import BenchmarkIntegration
    from core.agents.coordinator_agent import CoordinatorAgent
    from core.unified_tools_system import UnifiedToolsSystem
except ImportError as e:
    logging.warning(f"Не удалось импортировать модули бенчмарков: {e}")
    BenchmarkIntegration = None

logger = logging.getLogger(__name__)

# Создаем роутер
router = APIRouter(prefix="/benchmark", tags=["benchmark"])

# Глобальные переменные для интеграции
benchmark_integration: Optional[BenchmarkIntegration] = None

def get_benchmark_integration() -> BenchmarkIntegration:
    """Получение экземпляра интеграции бенчмарков"""
    global benchmark_integration
    if benchmark_integration is None:
        # Инициализируем интеграцию
        coordinator = CoordinatorAgent()
        tools_system = UnifiedToolsSystem()
        benchmark_integration = BenchmarkIntegration(coordinator, tools_system)
    return benchmark_integration

@router.get("/status")
async def get_benchmark_status():
    """Получение статуса системы бенчмарков"""
    try:
        integration = get_benchmark_integration()
        return {
            "status": "available",
            "auto_benchmark_enabled": integration.auto_benchmark_enabled,
            "last_run": integration.last_benchmark_run is not None
        }
    except Exception as e:
        logger.error(f"Ошибка получения статуса бенчмарков: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

@router.post("/quick")
async def run_quick_benchmark():
    """Запуск быстрого бенчмарка"""
    try:
        integration = get_benchmark_integration()
        results = integration.run_quick_benchmark()
        return {
            "status": "success",
            "results": results
        }
    except Exception as e:
        logger.error(f"Ошибка запуска быстрого бенчмарка: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/full")
async def run_full_benchmark():
    """Запуск полного бенчмарка"""
    try:
        integration = get_benchmark_integration()
        results = integration.run_full_benchmark()
        return {
            "status": "success",
            "results": results
        }
    except Exception as e:
        logger.error(f"Ошибка запуска полного бенчмарка: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance")
async def get_performance_summary():
    """Получение сводки по производительности"""
    try:
        integration = get_benchmark_integration()
        summary = integration.get_performance_summary()
        return {
            "status": "success",
            "performance": summary
        }
    except Exception as e:
        logger.error(f"Ошибка получения сводки производительности: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_detailed_metrics():
    """Получение детальных метрик"""
    try:
        integration = get_benchmark_integration()
        if integration.last_benchmark_run:
            return {
                "status": "success",
                "metrics": integration.last_benchmark_run
            }
        else:
            return {
                "status": "no_data",
                "message": "Бенчмарк еще не запускался"
            }
    except Exception as e:
        logger.error(f"Ошибка получения детальных метрик: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auto-toggle")
async def toggle_auto_benchmark(enabled: bool):
    """Включение/выключение автоматических бенчмарков"""
    try:
        integration = get_benchmark_integration()
        integration.auto_benchmark_enabled = enabled
        return {
            "status": "success",
            "auto_benchmark_enabled": enabled
        }
    except Exception as e:
        logger.error(f"Ошибка переключения автоматических бенчмарков: {e}")
        raise HTTPException(status_code=500, detail=str(e))
