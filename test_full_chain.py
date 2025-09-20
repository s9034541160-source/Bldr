#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ТЕСТ ПОЛНОЙ ЦЕПОЧКИ ОБРАБОТКИ ЗАПРОСОВ
=====================================

Проверяет цепочку:
ТГ-бот/Фронт → API → Координатор → Master Tools → Координатор → API → Ответ

ЦЕЛЬ: Убедиться что вся цепочка работает БЕЗ моков и заглушек
"""

import os
import sys
import requests
import json
import time
from datetime import datetime

# Add path for imports
sys.path.append('C:/Bldr/core')

def test_api_connection():
    """Тест соединения с API"""
    print("🔌 Testing API connection...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ API connection OK: {health_data.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ API not reachable - make sure server is running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ API connection error: {e}")
        return False

def test_master_tools_integration():
    """Тест интеграции Master Tools System"""
    print("🔧 Testing Master Tools System integration...")
    
    try:
        from master_tools_system import MasterToolsSystem, get_master_tools_system
        from tools_adapter import get_tools_adapter
        
        # Test Master Tools System
        mts = MasterToolsSystem()
        tools_info = mts.list_all_tools()
        print(f"✅ Master Tools System: {tools_info['total_count']} tools available")
        
        # Test adapter
        adapter = get_tools_adapter()
        health = adapter.health_check()
        print(f"✅ Tools Adapter: {health['system_status']}, {health['total_tools']} tools")
        
        return True
        
    except ImportError as e:
        print(f"❌ Master Tools import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Master Tools test error: {e}")
        return False

def test_coordinator_integration():
    """Тест интеграции координатора"""
    print("🧠 Testing Coordinator integration...")
    
    try:
        from agents.coordinator_agent import CoordinatorAgent
        
        # Create coordinator
        coordinator = CoordinatorAgent()
        
        # Test plan generation
        test_query = "Привет, расскажи о строительных нормах для фундамента"
        plan = coordinator.generate_plan(test_query)
        print(f"✅ Plan generated: {type(plan)} - {len(str(plan))} chars")
        
        # Test response generation
        response = coordinator.generate_response(test_query)
        if isinstance(response, dict):
            print(f"✅ Response generated: status={response.get('status')}, {len(response.get('response', ''))} chars")
        else:
            print(f"✅ Response generated: {len(str(response))} chars")
        
        return True
        
    except ImportError as e:
        print(f"❌ Coordinator import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Coordinator test error: {e}")
        return False

def test_ai_chat_endpoint():
    """Тест AI chat endpoint через API"""
    print("💬 Testing AI Chat endpoint...")
    
    # Skip auth if configured
    headers = {
        "Content-Type": "application/json"
    }
    
    # Try to get API token
    api_token = os.getenv('API_TOKEN')
    if api_token:
        headers['Authorization'] = f'Bearer {api_token}'
    
    test_cases = [
        {
            "name": "Simple greeting",
            "payload": {
                "message": "Привет! Расскажи о себе",
                "context_search": False,
                "max_context": 2
            },
            "expected_agent": ["coordinator", "coordinator_with_tools", "fallback_llm"]
        },
        {
            "name": "Construction norms query",
            "payload": {
                "message": "Какие требования к железобетонным фундаментам по СП 63.13330?",
                "context_search": True,
                "max_context": 3
            },
            "expected_agent": ["coordinator", "coordinator_with_tools"]
        },
        {
            "name": "Complex request with tools",
            "payload": {
                "message": "Создай круговую диаграмму распределения стоимости строительства: материалы 60%, работа 25%, накладные 15%",
                "context_search": False,
                "max_context": 2
            },
            "expected_agent": ["coordinator", "coordinator_with_tools"]
        }
    ]
    
    passed = 0
    total = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}/{total}: {test_case['name']}")
        
        try:
            start_time = time.time()
            response = requests.post(
                "http://localhost:8000/api/ai/chat",
                json=test_case["payload"],
                headers=headers,
                timeout=30
            )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                agent_used = data.get("agent_used", "unknown")
                response_text = data.get("response", "")
                context_used = data.get("context_used", [])
                api_processing_time = data.get("processing_time", 0)
                
                print(f"✅ Status: 200 OK")
                print(f"📊 Agent: {agent_used}")
                print(f"⏱️ Processing time: {api_processing_time:.2f}s (total: {processing_time:.2f}s)")
                print(f"📝 Response length: {len(response_text)} chars")
                print(f"📁 Context used: {len(context_used)} documents")
                
                if response_text and len(response_text) > 10:
                    print(f"📄 Response preview: {response_text[:100]}...")
                    passed += 1
                    print("✅ Test PASSED")
                else:
                    print("❌ Test FAILED: Empty or too short response")
                    
            else:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.Timeout:
            print("❌ Request timeout (30s)")
        except Exception as e:
            print(f"❌ Request error: {e}")
    
    print(f"\n🏁 AI Chat endpoint tests: {passed}/{total} passed")
    return passed == total

def test_telegram_simulation():
    """Симуляция запроса от ТГ-бота"""
    print("📱 Testing Telegram bot simulation...")
    
    headers = {
        "Content-Type": "application/json"
    }
    
    api_token = os.getenv('API_TOKEN')
    if api_token:
        headers['Authorization'] = f'Bearer {api_token}'
    
    # Simulate Telegram context
    telegram_payload = {
        "message": "Проверь норматив СП 20.13330 для нагрузок на здания",
        "context_search": True,
        "max_context": 3,
        "agent_role": "coordinator",
        "request_context": {
            "channel": "telegram",
            "chat_id": "test_chat_123",
            "user_id": "test_user_456"
        }
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            "http://localhost:8000/api/ai/chat",
            json=telegram_payload,
            headers=headers,
            timeout=60  # Longer timeout for complex processing
        )
        
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Telegram simulation successful")
            print(f"📊 Agent: {data.get('agent_used')}")
            print(f"⏱️ Time: {data.get('processing_time', 0):.2f}s")
            print(f"📝 Response: {len(data.get('response', ''))} chars")
            return True
        else:
            print(f"❌ Telegram simulation failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Telegram simulation error: {e}")
        return False

def test_full_chain_end_to_end():
    """Полный end-to-end тест цепочки"""
    print("\n" + "="*60)
    print("🚀 FULL CHAIN END-TO-END TEST")
    print("="*60)
    
    tests = [
        ("API Connection", test_api_connection),
        ("Master Tools Integration", test_master_tools_integration), 
        ("Coordinator Integration", test_coordinator_integration),
        ("AI Chat Endpoint", test_ai_chat_endpoint),
        ("Telegram Simulation", test_telegram_simulation)
    ]
    
    passed = 0
    total = len(tests)
    start_time = time.time()
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: EXCEPTION - {e}")
    
    total_time = time.time() - start_time
    
    print(f"\n{'='*60}")
    print(f"🏁 FINAL RESULTS:")
    print(f"✅ Passed: {passed}/{total} tests")
    print(f"⏱️ Total time: {total_time:.2f} seconds")
    print(f"📊 Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Chain is working correctly!")
        return True
    else:
        print("⚠️ Some tests failed. Check the issues above.")
        return False

if __name__ == "__main__":
    print(f"🧪 Starting Full Chain Test at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📍 Working directory: {os.getcwd()}")
    print(f"🐍 Python path: {sys.path[:3]}...")
    
    success = test_full_chain_end_to_end()
    exit(0 if success else 1)