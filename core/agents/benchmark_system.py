#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BENCHMARK SYSTEM FOR Bldr AGENTS
================================

Система бенчмарков для оценки производительности агентов Bldr
на основе репозиториев agents-towards-production и других источников.

Включает:
- Бенчмарки для строительных задач
- Оценка производительности CoordinatorAgent
- Тестирование ToolsSystem
- Метрики качества ответов
"""

import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import statistics

logger = logging.getLogger(__name__)

@dataclass
class BenchmarkResult:
    """Результат выполнения бенчмарка"""
    test_name: str
    success: bool
    execution_time: float
    accuracy_score: float
    response_quality: str
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ConstructionBenchmark:
    """Бенчмарк для строительных задач"""
    name: str
    description: str
    input_query: str
    expected_elements: List[str]
    difficulty: str  # 'easy', 'medium', 'hard'
    category: str    # 'norms', 'cost', 'safety', 'design'

class BldrBenchmarkSystem:
    """Система бенчмарков для Bldr агентов"""
    
    def __init__(self):
        self.construction_benchmarks = self._load_construction_benchmarks()
        self.results_history = []
    
    def _load_construction_benchmarks(self) -> List[ConstructionBenchmark]:
        """Загружаем бенчмарки для строительных задач"""
        return [
            # НОРМАТИВНЫЕ ДОКУМЕНТЫ
            ConstructionBenchmark(
                name="norms_search_sp",
                description="Поиск СП по автомобильным дорогам",
                input_query="подскажи мне номер СП по автомобильным дорогам",
                expected_elements=["СП", "автомобиль", "дорог"],
                difficulty="easy",
                category="norms"
            ),
            ConstructionBenchmark(
                name="norms_search_snip",
                description="Поиск СНиП по зданиям",
                input_query="найди СНиП по жилым зданиям",
                expected_elements=["СНиП", "здание", "жилой"],
                difficulty="medium",
                category="norms"
            ),
            ConstructionBenchmark(
                name="norms_complex_query",
                description="Сложный запрос по нормам",
                input_query="какие нормы действуют для строительства многоэтажных зданий в сейсмических районах",
                expected_elements=["СП", "СНиП", "сейсмический", "многоэтажный"],
                difficulty="hard",
                category="norms"
            ),
            
            # СМЕТНЫЕ РАСЧЕТЫ
            ConstructionBenchmark(
                name="cost_estimation_basic",
                description="Базовый расчет стоимости",
                input_query="рассчитай стоимость строительства дома 100 кв.м",
                expected_elements=["стоимость", "расчет", "дом"],
                difficulty="easy",
                category="cost"
            ),
            ConstructionBenchmark(
                name="cost_estimation_complex",
                description="Сложный расчет стоимости",
                input_query="составь смету на строительство торгового центра с подземной парковкой",
                expected_elements=["смета", "торговый", "парковка", "подземная"],
                difficulty="hard",
                category="cost"
            ),
            
            # БЕЗОПАСНОСТЬ
            ConstructionBenchmark(
                name="safety_requirements",
                description="Требования безопасности",
                input_query="какие требования безопасности при строительстве высотных зданий",
                expected_elements=["безопасность", "высотный", "требование"],
                difficulty="medium",
                category="safety"
            ),
            
            # ПРОЕКТИРОВАНИЕ
            ConstructionBenchmark(
                name="design_standards",
                description="Стандарты проектирования",
                input_query="какие стандарты проектирования для общественных зданий",
                expected_elements=["проектирование", "стандарт", "общественный"],
                difficulty="medium",
                category="design"
            )
        ]
    
    def run_benchmark(self, agent, benchmark: ConstructionBenchmark) -> BenchmarkResult:
        """Запуск одного бенчмарка"""
        start_time = time.time()
        errors = []
        
        try:
            # Выполняем запрос через агента
            response = agent.process_request(benchmark.input_query)
            execution_time = time.time() - start_time
            
            # Анализируем качество ответа
            accuracy_score = self._calculate_accuracy(response, benchmark.expected_elements)
            response_quality = self._assess_response_quality(response, benchmark)
            
            success = accuracy_score >= 0.7 and len(errors) == 0
            
            result = BenchmarkResult(
                test_name=benchmark.name,
                success=success,
                execution_time=execution_time,
                accuracy_score=accuracy_score,
                response_quality=response_quality,
                errors=errors,
                metadata={
                    "benchmark_category": benchmark.category,
                    "benchmark_difficulty": benchmark.difficulty,
                    "response_length": len(response)
                }
            )
            
            self.results_history.append(result)
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            errors.append(str(e))
            
            return BenchmarkResult(
                test_name=benchmark.name,
                success=False,
                execution_time=execution_time,
                accuracy_score=0.0,
                response_quality="error",
                errors=errors
            )
    
    def _calculate_accuracy(self, response: str, expected_elements: List[str]) -> float:
        """Вычисляем точность ответа"""
        if not response:
            return 0.0
        
        response_lower = response.lower()
        found_elements = 0
        
        for element in expected_elements:
            if element.lower() in response_lower:
                found_elements += 1
        
        return found_elements / len(expected_elements)
    
    def _assess_response_quality(self, response: str, benchmark: ConstructionBenchmark) -> str:
        """Оцениваем качество ответа"""
        if not response:
            return "empty"
        
        if len(response) < 50:
            return "too_short"
        
        if "ошибка" in response.lower() or "error" in response.lower():
            return "error_response"
        
        if "готово" in response.lower() and len(response) < 100:
            return "generic_response"
        
        return "good"
    
    def run_all_benchmarks(self, agent) -> Dict[str, Any]:
        """Запуск всех бенчмарков"""
        results = []
        
        for benchmark in self.construction_benchmarks:
            logger.info(f"Запуск бенчмарка: {benchmark.name}")
            result = self.run_benchmark(agent, benchmark)
            results.append(result)
        
        return self._generate_report(results)
    
    def _generate_report(self, results: List[BenchmarkResult]) -> Dict[str, Any]:
        """Генерация отчета по бенчмаркам"""
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r.success)
        success_rate = successful_tests / total_tests if total_tests > 0 else 0
        
        execution_times = [r.execution_time for r in results]
        avg_execution_time = statistics.mean(execution_times) if execution_times else 0
        
        accuracy_scores = [r.accuracy_score for r in results]
        avg_accuracy = statistics.mean(accuracy_scores) if accuracy_scores else 0
        
        # Группировка по категориям
        category_stats = {}
        for result in results:
            category = result.metadata.get("benchmark_category", "unknown")
            if category not in category_stats:
                category_stats[category] = {"total": 0, "successful": 0}
            category_stats[category]["total"] += 1
            if result.success:
                category_stats[category]["successful"] += 1
        
        return {
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": success_rate,
                "avg_execution_time": avg_execution_time,
                "avg_accuracy": avg_accuracy
            },
            "category_stats": category_stats,
            "detailed_results": [
                {
                    "test_name": r.test_name,
                    "success": r.success,
                    "execution_time": r.execution_time,
                    "accuracy_score": r.accuracy_score,
                    "response_quality": r.response_quality,
                    "errors": r.errors
                }
                for r in results
            ]
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Получение метрик производительности"""
        if not self.results_history:
            return {"message": "Нет данных для анализа"}
        
        recent_results = self.results_history[-10:]  # Последние 10 тестов
        
        return {
            "recent_performance": {
                "avg_execution_time": statistics.mean([r.execution_time for r in recent_results]),
                "avg_accuracy": statistics.mean([r.accuracy_score for r in recent_results]),
                "success_rate": sum(1 for r in recent_results if r.success) / len(recent_results)
            },
            "total_tests_run": len(self.results_history),
            "last_run": self.results_history[-1].test_name if self.results_history else None
        }
