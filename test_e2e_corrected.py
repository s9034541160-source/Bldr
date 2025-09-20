#!/usr/bin/env python3
"""
Исправленный E2E тест с правильным портом API (8000)
"""

import asyncio
import aiohttp
import websockets
import json
import time
import requests
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Результат теста"""
    test_name: str
    success: bool
    duration: float
    error_msg: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class E2EFlowTester:
    """Класс для тестирования E2E процесса с правильными портами"""
    
    def __init__(self):
        # Используем правильный порт 8000
        self.api_base = "http://localhost:8000"
        self.ws_base = "ws://localhost:8000"
        self.lm_studio_base = "http://localhost:1234"
        self.results: List[TestResult] = []
        
        # Тестовые запросы
        self.test_queries = [
            {
                "type": "norms",
                "query": "СП 31.13330.2012 пункт 5.2.1 требования к фундаменту",
                "expected_tools": ["search_rag_database", "find_normatives"]
            },
            {
                "type": "financial", 
                "query": "Расчет стоимости строительства 2-этажного дома 100 кв.м",
                "expected_tools": ["calculate_estimate", "search_rag_database"]
            },
            {
                "type": "project",
                "query": "Создать ППР для кирпичной кладки стен",
                "expected_tools": ["generate_ppr", "get_work_sequence"]
            }
        ]
    
    async def test_api_connectivity(self) -> TestResult:
        """Тест подключения к API"""
        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base}/health", timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        duration = time.time() - start_time
                        return TestResult("API Connectivity", True, duration, details=data)
                    else:
                        duration = time.time() - start_time
                        return TestResult("API Connectivity", False, duration, f"HTTP {response.status}")
        except Exception as e:
            duration = time.time() - start_time
            return TestResult("API Connectivity", False, duration, str(e))
    
    async def test_rag_search(self) -> TestResult:
        """Тест RAG поиска"""
        start_time = time.time()
        try:
            query_data = {
                "query": "СП 31",
                "k": 3
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/query", 
                    json=query_data,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        duration = time.time() - start_time
                        results_count = len(data.get('results', []))
                        return TestResult("RAG Search", True, duration, 
                                        details={"results_count": results_count, "ndcg": data.get('ndcg', 0)})
                    else:
                        duration = time.time() - start_time
                        error_text = await response.text()
                        return TestResult("RAG Search", False, duration, f"HTTP {response.status}: {error_text}")
        except Exception as e:
            duration = time.time() - start_time
            return TestResult("RAG Search", False, duration, str(e))
    
    async def test_ai_request(self) -> TestResult:
        """Тест AI запроса"""
        start_time = time.time()
        try:
            ai_request = {
                "prompt": "Привет! Проверяем работу AI системы",
                "model": "deepseek/deepseek-r1-0528-qwen3-8b"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/ai",
                    json=ai_request,
                    timeout=60
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        duration = time.time() - start_time
                        
                        is_processing = data.get('status') == 'processing'
                        has_task_id = 'task_id' in data
                        
                        return TestResult("AI Request", True, duration,
                                        details={
                                            "status": data.get('status'),
                                            "task_id": data.get('task_id'),
                                            "is_processing": is_processing,
                                            "has_task_id": has_task_id
                                        })
                    else:
                        duration = time.time() - start_time
                        error_text = await response.text()
                        return TestResult("AI Request", False, duration, f"HTTP {response.status}: {error_text}")
        except Exception as e:
            duration = time.time() - start_time
            return TestResult("AI Request", False, duration, str(e))
    
    async def test_coordinator_query(self) -> TestResult:
        """Тест координатора через submit_query"""
        start_time = time.time()
        try:
            submit_data = {
                "query": "Создай смету для строительства гаража 6x4 метра",
                "source": "test",
                "user_id": "test_user"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/submit_query",
                    json=submit_data,
                    timeout=60
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        duration = time.time() - start_time
                        
                        has_plan = 'plan' in data
                        has_results = 'results' in data
                        
                        return TestResult("Coordinator Query", True, duration,
                                        details={
                                            "has_plan": has_plan,
                                            "has_results": has_results,
                                            "query": data.get('query'),
                                            "status": data.get('status')
                                        })
                    else:
                        duration = time.time() - start_time
                        error_text = await response.text()
                        return TestResult("Coordinator Query", False, duration, f"HTTP {response.status}: {error_text}")
        except Exception as e:
            duration = time.time() - start_time
            return TestResult("Coordinator Query", False, duration, str(e))
    
    async def test_websocket_connection(self) -> TestResult:
        """Тест WebSocket подключения"""
        start_time = time.time()
        try:
            uri = f"{self.ws_base}/ws"
            async with websockets.connect(uri, timeout=10) as websocket:
                # Отправим тестовое сообщение
                test_message = {"type": "test", "message": "WebSocket connectivity test"}
                await websocket.send(json.dumps(test_message))
                
                # Ждем ответ (если есть)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    duration = time.time() - start_time
                    return TestResult("WebSocket Connection", True, duration, details={"response": response})
                except asyncio.TimeoutError:
                    # Это нормально, если сервер не отвечает на тестовое сообщение
                    duration = time.time() - start_time
                    return TestResult("WebSocket Connection", True, duration, details={"note": "Connection established"})
        except Exception as e:
            duration = time.time() - start_time
            return TestResult("WebSocket Connection", False, duration, str(e))
    
    async def test_training_status(self) -> TestResult:
        """Тест статуса обучения"""
        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base}/api/training/status", timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        duration = time.time() - start_time
                        return TestResult("Training Status", True, duration,
                                        details={
                                            "is_training": data.get('is_training', False),
                                            "progress": data.get('progress', 0),
                                            "stage": data.get('current_stage', 'unknown')
                                        })
                    else:
                        duration = time.time() - start_time
                        error_text = await response.text()
                        return TestResult("Training Status", False, duration, f"HTTP {response.status}: {error_text}")
        except Exception as e:
            duration = time.time() - start_time
            return TestResult("Training Status", False, duration, str(e))
    
    async def test_lm_studio_connectivity(self) -> TestResult:
        """Тест подключения к LM Studio"""
        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.lm_studio_base}/v1/models", timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        duration = time.time() - start_time
                        models = [model['id'] for model in data.get('data', [])]
                        return TestResult("LM Studio Connectivity", True, duration, details={"models": models})
                    else:
                        duration = time.time() - start_time
                        return TestResult("LM Studio Connectivity", False, duration, f"HTTP {response.status}")
        except Exception as e:
            duration = time.time() - start_time
            return TestResult("LM Studio Connectivity", False, duration, str(e))
    
    async def run_all_tests(self) -> List[TestResult]:
        """Запуск всех тестов"""
        logger.info("🚀 Запуск исправленного E2E тестирования (порт 8000)")
        logger.info("=" * 60)
        
        # 1. Базовая связность
        logger.info("1️⃣ Тестируем базовую связность...")
        self.results.append(await self.test_api_connectivity())
        self.results.append(await self.test_lm_studio_connectivity())
        self.results.append(await self.test_websocket_connection())
        
        # 2. Core функциональность
        logger.info("2️⃣ Тестируем core функциональность...")
        self.results.append(await self.test_training_status())
        self.results.append(await self.test_rag_search())
        
        # 3. AI и координатор
        logger.info("3️⃣ Тестируем AI и координатор...")
        self.results.append(await self.test_ai_request())
        self.results.append(await self.test_coordinator_query())
        
        return self.results
    
    def generate_quick_report(self) -> str:
        """Быстрый отчет"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        
        report = f"""
🔄 ИСПРАВЛЕННЫЙ E2E ТЕСТ (порт 8000)
{'=' * 50}

📊 Результаты: {passed_tests}/{total_tests} тестов пройдено

"""
        
        for result in self.results:
            status = "✅" if result.success else "❌"
            report += f"{status} {result.test_name}: {result.duration:.2f}s"
            
            if result.error_msg:
                report += f" - {result.error_msg}"
            elif result.details:
                # Показываем ключевые детали
                if 'results_count' in result.details:
                    report += f" (результатов: {result.details['results_count']})"
                elif 'models' in result.details:
                    report += f" (моделей: {len(result.details['models'])})"
                elif 'is_training' in result.details:
                    report += f" (обучение: {result.details['is_training']})"
                elif 'status' in result.details:
                    report += f" (статус: {result.details['status']})"
            
            report += "\\n"
        
        if passed_tests == total_tests:
            report += "\\n🎉 Все тесты прошли! E2E процесс работает корректно."
        elif passed_tests >= total_tests * 0.7:
            report += "\\n⚠️ Большинство тестов успешны, есть мелкие проблемы."
        else:
            report += "\\n🔧 Требуется диагностика неудачных тестов."
        
        return report

async def main():
    """Основная функция"""
    tester = E2EFlowTester()
    
    try:
        results = await tester.run_all_tests()
        report = tester.generate_quick_report()
        print(report)
        
        # Сохраняем результаты
        timestamp = datetime.now().isoformat()
        json_results = {
            "timestamp": timestamp,
            "api_port": 8000,
            "total_tests": len(results),
            "passed": sum(1 for r in results if r.success),
            "results": [
                {
                    "name": r.test_name,
                    "success": r.success,
                    "duration": r.duration,
                    "error": r.error_msg,
                    "details": r.details
                }
                for r in results
            ]
        }
        
        with open("C:\\Bldr\\e2e_results_corrected.json", "w", encoding="utf-8") as f:
            json.dump(json_results, f, ensure_ascii=False, indent=2)
        
        logger.info("📄 Результаты сохранены в e2e_results_corrected.json")
        
    except KeyboardInterrupt:
        logger.info("⏹️ Тестирование прервано")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())