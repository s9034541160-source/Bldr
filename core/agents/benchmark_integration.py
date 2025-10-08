#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BENCHMARK INTEGRATION FOR Bldr
==============================

Интеграция системы бенчмарков в основной код Bldr
для автоматического тестирования и мониторинга производительности.
"""

import logging
from typing import Dict, Any, Optional
from core.agents.benchmark_system import BldrBenchmarkSystem, BenchmarkResult

logger = logging.getLogger(__name__)

class BenchmarkIntegration:
    """Интеграция бенчмарков в Bldr"""
    
    def __init__(self, coordinator_agent, tools_system):
        self.coordinator_agent = coordinator_agent
        self.tools_system = tools_system
        self.benchmark_system = BldrBenchmarkSystem()
        self.auto_benchmark_enabled = True
        self.last_benchmark_run = None
    
    def run_quick_benchmark(self) -> Dict[str, Any]:
        """Быстрый бенчмарк для проверки работоспособности"""
        logger.info("🚀 Запуск быстрого бенчмарка...")
        
        # Тестируем базовые функции
        test_queries = [
            "привет",
            "подскажи номер СП по автомобильным дорогам",
            "расскажи о себе"
        ]
        
        results = []
        for query in test_queries:
            try:
                response = self.coordinator_agent.process_request(query)
                results.append({
                    "query": query,
                    "response_length": len(response),
                    "has_error": "ошибка" in response.lower() or "error" in response.lower(),
                    "is_generic": response.strip() == "Готово." or len(response) < 20
                })
            except Exception as e:
                results.append({
                    "query": query,
                    "error": str(e),
                    "has_error": True
                })
        
        return {
            "quick_benchmark_results": results,
            "system_status": "healthy" if all(not r.get("has_error", False) for r in results) else "issues_detected"
        }
    
    def run_full_benchmark(self) -> Dict[str, Any]:
        """Полный бенчмарк всех агентов"""
        logger.info("🚀 Запуск полного бенчмарка...")
        
        try:
            results = self.benchmark_system.run_all_benchmarks(self.coordinator_agent)
            self.last_benchmark_run = results
            return results
        except Exception as e:
            logger.error(f"Ошибка при запуске полного бенчмарка: {e}")
            return {"error": str(e)}
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Получение сводки по производительности"""
        if not self.last_benchmark_run:
            return {"message": "Бенчмарк еще не запускался"}
        
        summary = self.last_benchmark_run.get("summary", {})
        return {
            "success_rate": summary.get("success_rate", 0),
            "avg_execution_time": summary.get("avg_execution_time", 0),
            "avg_accuracy": summary.get("avg_accuracy", 0),
            "total_tests": summary.get("total_tests", 0),
            "performance_grade": self._calculate_performance_grade(summary)
        }
    
    def _calculate_performance_grade(self, summary: Dict[str, Any]) -> str:
        """Вычисляем оценку производительности"""
        success_rate = summary.get("success_rate", 0)
        avg_accuracy = summary.get("avg_accuracy", 0)
        
        if success_rate >= 0.9 and avg_accuracy >= 0.8:
            return "A+ (Отлично)"
        elif success_rate >= 0.8 and avg_accuracy >= 0.7:
            return "A (Хорошо)"
        elif success_rate >= 0.7 and avg_accuracy >= 0.6:
            return "B (Удовлетворительно)"
        elif success_rate >= 0.6 and avg_accuracy >= 0.5:
            return "C (Требует улучшения)"
        else:
            return "D (Критические проблемы)"
    
    def auto_benchmark_if_needed(self) -> Optional[Dict[str, Any]]:
        """Автоматический бенчмарк при необходимости"""
        if not self.auto_benchmark_enabled:
            return None
        
        # Запускаем быстрый бенчмарк каждые 10 запросов
        # (это можно настроить)
        return self.run_quick_benchmark()
