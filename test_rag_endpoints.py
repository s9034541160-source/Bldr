#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test RAG API Endpoints
======================
Тестирование новых RAG эндпоинтов API
"""

import requests
import json
import time
import os
from dotenv import load_dotenv

# Загрузить переменные окружения
load_dotenv()

# Настройки API
API_BASE_URL = "http://localhost:8001"
API_TOKEN = "test_token_12345"  # Временный токен для тестирования

# Заголовки для аутентификации
headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def generate_test_token():
    """Создать тестовый JWT токен для авторизации"""
    import jwt
    from datetime import datetime, timedelta
    
    secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    
    payload = {
        "sub": "test_user",
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow()
    }
    
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return token

def test_api_server():
    """Проверить, что API сервер работает"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API server is running")
            print(f"   Status: {response.json()}")
            return True
        else:
            print(f"❌ API server error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API server: {e}")
        return False

def test_rag_search():
    """Тестировать RAG поиск"""
    print("\n🔍 Testing RAG Search Endpoint...")
    
    search_data = {
        "query": "строительные нормы",
        "k": 3,
        "threshold": 0.3,
        "include_metadata": True
    }
    
    try:
        # Генерировать корректный токен
        token = generate_test_token()
        test_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/rag/search",
            headers=test_headers,
            json=search_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ RAG Search successful")
            print(f"   Query: {result.get('query')}")
            print(f"   Results found: {result.get('total_found')}")
            print(f"   Processing time: {result.get('processing_time', 0):.2f}s")
            print(f"   Search method: {result.get('search_method')}")
            
            # Показать первый результат
            if result.get('results'):
                first_result = result['results'][0]
                print(f"   First result score: {first_result.get('score', 0):.3f}")
                print(f"   First result preview: {first_result.get('content', '')[:100]}...")
            
            return True
        else:
            print(f"❌ RAG Search failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ RAG Search error: {e}")
        return False

def test_rag_status():
    """Тестировать статус RAG системы"""
    print("\n📊 Testing RAG Status Endpoint...")
    
    try:
        # Генерировать корректный токен
        token = generate_test_token()
        test_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{API_BASE_URL}/api/rag/status",
            headers=test_headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ RAG Status successful")
            print(f"   Training: {'🔄' if result.get('is_training') else '⏸️'} {result.get('current_stage')}")
            print(f"   Progress: {result.get('progress')}%")
            print(f"   Message: {result.get('message')}")
            print(f"   Documents: {result.get('total_documents')}")
            print(f"   Chunks: {result.get('total_chunks')}")
            
            return True
        else:
            print(f"❌ RAG Status failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ RAG Status error: {e}")
        return False

def test_ai_chat():
    """Тестировать AI чат с RAG контекстом"""
    print("\n💬 Testing AI Chat Endpoint...")
    
    chat_data = {
        "message": "Расскажи о строительных нормах",
        "context_search": True,
        "max_context": 2,
        "agent_role": "coordinator"
    }
    
    try:
        # Генерировать корректный токен
        token = generate_test_token()
        test_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/ai/chat",
            headers=test_headers,
            json=chat_data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ AI Chat successful")
            print(f"   Agent used: {result.get('agent_used')}")
            print(f"   Context documents: {len(result.get('context_used', []))}")
            print(f"   Processing time: {result.get('processing_time', 0):.2f}s")
            print(f"   Response preview: {result.get('response', '')[:150]}...")
            
            return True
        else:
            print(f"❌ AI Chat failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ AI Chat error: {e}")
        return False

def test_existing_query_endpoint():
    """Тестировать существующий /query эндпоинт для сравнения"""
    print("\n🔍 Testing Existing Query Endpoint...")
    
    query_data = {
        "query": "строительные нормы",
        "k": 3
    }
    
    try:
        # Генерировать корректный токен
        token = generate_test_token()
        test_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/query",
            headers=test_headers,
            json=query_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Existing Query successful")
            print(f"   Results found: {len(result.get('results', []))}")
            print(f"   NDCG score: {result.get('ndcg', 0):.3f}")
            
            # Показать первый результат
            if result.get('results'):
                first_result = result['results'][0]
                print(f"   First result score: {first_result.get('score', 0):.3f}")
                print(f"   First result preview: {first_result.get('chunk', '')[:100]}...")
            
            return True
        else:
            print(f"❌ Existing Query failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Existing Query error: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🧪 RAG API Endpoints Testing")
    print("=" * 50)
    
    # Проверить подключение к серверу
    if not test_api_server():
        print("\n❌ Cannot proceed without API server")
        return
    
    # Подождать немного для стабилизации
    time.sleep(2)
    
    # Запустить тесты
    tests = [
        test_rag_status,
        test_rag_search, 
        test_existing_query_endpoint,
        test_ai_chat
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            time.sleep(1)  # Пауза между тестами
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
    
    # Итоговые результаты
    print("\n" + "=" * 50)
    print(f"🧪 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! RAG API endpoints are working correctly.")
    else:
        print(f"⚠️ {total - passed} tests failed. Check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)