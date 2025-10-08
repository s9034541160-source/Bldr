#!/usr/bin/env python3
"""
Быстрая проверка прогресса поиска после запуска обучения
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE = "http://localhost:8000"
API_TOKEN = os.getenv("API_TOKEN")

def test_quick_search():
    """Быстрый тест поиска"""
    if not API_TOKEN:
        print("❌ Нет токена API")
        return
    
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    
    test_queries = [
        "строительные нормы",
        "ГОСТ",
        "СП", 
        "техническое регулирование"
    ]
    
    print("🔍 Быстрая проверка поиска после запуска обучения:")
    print("=" * 50)
    
    total_results = 0
    
    for query in test_queries:
        try:
            response = requests.post(
                f"{API_BASE}/query",
                json={"query": query, "k": 3},
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                count = len(results)
                total_results += count
                
                print(f"✅ '{query}': {count} результатов")
                
                if count > 0:
                    # Показываем первый результат
                    first = results[0]
                    chunk = first.get('chunk', '')[:100]
                    score = first.get('score', 0)
                    print(f"   📄 [{score:.3f}] {chunk}...")
                    
            else:
                print(f"❌ '{query}': ошибка {response.status_code}")
                print(f"   {response.text}")
                
        except Exception as e:
            print(f"⚠️ '{query}': {e}")
    
    print()
    print(f"📊 Всего результатов: {total_results}")
    
    if total_results == 0:
        print("ℹ️  Пока нет результатов - обучение продолжается")
        print("🔄 Попробуйте через несколько минут")
    elif total_results < 5:
        print("⚡ Начальные результаты появляются!")
        print("🔄 Обучение активно продолжается")  
    else:
        print("🎉 Отлично! RAG система уже работает")
        print("💡 Можно тестировать более сложные запросы")

if __name__ == "__main__":
    test_quick_search()