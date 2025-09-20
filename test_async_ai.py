#!/usr/bin/env python3
"""
Test Async AI Processing Architecture
Verify non-blocking AI requests and concurrent handling
"""

import asyncio
import requests
import json
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_BASE = 'http://localhost:8000'
API_TOKEN = os.getenv('API_TOKEN')

def get_auth_headers():
    """Get authentication headers for API calls"""
    headers = {
        "Content-Type": "application/json"
    }
    if API_TOKEN:
        headers['Authorization'] = f'Bearer {API_TOKEN}'
    return headers

async def test_concurrent_ai_requests():
    """Test multiple concurrent AI requests"""
    print("🧪 Тестирование асинхронной обработки AI запросов...")
    
    # Check if API is responsive first
    try:
        response = requests.get(f'{API_BASE}/health', timeout=5)
        if response.status_code != 200:
            print(f"❌ API не отвечает: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ API недоступен: {str(e)}")
        return
    
    print("✅ API доступен, запускаем тесты...")
    
    # Test 1: Submit multiple AI requests concurrently
    print("\n📤 Отправка 3 одновременных AI запросов...")
    
    requests_data = [
        {
            "prompt": "Какие требования к бетону М300?",
            "model": "deepseek/deepseek-r1-0528-qwen3-8b"
        },
        {
            "prompt": "Анализ строительных норм для фундамента",
            "model": "deepseek/deepseek-r1-0528-qwen3-8b"
        },
        {
            "prompt": "Требования к арматуре в железобетонных конструкциях",
            "model": "deepseek/deepseek-r1-0528-qwen3-8b"
        }
    ]
    
    task_ids = []
    start_time = time.time()
    
    # Submit all requests quickly
    for i, request_data in enumerate(requests_data):
        try:
            response = requests.post(
                f'{API_BASE}/ai',
                json=request_data,
                headers=get_auth_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                task_id = result.get('task_id')
                task_ids.append(task_id)
                print(f"✅ Запрос {i+1} отправлен: {task_id}")
            else:
                print(f"❌ Ошибка запроса {i+1}: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Исключение в запросе {i+1}: {str(e)}")
    
    submission_time = time.time() - start_time
    print(f"⏱️ Время отправки всех запросов: {submission_time:.2f} секунд")
    
    if len(task_ids) == 0:
        print("❌ Не удалось отправить ни одного запроса")
        return
    
    # Test 2: Check that API remains responsive during processing
    print(f"\n🏃 Проверка отзывчивости API во время обработки {len(task_ids)} задач...")
    
    # Make a simple health check while AI requests are processing
    for i in range(5):
        try:
            health_start = time.time()
            response = requests.get(f'{API_BASE}/health', timeout=5)
            health_time = time.time() - health_start
            
            if response.status_code == 200:
                print(f"✅ Health check {i+1}: {health_time:.3f}s - API отзывчив")
            else:
                print(f"⚠️ Health check {i+1}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Health check {i+1} failed: {str(e)}")
        
        await asyncio.sleep(2)
    
    # Test 3: Monitor AI task progress
    print(f"\n📊 Мониторинг прогресса задач...")
    
    completed_tasks = set()
    max_wait_time = 300  # 5 minutes
    check_start = time.time()
    
    while len(completed_tasks) < len(task_ids) and (time.time() - check_start) < max_wait_time:
        for task_id in task_ids:
            if task_id in completed_tasks:
                continue
                
            try:
                response = requests.get(
                    f'{API_BASE}/ai/status/{task_id}',
                    headers=get_auth_headers(),
                    timeout=5
                )
                
                if response.status_code == 200:
                    status_data = response.json()
                    status = status_data.get('status')
                    stage = status_data.get('stage', '')
                    progress = status_data.get('progress', 0)
                    
                    print(f"📋 {task_id[:12]}: {status} - {stage} ({progress}%)")
                    
                    if status in ['completed', 'error', 'timeout']:
                        completed_tasks.add(task_id)
                        if status == 'completed' and 'result' in status_data:
                            result_preview = status_data['result'][:100] + "..." if len(status_data['result']) > 100 else status_data['result']
                            print(f"✅ Результат {task_id[:12]}: {result_preview}")
                        elif status == 'error':
                            print(f"❌ Ошибка {task_id[:12]}: {status_data.get('error', 'Unknown error')}")
                            
                elif response.status_code == 404:
                    print(f"❌ Задача {task_id[:12]} не найдена")
                    completed_tasks.add(task_id)  # Remove from monitoring
                else:
                    print(f"⚠️ Ошибка статуса {task_id[:12]}: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Ошибка проверки {task_id[:12]}: {str(e)}")
        
        if len(completed_tasks) < len(task_ids):
            await asyncio.sleep(10)  # Check every 10 seconds
    
    total_time = time.time() - start_time
    print(f"\n🏁 Тест завершен за {total_time:.1f} секунд")
    print(f"📈 Завершено задач: {len(completed_tasks)}/{len(task_ids)}")
    
    # Test 4: List all active tasks
    print(f"\n📋 Просмотр всех активных задач...")
    try:
        response = requests.get(
            f'{API_BASE}/ai/tasks',
            headers=get_auth_headers(),
            timeout=5
        )
        
        if response.status_code == 200:
            tasks_data = response.json()
            active_count = tasks_data.get('active_tasks', 0)
            max_concurrent = tasks_data.get('max_concurrent', 0)
            print(f"📊 Активных задач: {active_count}, Максимум одновременно: {max_concurrent}")
        else:
            print(f"⚠️ Ошибка получения списка задач: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка запроса списка задач: {str(e)}")

def test_multimedia_support():
    """Test multimedia data support"""
    print(f"\n🎬 Тестирование поддержки мультимедиа...")
    
    # Test image data
    test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    
    multimedia_request = {
        "prompt": "Проанализируй это изображение строительного чертежа",
        "model": "deepseek/deepseek-r1-0528-qwen3-8b",
        "image_data": test_image_b64
    }
    
    try:
        response = requests.post(
            f'{API_BASE}/ai',
            json=multimedia_request,
            headers=get_auth_headers(),
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Мультимедиа запрос принят: {result.get('task_id', 'No task ID')}")
        else:
            print(f"❌ Ошибка мультимедиа запроса: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Исключение мультимедиа теста: {str(e)}")

async def main():
    """Main test function"""
    print("🚀 Тестирование асинхронной AI архитектуры Bldr API")
    print("=" * 60)
    
    await test_concurrent_ai_requests()
    test_multimedia_support()
    
    print("\n✨ Все тесты завершены!")
    print("\n📋 Ключевые улучшения:")
    print("  🔄 Неблокирующая обработка AI запросов")
    print("  🚀 Поддержка множественных одновременных запросов")  
    print("  📊 Мониторинг прогресса через REST API")
    print("  🎬 Поддержка мультимедиа данных (фото, голос, документы)")
    print("  🌐 WebSocket уведомления о прогрессе")
    print("  🛡️ Ограничение количества одновременных задач")
    print("  🧹 Автоматическая очистка завершенных задач")

if __name__ == '__main__':
    asyncio.run(main())