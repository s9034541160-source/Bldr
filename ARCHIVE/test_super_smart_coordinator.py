#!/usr/bin/env python3
"""
Тест СУПЕР-УМНОГО КООРДИНАТОРА с реальным LLM
"""

import requests
import json
from datetime import datetime

# Конфигурация
BACKEND_URL = "http://localhost:8000"
TEST_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTc5MDAwNDY4NX0.hVYULUk7tjUFUNAVSOulnNy6sQXFozEiel3b2tSNhME"

def test_coordinator(query: str):
    """Тестируем координатор с реальным запросом"""
    print(f"\n{'='*60}")
    print(f"🧠 ТЕСТИРУЕМ: {query}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/ai/chat",
            headers={
                "Authorization": f"Bearer {TEST_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "message": query,
                "context_search": True,
                "agent_role": "coordinator"
            },
            timeout=30  # 30 секунд таймаут
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ STATUS: {result.get('status', 'unknown')}")
            print(f"📝 ОТВЕТ:")
            print(f"{result.get('response', 'Нет ответа')}")
            
            if result.get('execution_summary'):
                print(f"\n⚡ ВЫПОЛНЕНИЕ: {result['execution_summary']}")
            
            if result.get('context_used'):
                print(f"\n📚 КОНТЕКСТ: {len(result['context_used'])} документов")
            
            return True
        else:
            print(f"❌ ОШИБКА HTTP: {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ОШИБКА ЗАПРОСА: {e}")
        return False

def main():
    """Главная функция тестирования"""
    print(f"""
🚀 ТЕСТИРУЕМ СУПЕР-УМНОГО КООРДИНАТОРА v2.0
==========================================
Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Backend: {BACKEND_URL}
    """)
    
    # Список тестовых запросов
    test_queries = [
        "сделай чек-лист мастера СМР",
        "что нужно для земляных работ",
        "проверь СП по фундаментам",
        "смета на котлован 100 куб.м.",
        "требования безопасности стройплощадки"
    ]
    
    success_count = 0
    total_count = len(test_queries)
    
    for query in test_queries:
        if test_coordinator(query):
            success_count += 1
        
        print(f"\n{'.'*60}")
        input("Нажмите Enter для следующего теста...")
    
    print(f"\n{'='*60}")
    print(f"📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"✅ Успешных: {success_count}/{total_count}")
    print(f"❌ Неудачных: {total_count - success_count}/{total_count}")
    print(f"📈 Процент успеха: {success_count/total_count*100:.1f}%")
    
    if success_count == total_count:
        print(f"\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! КООРДИНАТОР РАБОТАЕТ!")
    else:
        print(f"\n⚠️  Есть проблемы, требуется доработка...")

if __name__ == "__main__":
    main()