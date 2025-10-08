#!/usr/bin/env python3
"""
Финальный E2E тест с правильной аутентификацией
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

class FinalE2ETester:
    """Финальный E2E тестер с аутентификацией"""
    
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
        
        self.results = []
    
    def log_result(self, test_name: str, success: bool, duration: float, details: str = ""):
        """Логирование результата теста"""
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {duration:.2f}s {details}")
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
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base}/health", timeout=10) as response:
                    duration = time.time() - start_time
                    if response.status == 200:
                        data = await response.json()
                        endpoints = data.get('components', {}).get('endpoints', 0)
                        self.log_result("API Connectivity", True, duration, f"({endpoints} endpoints)")
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
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.lm_studio_base}/v1/models", timeout=10) as response:
                    duration = time.time() - start_time
                    if response.status == 200:
                        data = await response.json()
                        models_count = len(data.get('data', []))
                        self.log_result("LM Studio", True, duration, f"({models_count} models)")
                        return True
                    else:
                        self.log_result("LM Studio", False, duration, f"HTTP {response.status}")
                        return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("LM Studio", False, duration, str(e))
            return False
    
    async def test_websocket_with_auth(self):
        """Тест WebSocket с аутентификацией"""
        start_time = time.time()
        try:
            # Используем токен в query parameter
            uri = f"{self.ws_base}/ws?token={self.api_token}"
            async with websockets.connect(uri, timeout=10) as websocket:
                # Отправляем тестовое сообщение
                test_message = json.dumps({"type": "test", "message": "WebSocket test"})
                await websocket.send(test_message)
                
                # Ждем ответ
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    duration = time.time() - start_time
                    self.log_result("WebSocket Auth", True, duration, "Connection OK")
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
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(f"{self.api_base}/api/training/status", timeout=10) as response:
                    duration = time.time() - start_time
                    if response.status == 200:
                        data = await response.json()
                        is_training = data.get('is_training', False)
                        self.log_result("Training Status", True, duration, f"(training: {is_training})")
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
            query_data = {"query": "СП 31 требования", "k": 3}
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.post(f"{self.api_base}/query", json=query_data, timeout=30) as response:
                    duration = time.time() - start_time
                    if response.status == 200:
                        data = await response.json()
                        results_count = len(data.get('results', []))
                        ndcg = data.get('ndcg', 0)
                        self.log_result("RAG Search", True, duration, f"({results_count} results, NDCG: {ndcg})")
                        return True
                    else:
                        error_text = await response.text()
                        self.log_result("RAG Search", False, duration, f"HTTP {response.status}")
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
                "prompt": "Привет! Тест системы координатора",
                "model": "deepseek/deepseek-r1-0528-qwen3-8b"
            }
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.post(f"{self.api_base}/ai", json=ai_data, timeout=30) as response:
                    duration = time.time() - start_time
                    if response.status == 200:
                        data = await response.json()
                        status = data.get('status', 'unknown')
                        task_id = data.get('task_id', 'N/A')
                        self.log_result("AI Request", True, duration, f"({status}, task: {task_id})")
                        return True
                    else:
                        error_text = await response.text()
                        self.log_result("AI Request", False, duration, f"HTTP {response.status}")
                        return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("AI Request", False, duration, str(e))
            return False
    
    async def test_coordinator_light(self):
        """Легкий тест координатора (без timeout)"""
        start_time = time.time()
        try:
            coord_data = {
                "query": "Найди СП 31.13330",
                "source": "test",
                "user_id": "test_user"
            }
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.post(f"{self.api_base}/submit_query", json=coord_data, timeout=30) as response:
                    duration = time.time() - start_time
                    if response.status == 200:
                        data = await response.json()
                        has_plan = 'plan' in data
                        has_results = 'results' in data
                        status = data.get('status', 'unknown')
                        self.log_result("Coordinator Light", True, duration, f"({status}, plan: {has_plan}, results: {has_results})")
                        return True
                    else:
                        error_text = await response.text()
                        self.log_result("Coordinator Light", False, duration, f"HTTP {response.status}")
                        return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Coordinator Light", False, duration, str(e))
            return False
    
    async def run_all_tests(self):
        """Запуск всех тестов"""
        print("🚀 Финальное E2E тестирование с аутентификацией")
        print(f"🔑 Токен: {self.api_token[:20]}...")
        print("=" * 60)
        
        tests = [
            ("🌐 Connectivity", [
                self.test_api_connectivity,
                self.test_lm_studio,
                self.test_websocket_with_auth,
            ]),
            ("🔧 Core Functions", [
                self.test_training_status,
                self.test_rag_search,
            ]),
            ("🤖 AI & Coordinator", [
                self.test_ai_request,
                self.test_coordinator_light,
            ])
        ]
        
        for category, test_functions in tests:
            print(f"\n{category}:")
            for test_func in test_functions:
                await test_func()
        
        return self.results
    
    def generate_summary(self):
        """Генерация итоговой сводки"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r['success'])
        
        print(f"\n{'='*60}")
        print("📊 ИТОГОВАЯ СВОДКА")
        print("="*60)
        print(f"✅ Пройдено: {passed}/{total} тестов ({passed/total*100:.1f}%)")
        print(f"❌ Провалено: {total-passed}/{total} тестов")
        
        if passed == total:
            print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ! E2E процесс работает полностью!")
        elif passed >= total * 0.8:
            print("\n⚠️ Большинство тестов успешны, есть мелкие проблемы")
        elif passed >= total * 0.5:
            print("\n🔧 Половина тестов не прошла, требуется диагностика")
        else:
            print("\n🚨 Критические проблемы, большинство функций не работает")
        
        # Детали провалов
        failed = [r for r in self.results if not r['success']]
        if failed:
            print(f"\n❌ Провалившие тесты:")
            for fail in failed:
                print(f"   • {fail['name']}: {fail['details']}")
        
        print(f"\n📅 Время тестирования: {datetime.now().strftime('%H:%M:%S')}")
        
        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "success_rate": passed/total*100 if total > 0 else 0,
            "results": self.results
        }

async def main():
    """Главная функция"""
    try:
        tester = FinalE2ETester()
        await tester.run_all_tests()
        summary = tester.generate_summary()
        
        # Сохраняем результат
        with open("C:\\Bldr\\final_e2e_results.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 Результаты сохранены в final_e2e_results.json")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())