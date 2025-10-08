#!/usr/bin/env python3
"""
Простой тест API на порту 8000
"""

import requests
import json

def test_api():
    """Простое тестирование API"""
    base_url = "http://localhost:8000"
    
    # 1. Health check
    print("1️⃣ Тестируем health...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Ошибка: {e}")
    
    # 2. RAG query test
    print("\n2️⃣ Тестируем RAG поиск...")
    try:
        query_data = {
            "query": "СП 31",
            "k": 3
        }
        response = requests.post(f"{base_url}/query", json=query_data, timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            results_count = len(data.get('results', []))
            print(f"   Найдено результатов: {results_count}")
            print(f"   NDCG: {data.get('ndcg', 'N/A')}")
        else:
            print(f"   Ошибка: {response.text}")
    except Exception as e:
        print(f"   Ошибка: {e}")
    
    # 3. AI request test
    print("\n3️⃣ Тестируем AI запрос...")
    try:
        ai_data = {
            "prompt": "Привет! Это тест AI системы",
            "model": "deepseek/deepseek-r1-0528-qwen3-8b"
        }
        response = requests.post(f"{base_url}/ai", json=ai_data, timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Статус: {data.get('status')}")
            print(f"   Task ID: {data.get('task_id', 'N/A')}")
        else:
            print(f"   Ошибка: {response.text}")
    except Exception as e:
        print(f"   Ошибка: {e}")

    # 4. Coordinator test
    print("\n4️⃣ Тестируем координатор...")
    try:
        coord_data = {
            "query": "Создай смету для строительства беседки 4x4 метра",
            "source": "test",
            "user_id": "test_user"
        }
        response = requests.post(f"{base_url}/submit_query", json=coord_data, timeout=60)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Статус: {data.get('status')}")
            has_plan = 'plan' in data
            has_results = 'results' in data
            print(f"   Есть план: {has_plan}")
            print(f"   Есть результаты: {has_results}")
        else:
            print(f"   Ошибка: {response.text}")
    except Exception as e:
        print(f"   Ошибка: {e}")

if __name__ == "__main__":
    print("🚀 Простое тестирование API на порту 8000")
    print("=" * 50)
    test_api()
    print("\n✅ Тестирование завершено!")