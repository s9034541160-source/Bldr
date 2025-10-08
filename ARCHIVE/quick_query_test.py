#!/usr/bin/env python3
"""
Quick test for current query functionality
"""

import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

def test_query():
    API_TOKEN = os.getenv('API_TOKEN')
    headers = {
        'Authorization': f'Bearer {API_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    print("🔍 Тестирование текущего состояния системы запросов...")
    
    test_queries = [
        "строительство",
        "бетон", 
        "документ",
        "требования"
    ]
    
    for query in test_queries:
        print(f"\n🎯 Тест запроса: '{query}'")
        
        try:
            response = requests.post(
                'http://localhost:8000/query',
                json={'query': query, 'k': 3},
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                ndcg = data.get('ndcg', 0)
                
                print(f"   ✅ Статус: 200 OK")
                print(f"   📊 Результатов: {len(results)}")
                print(f"   📈 NDCG: {ndcg}")
                
                if results:
                    best_result = results[0]
                    score = best_result.get('score', 0)
                    chunk = best_result.get('chunk', '')[:100]
                    print(f"   🎯 Лучший score: {score:.3f}")
                    print(f"   📄 Превью: {chunk}...")
                else:
                    print("   ⚠️ Результатов не найдено")
                    
            else:
                print(f"   ❌ HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Исключение: {str(e)}")
    
    # Проверим также состояние trainer
    print(f"\n📊 Проверка состояния trainer...")
    try:
        # Попробуем получить информацию о trainer через API
        health_response = requests.get('http://localhost:8000/health', timeout=10)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"   🏥 Health status: {health_data.get('status', 'unknown')}")
            
            components = health_data.get('components', {})
            for component, status in components.items():
                print(f"   📦 {component}: {status}")
        
    except Exception as e:
        print(f"   ❌ Ошибка health check: {str(e)}")

if __name__ == '__main__':
    test_query()