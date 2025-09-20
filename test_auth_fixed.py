#!/usr/bin/env python3
"""
Тест API с правильным токеном аутентификации
"""

import requests
import json
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def test_api_with_auth():
    """Тестирование API с токеном из .env файла"""
    base_url = "http://localhost:8000"
    
    # Получаем токен из .env
    api_token = os.getenv('API_TOKEN')
    if not api_token:
        print("❌ API_TOKEN не найден в .env файле!")
        return
    
    print(f"🔑 Используем токен: {api_token[:20]}...")
    
    # Подготавливаем заголовки с токеном
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # 1. Health check (без токена)
    print("1️⃣ Health check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Ошибка: {e}")
    
    # 2. RAG query test (с токеном)
    print("\n2️⃣ Тестируем RAG поиск с токеном...")
    try:
        query_data = {
            "query": "СП 31",
            "k": 3
        }
        response = requests.post(f"{base_url}/query", json=query_data, headers=headers, timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            results_count = len(data.get('results', []))
            print(f"   ✅ Найдено результатов: {results_count}")
            print(f"   NDCG: {data.get('ndcg', 'N/A')}")
            if results_count > 0:
                first_result = data['results'][0]
                print(f"   Первый результат: {first_result.get('chunk', '')[:100]}...")
        else:
            print(f"   ❌ Ошибка: {response.text}")
    except Exception as e:
        print(f"   Ошибка: {e}")
    
    # 3. AI request test (с токеном)
    print("\n3️⃣ Тестируем AI запрос с токеном...")
    try:
        ai_data = {
            "prompt": "Привет! Это тест AI системы",
            "model": "deepseek/deepseek-r1-0528-qwen3-8b"
        }
        response = requests.post(f"{base_url}/ai", json=ai_data, headers=headers, timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Статус: {data.get('status')}")
            print(f"   Task ID: {data.get('task_id', 'N/A')}")
        else:
            print(f"   ❌ Ошибка: {response.text}")
    except Exception as e:
        print(f"   Ошибка: {e}")

    # 4. Coordinator test (с токеном)
    print("\n4️⃣ Тестируем координатор с токеном...")
    try:
        coord_data = {
            "query": "Создай смету для строительства беседки 4x4 метра",
            "source": "test",
            "user_id": "test_user"
        }
        response = requests.post(f"{base_url}/submit_query", json=coord_data, headers=headers, timeout=60)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Статус: {data.get('status')}")
            has_plan = 'plan' in data
            has_results = 'results' in data
            print(f"   Есть план: {has_plan}")
            print(f"   Есть результаты: {has_results}")
            if has_plan and data['plan']:
                plan = data['plan']
                print(f"   Тип запроса: {plan.get('query_type', 'N/A')}")
                tools = plan.get('tools', [])
                if tools:
                    tool_names = [tool.get('name', 'unknown') for tool in tools]
                    print(f"   Инструменты: {', '.join(tool_names)}")
        else:
            print(f"   ❌ Ошибка: {response.text}")
    except Exception as e:
        print(f"   Ошибка: {e}")

    # 5. Training endpoint search
    print("\n5️⃣ Ищем правильный training endpoint...")
    
    # Попробуем разные варианты
    training_endpoints = [
        "/api/training/status",
        "/training/status", 
        "/train/status",
        "/training-status"
    ]
    
    for endpoint in training_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", headers=headers, timeout=10)
            print(f"   {endpoint}: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ Найден! Ответ: {response.json()}")
                break
        except Exception as e:
            print(f"   {endpoint}: Ошибка - {e}")

if __name__ == "__main__":
    print("🚀 Тестирование API с аутентификацией")
    print("=" * 50)
    test_api_with_auth()
    print("\n✅ Тестирование завершено!")