#!/usr/bin/env python3
"""
Комплексный тест E2E (end-to-end) процесса системы BLDR
Проверяет весь путь от запроса пользователя до получения ответа

Включает:
1. Telegram Bot -> API -> Coordinator -> Tools -> Response
2. AI Shell Frontend -> API -> Coordinator -> Tools -> Response  
3. Тестирование интеграции с LM Studio
4. WebSocket обновления в реальном времени
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
    """Класс для тестирования E2E процесса"""
    
    def __init__(self, 
                 api_base: str = "http://localhost:8001",
                 ws_base: str = "ws://localhost:8001",
                 lm_studio_base: str = "http://localhost:1234"):
        self.api_base = api_base
        self.ws_base = ws_base
        self.lm_studio_base = lm_studio_base
        self.results: List[TestResult] = []
        
        # Тестовые запросы разных типов
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
            },
            {
                "type": "coordination",
                "query": "Проанализировать проект и создать план работ с графиком",
                "expected_tools": ["analyze_tender", "create_gantt_chart"]
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
    
    async def test_lm_studio_connectivity(self) -> TestResult:
        """Тест подключения к LM Studio"""
        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                # Проверяем модели LM Studio
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
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    duration = time.time() - start_time
                    return TestResult("WebSocket Connection", True, duration, details={"response": response})
                except asyncio.TimeoutError:
                    # Это нормально, если сервер не отвечает на тестовое сообщение
                    duration = time.time() - start_time
                    return TestResult("WebSocket Connection", True, duration, details={"note": "Connection established, no response expected"})
        except Exception as e:
            duration = time.time() - start_time
            return TestResult("WebSocket Connection", False, duration, str(e))
    
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
                    f"{self.api_base}/api/search", 
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
    
    async def test_coordinator_plan_generation(self, test_query: Dict[str, Any]) -> TestResult:
        """Тест генерации плана координатором"""
        start_time = time.time()
        try:
            submit_data = {
                "query": test_query["query"],
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
                        
                        # Проверяем структуру плана
                        plan = data.get('plan', {})
                        has_expected_tools = False
                        if 'tools' in plan:
                            plan_tools = [tool.get('name', '') for tool in plan.get('tools', [])]
                            has_expected_tools = any(tool in plan_tools for tool in test_query.get('expected_tools', []))
                        
                        return TestResult(
                            f"Coordinator Plan ({test_query['type']})", 
                            True, 
                            duration,
                            details={
                                "plan": plan,
                                "results": data.get('results', {}),
                                "has_expected_tools": has_expected_tools,
                                "plan_tools": plan_tools if 'plan_tools' in locals() else []
                            }
                        )
                    else:
                        duration = time.time() - start_time
                        error_text = await response.text()
                        return TestResult(f"Coordinator Plan ({test_query['type']})", False, duration, 
                                        f"HTTP {response.status}: {error_text}")
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(f"Coordinator Plan ({test_query['type']})", False, duration, str(e))
    
    async def test_ai_shell_integration(self) -> TestResult:
        """Тест интеграции AI Shell"""
        start_time = time.time()
        try:
            ai_request = {
                "prompt": "Выступая в роли координатора: Создай план строительства гаража",
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
                        
                        # Проверяем что задача запущена
                        is_processing = data.get('status') == 'processing'
                        has_task_id = 'task_id' in data
                        
                        return TestResult("AI Shell Integration", True, duration,
                                        details={
                                            "status": data.get('status'),
                                            "task_id": data.get('task_id'),
                                            "is_processing": is_processing,
                                            "has_task_id": has_task_id
                                        })
                    else:
                        duration = time.time() - start_time
                        error_text = await response.text()
                        return TestResult("AI Shell Integration", False, duration, f"HTTP {response.status}: {error_text}")
        except Exception as e:
            duration = time.time() - start_time
            return TestResult("AI Shell Integration", False, duration, str(e))
    
    async def test_telegram_bot_simulation(self) -> TestResult:
        """Симуляция запроса от Telegram бота"""
        start_time = time.time()
        try:
            # Симулируем запрос как от Telegram бота через /query endpoint
            query_data = {
                "query": "требования СП31 для фундамента",
                "k": 3
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/query",
                    json=query_data,
                    timeout=60
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        duration = time.time() - start_time
                        
                        results = data.get('results', [])
                        has_results = len(results) > 0
                        has_ndcg = 'ndcg' in data
                        
                        return TestResult("Telegram Bot Simulation", True, duration,
                                        details={
                                            "results_count": len(results),
                                            "ndcg": data.get('ndcg', 0),
                                            "has_results": has_results,
                                            "has_ndcg": has_ndcg,
                                            "first_result": results[0] if results else None
                                        })
                    else:
                        duration = time.time() - start_time
                        error_text = await response.text()
                        return TestResult("Telegram Bot Simulation", False, duration, f"HTTP {response.status}: {error_text}")
        except Exception as e:
            duration = time.time() - start_time
            return TestResult("Telegram Bot Simulation", False, duration, str(e))
    
    async def run_all_tests(self) -> List[TestResult]:
        """Запуск всех тестов"""
        logger.info("🚀 Начинаем комплексное тестирование E2E процесса")
        logger.info("=" * 80)
        
        # 1. Тест базовой связности
        logger.info("1️⃣ Тестирование базовой связности...")
        self.results.append(await self.test_api_connectivity())
        self.results.append(await self.test_lm_studio_connectivity())
        self.results.append(await self.test_websocket_connection())
        
        # 2. Тест RAG системы
        logger.info("2️⃣ Тестирование RAG системы...")
        self.results.append(await self.test_rag_search())
        
        # 3. Тест координатора для разных типов запросов
        logger.info("3️⃣ Тестирование координатора...")
        for test_query in self.test_queries:
            result = await self.test_coordinator_plan_generation(test_query)
            self.results.append(result)
            await asyncio.sleep(1)  # Небольшая пауза между тестами
        
        # 4. Тест AI Shell интеграции
        logger.info("4️⃣ Тестирование AI Shell интеграции...")
        self.results.append(await self.test_ai_shell_integration())
        
        # 5. Симуляция Telegram бота
        logger.info("5️⃣ Симуляция Telegram бота...")
        self.results.append(await self.test_telegram_bot_simulation())
        
        return self.results
    
    def generate_report(self) -> str:
        """Генерация итогового отчета"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - passed_tests
        
        report = f"""
📊 ОТЧЕТ О ТЕСТИРОВАНИИ E2E ПРОЦЕССА
{'=' * 80}

📈 СТАТИСТИКА:
✅ Пройдено: {passed_tests}/{total_tests}
❌ Провалено: {failed_tests}/{total_tests}
📊 Успешность: {(passed_tests/total_tests*100):.1f}%

🔍 ДЕТАЛИ ТЕСТОВ:
"""
        
        for result in self.results:
            status = "✅" if result.success else "❌"
            report += f"{status} {result.test_name}: {result.duration:.2f}s"
            
            if result.error_msg:
                report += f" - {result.error_msg}"
            
            if result.details:
                key_details = []
                if 'results_count' in result.details:
                    key_details.append(f"результатов: {result.details['results_count']}")
                if 'models' in result.details:
                    key_details.append(f"моделей: {len(result.details['models'])}")
                if 'has_expected_tools' in result.details:
                    key_details.append(f"инструменты: {'✓' if result.details['has_expected_tools'] else '✗'}")
                if 'is_processing' in result.details:
                    key_details.append(f"обработка: {'✓' if result.details['is_processing'] else '✗'}")
                
                if key_details:
                    report += f" ({', '.join(key_details)})"
            
            report += "\\n"
        
        report += f"""
🎯 ВЫВОДЫ:
"""
        
        if passed_tests == total_tests:
            report += "🎉 Все тесты прошли успешно! E2E процесс работает корректно."
        elif passed_tests >= total_tests * 0.8:
            report += "⚠️ Большинство тестов прошли успешно, но есть проблемы требующие внимания."
        elif passed_tests >= total_tests * 0.5:
            report += "🔧 Половина тестов провалена. Требуется серьезная диагностика."
        else:
            report += "🚨 Критическое состояние! Большинство компонентов E2E процесса не работают."
        
        # Рекомендации
        failed_results = [r for r in self.results if not r.success]
        if failed_results:
            report += f"""

🔧 РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ:
"""
            for result in failed_results:
                if "Connectivity" in result.test_name:
                    report += f"- {result.test_name}: Проверьте что сервис запущен и доступен\\n"
                elif "RAG" in result.test_name:
                    report += f"- {result.test_name}: Убедитесь что RAG обучение завершено\\n"
                elif "Coordinator" in result.test_name:
                    report += f"- {result.test_name}: Проверьте работу координатора и инструментов\\n"
                elif "AI Shell" in result.test_name:
                    report += f"- {result.test_name}: Проверьте интеграцию с LM Studio\\n"
                elif "Telegram" in result.test_name:
                    report += f"- {result.test_name}: Проверьте Telegram бот конфигурацию\\n"
        
        report += f"""

📝 ВРЕМЯ ГЕНЕРАЦИИ ОТЧЕТА: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return report

async def main():
    """Основная функция тестирования"""
    tester = E2EFlowTester()
    
    try:
        # Запуск всех тестов
        results = await tester.run_all_tests()
        
        # Генерация и вывод отчета
        report = tester.generate_report()
        print(report)
        
        # Сохранение отчета в файл
        with open("C:\\Bldr\\e2e_test_report.txt", "w", encoding="utf-8") as f:
            f.write(report)
        
        logger.info("📄 Отчет сохранен в C:\\Bldr\\e2e_test_report.txt")
        
        # Вывод JSON результатов для программной обработки
        json_results = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(results),
            "passed": sum(1 for r in results if r.success),
            "failed": sum(1 for r in results if not r.success),
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
        
        with open("C:\\Bldr\\e2e_test_results.json", "w", encoding="utf-8") as f:
            json.dump(json_results, f, ensure_ascii=False, indent=2)
        
        logger.info("📄 JSON результаты сохранены в C:\\Bldr\\e2e_test_results.json")
        
    except KeyboardInterrupt:
        logger.info("⏹️ Тестирование прервано пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка тестирования: {e}")

if __name__ == "__main__":
    asyncio.run(main())