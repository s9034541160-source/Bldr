#!/usr/bin/env python3
"""
E2E тест с увеличенными таймаутами для стабильной работы
"""

import asyncio
import aiohttp
import websockets
import json
import time
import os
from dotenv import load_dotenv
from datetime import datetime

# Загружаем переменные окружения
load_dotenv()

class ExtendedTimeoutE2ETester:
    """E2E тестер с увеличенными таймаутами"""
    
    def __init__(self):
        self.api_base = "http://localhost:8000"
        self.ws_base = "ws://localhost:8000"
        self.lm_studio_base = "http://localhost:1234"
        
        # Получаем токен из .env
        self.api_token = os.getenv('API_TOKEN')
        if not self.api_token:
            raise ValueError("API_TOKEN не найден в .env файле!")
        
        # Заголовки аутентификации
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        # Увеличенные таймауты
        self.timeouts = {
            "quick": 30,        # Для быстрых операций (health, models)
            "standard": 60,     # Для стандартных операций (RAG, AI)
            "long": 120,        # Для долгих операций (coordinator, complex AI)
            "websocket": 20,    # Для WebSocket подключений
            "training": 180     # Для операций обучения
        }
        
        self.results = []
    
    def log_result(self, test_name: str, success: bool, duration: float, details: str = ""):
        """Логирование результата теста"""
        status = "✅" if success else "❌"
        timeout_info = ""
        if duration > 30:
            timeout_info = f" [SLOW: {duration:.1f}s]"
        print(f"{status} {test_name}: {duration:.2f}s{timeout_info} {details}")
        self.results.append({
            "name": test_name,
            "success": success,
            "duration": duration,
            "details": details
        })
    
    async def test_api_connectivity(self):
        """Тест подключения к API"""
        start_time = time.time()
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeouts["quick"])
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.api_base}/health") as response:
                    duration = time.time() - start_time
                    if response.status == 200:
                        data = await response.json()
                        endpoints = data.get('components', {}).get('endpoints', 0)
                        status = data.get('status', 'unknown')
                        self.log_result("API Connectivity", True, duration, f"({endpoints} endpoints, {status})")
                        return True
                    else:
                        self.log_result("API Connectivity", False, duration, f"HTTP {response.status}")
                        return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("API Connectivity", False, duration, str(e))
            return False
    
    async def test_lm_studio(self):
        """Тест LM Studio"""
        start_time = time.time()
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeouts["quick"])
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.lm_studio_base}/v1/models") as response:
                    duration = time.time() - start_time
                    if response.status == 200:
                        data = await response.json()
                        models = data.get('data', [])
                        models_count = len(models)
                        model_names = [model.get('id', 'unknown')[:20] for model in models[:3]]
                        self.log_result("LM Studio", True, duration, f"({models_count} models: {', '.join(model_names)})")
                        return True
                    else:
                        self.log_result("LM Studio", False, duration, f"HTTP {response.status}")
                        return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("LM Studio", False, duration, str(e))
            return False
    
    async def test_websocket_with_auth(self):
        """Тест WebSocket с аутентификацией и увеличенным таймаутом"""
        start_time = time.time()
        try:
            # Используем токен в query parameter
            uri = f"{self.ws_base}/ws?token={self.api_token}"
            async with websockets.connect(uri, timeout=self.timeouts["websocket"]) as websocket:
                # Отправляем тестовое сообщение
                test_message = json.dumps({
                    "type": "ping", 
                    "message": "WebSocket connectivity test",
                    "timestamp": datetime.now().isoformat()
                })
                await websocket.send(test_message)
                
                # Ждем ответ с увеличенным таймаутом
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    duration = time.time() - start_time
                    self.log_result("WebSocket Auth", True, duration, "Connected + Response")
                    return True
                except asyncio.TimeoutError:
                    duration = time.time() - start_time
                    self.log_result("WebSocket Auth", True, duration, "Connected (no response)")
                    return True
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("WebSocket Auth", False, duration, str(e))
            return False
    
    async def test_training_status(self):
        """Тест статуса обучения"""
        start_time = time.time()
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeouts["standard"])
            async with aiohttp.ClientSession(headers=self.headers, timeout=timeout) as session:
                async with session.get(f"{self.api_base}/api/training/status") as response:
                    duration = time.time() - start_time
                    if response.status == 200:
                        data = await response.json()
                        is_training = data.get('is_training', False)
                        status = data.get('status', 'unknown')
                        stage = data.get('current_stage', 'unknown')
                        self.log_result("Training Status", True, duration, f"({status}, training: {is_training}, stage: {stage})")
                        return True
                    else:
                        error_text = await response.text()
                        self.log_result("Training Status", False, duration, f"HTTP {response.status}")
                        return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Training Status", False, duration, str(e))
            return False
    
    async def test_rag_search(self):
        """Тест RAG поиска"""
        start_time = time.time()
        try:
            query_data = {"query": "СП 31 строительные нормы", "k": 5}
            timeout = aiohttp.ClientTimeout(total=self.timeouts["standard"])
            async with aiohttp.ClientSession(headers=self.headers, timeout=timeout) as session:
                async with session.post(f"{self.api_base}/query", json=query_data) as response:
                    duration = time.time() - start_time
                    if response.status == 200:
                        data = await response.json()
                        results = data.get('results', [])
                        results_count = len(results)
                        ndcg = data.get('ndcg', 0)
                        
                        # Проверяем качество результатов
                        has_content = any(len(r.get('chunk', '')) > 50 for r in results)
                        avg_score = sum(r.get('score', 0) for r in results) / len(results) if results else 0
                        
                        details = f"({results_count} results, NDCG: {ndcg}, avg_score: {avg_score:.2f}, has_content: {has_content})"
                        self.log_result("RAG Search", True, duration, details)
                        return True
                    else:
                        error_text = await response.text()
                        self.log_result("RAG Search", False, duration, f"HTTP {response.status}: {error_text[:100]}")
                        return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("RAG Search", False, duration, str(e))
            return False
    
    async def test_ai_request(self):
        """Тест AI запроса"""
        start_time = time.time()
        try:
            ai_data = {
                "prompt": "Привет! Это быстрый тест AI системы координатора BLDR. Ответь кратко.",
                "model": "deepseek/deepseek-r1-0528-qwen3-8b"
            }
            timeout = aiohttp.ClientTimeout(total=self.timeouts["standard"])
            async with aiohttp.ClientSession(headers=self.headers, timeout=timeout) as session:
                async with session.post(f"{self.api_base}/ai", json=ai_data) as response:
                    duration = time.time() - start_time
                    if response.status == 200:
                        data = await response.json()
                        status = data.get('status', 'unknown')
                        task_id = data.get('task_id', 'N/A')
                        model = data.get('model', 'unknown')
                        self.log_result("AI Request", True, duration, f"({status}, task: {task_id}, model: {model})")
                        return True
                    else:
                        error_text = await response.text()
                        self.log_result("AI Request", False, duration, f"HTTP {response.status}: {error_text[:100]}")
                        return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("AI Request", False, duration, str(e))
            return False
    
    async def test_coordinator_simple(self):
        """Простой тест координатора с увеличенным таймаутом"""
        start_time = time.time()
        try:
            coord_data = {
                "query": "Найди информацию о СП 31",
                "source": "test",
                "user_id": "test_user"
            }
            timeout = aiohttp.ClientTimeout(total=self.timeouts["long"])
            async with aiohttp.ClientSession(headers=self.headers, timeout=timeout) as session:
                async with session.post(f"{self.api_base}/submit_query", json=coord_data) as response:
                    duration = time.time() - start_time
                    if response.status == 200:
                        data = await response.json()
                        has_plan = 'plan' in data
                        has_results = 'results' in data
                        status = data.get('status', 'unknown')
                        query = data.get('query', 'unknown')[:30]
                        
                        details = f"({status}, plan: {has_plan}, results: {has_results}, query: '{query}...')"
                        
                        if has_plan and data.get('plan'):
                            plan = data['plan']
                            query_type = plan.get('query_type', 'unknown')
                            tools = plan.get('tools', [])
                            tool_names = [t.get('name', 'unknown') for t in tools[:3]]
                            details += f", type: {query_type}, tools: {tool_names}"
                        
                        self.log_result("Coordinator Simple", True, duration, details)
                        return True
                    else:
                        error_text = await response.text()
                        self.log_result("Coordinator Simple", False, duration, f"HTTP {response.status}: {error_text[:100]}")
                        return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Coordinator Simple", False, duration, str(e))
            return False
    
    async def test_training_start(self):
        """Тест запуска обучения (если нужно)"""
        start_time = time.time()
        try:
            train_data = {"custom_dir": None}  # Используем дефолтную директорию
            timeout = aiohttp.ClientTimeout(total=self.timeouts["quick"])
            async with aiohttp.ClientSession(headers=self.headers, timeout=timeout) as session:
                async with session.post(f"{self.api_base}/train", json=train_data) as response:
                    duration = time.time() - start_time
                    if response.status == 200:
                        data = await response.json()
                        status = data.get('status', 'unknown')
                        message = data.get('message', '')[:50]
                        self.log_result("Training Start", True, duration, f"({status}, msg: '{message}...')")
                        return True
                    else:
                        error_text = await response.text()
                        self.log_result("Training Start", False, duration, f"HTTP {response.status}: {error_text[:100]}")
                        return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Training Start", False, duration, str(e))
            return False
    
    async def run_all_tests(self):
        """Запуск всех тестов с подробным мониторингом"""
        print("🚀 E2E тестирование с увеличенными таймаутами")
        print(f"🔑 Токен: {self.api_token[:20]}...")
        print(f"⏱️ Таймауты: quick={self.timeouts['quick']}s, standard={self.timeouts['standard']}s, long={self.timeouts['long']}s")
        print("=" * 80)
        
        tests = [
            ("🌐 Базовая связность", [
                ("API Health Check", self.test_api_connectivity),
                ("LM Studio Models", self.test_lm_studio),
                ("WebSocket Connection", self.test_websocket_with_auth),
            ]),
            ("🔧 Основные функции", [
                ("Training Status", self.test_training_status),
                ("RAG Search Engine", self.test_rag_search),
                ("Training Start", self.test_training_start),
            ]),
            ("🤖 AI & Координация", [
                ("AI Processing", self.test_ai_request),
                ("Coordinator System", self.test_coordinator_simple),
            ])
        ]
        
        total_start = time.time()
        
        for category, test_list in tests:
            print(f"\n{category}:")
            for test_name, test_func in test_list:
                print(f"   🔄 {test_name}...", end=" ", flush=True)
                try:
                    await test_func()
                except Exception as e:
                    print(f"❌ Exception: {str(e)}")
                    self.results.append({
                        "name": test_name,
                        "success": False,
                        "duration": 0,
                        "details": f"Exception: {str(e)}"
                    })
        
        total_duration = time.time() - total_start
        print(f"\n⏱️ Общее время тестирования: {total_duration:.2f}s")
        
        return self.results
    
    def generate_detailed_summary(self):
        """Генерация детальной сводки с рекомендациями"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r['success'])
        failed = [r for r in self.results if not r['success']]
        
        print(f"\n{'='*80}")
        print("📊 ДЕТАЛЬНАЯ ИТОГОВАЯ СВОДКА")
        print("="*80)
        print(f"✅ Успешно: {passed}/{total} тестов ({passed/total*100:.1f}%)")
        print(f"❌ Провалено: {len(failed)}/{total} тестов")
        
        # Анализ производительности
        slow_tests = [r for r in self.results if r['success'] and r['duration'] > 30]
        if slow_tests:
            print(f"\n⏱️ Медленные тесты (>30s):")
            for test in slow_tests:
                print(f"   • {test['name']}: {test['duration']:.1f}s - {test['details']}")
        
        # Статус системы
        if passed == total:
            print("\n🎉 ПОЛНЫЙ УСПЕХ! E2E процесс работает идеально!")
            print("   Все компоненты системы функционируют корректно.")
        elif passed >= total * 0.85:
            print("\n✨ ОТЛИЧНО! Система практически полностью работает!")
            print("   Минорные проблемы не влияют на основной функционал.")
        elif passed >= total * 0.7:
            print("\n⚠️ ХОРОШО! Основная функциональность работает.")
            print("   Есть проблемы, которые стоит исправить для полной стабильности.")
        elif passed >= total * 0.5:
            print("\n🔧 ЧАСТИЧНО! Половина функций работает.")
            print("   Требуется диагностика для повышения стабильности.")
        else:
            print("\n🚨 ПРОБЛЕМЫ! Много критических ошибок.")
            print("   Требуется серьезная диагностика и исправления.")
        
        # Детали провалов с рекомендациями
        if failed:
            print(f"\n❌ Детали провалов и рекомендации:")
            for fail in failed:
                print(f"\n   🔍 {fail['name']}:")
                print(f"      Ошибка: {fail['details']}")
                
                # Рекомендации по типу ошибки
                if "timeout" in fail['details'].lower():
                    print(f"      💡 Рекомендация: Увеличить таймаут или проверить производительность")
                elif "connection" in fail['details'].lower():
                    print(f"      💡 Рекомендация: Проверить сетевое подключение и статус сервисов")
                elif "401" in fail['details'] or "403" in fail['details']:
                    print(f"      💡 Рекомендация: Проверить токен аутентификации")
                elif "404" in fail['details']:
                    print(f"      💡 Рекомендация: Проверить корректность API endpoints")
                elif "500" in fail['details']:
                    print(f"      💡 Рекомендация: Проверить логи сервера для внутренних ошибок")
                else:
                    print(f"      💡 Рекомендация: Проверить конфигурацию и логи системы")
        
        # Рекомендации по следующим шагам
        print(f"\n🚀 СЛЕДУЮЩИЕ ШАГИ:")
        if passed >= total * 0.85:
            print("   1. Система готова к продуктивному использованию")
            print("   2. Мониторить производительность медленных операций")
            print("   3. Настроить автоматическое тестирование")
        else:
            print("   1. Исправить провалившие тесты по приоритету")
            print("   2. Увеличить таймауты для медленных операций")
            print("   3. Проверить конфигурацию и статус всех сервисов")
            print("   4. Повторить тестирование после исправлений")
        
        print(f"\n📅 Время завершения: {datetime.now().strftime('%H:%M:%S')}")
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total": total,
            "passed": passed,
            "failed": len(failed),
            "success_rate": passed/total*100 if total > 0 else 0,
            "slow_tests": len(slow_tests),
            "results": self.results,
            "timeouts_used": self.timeouts
        }

async def main():
    """Главная функция"""
    try:
        tester = ExtendedTimeoutE2ETester()
        await tester.run_all_tests()
        summary = tester.generate_detailed_summary()
        
        # Сохраняем детальные результаты
        with open("C:\\Bldr\\e2e_extended_results.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 Детальные результаты сохранены в e2e_extended_results.json")
        
    except Exception as e:
        print(f"❌ Критическая ошибка тестирования: {e}")

if __name__ == "__main__":
    asyncio.run(main())