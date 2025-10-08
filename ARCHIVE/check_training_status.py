#!/usr/bin/env python3
"""
Проверка статуса RAG обучения
"""

import requests
import os
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_BASE = "http://localhost:8000"
API_TOKEN = os.getenv("API_TOKEN")

def check_api_status():
    """Проверка статуса API"""
    print(f"🔍 Проверка статуса RAG системы - {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 50)
    
    if not API_TOKEN:
        print("❌ Нет API токена")
        return False
    
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    
    # 1. Проверка API
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        if response.status_code == 200:
            print("✅ API доступен")
        else:
            print(f"❌ API недоступен: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка API: {e}")
        return False
    
    # 2. Тестовый поиск
    print("\n🔍 Тестовый поиск...")
    search_queries = [
        "строительные нормы",
        "ГОСТ", 
        "СП",
        "железобетон"
    ]
    
    total_results = 0
    for query in search_queries:
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
                
                if count > 0:
                    print(f"   ✅ '{query}': {count} результатов")
                    # Показываем первый результат
                    first = results[0]
                    chunk = first.get('chunk', '')[:100]
                    score = first.get('score', 0)
                    print(f"      📄 [{score:.3f}] {chunk}...")
                else:
                    print(f"   ⚪ '{query}': нет результатов")
            else:
                print(f"   ❌ '{query}': ошибка {response.status_code}")
                
        except Exception as e:
            print(f"   ⚠️ '{query}': {e}")
    
    print(f"\n📊 Всего найдено результатов: {total_results}")
    
    if total_results == 0:
        print("ℹ️  Обучение ещё продолжается или не запущено")
    elif total_results < 5:
        print("⚡ Первые результаты появляются! Обучение работает")
    else:
        print("🎉 Система активно работает!")
    
    return True

def check_file_activity():
    """Проверка активности в папках"""
    print("\n📁 Проверка файловой активности...")
    
    paths_to_check = [
        ("I:/docs/downloaded", "Исходные НТД"),
        ("I:/docs/clean_base", "Обработанные файлы"),
        ("I:/docs/reports", "Отчёты системы"),
        ("C:/Bldr/data", "Данные системы")
    ]
    
    for path, description in paths_to_check:
        try:
            if os.path.exists(path):
                files = len([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))])
                print(f"   📂 {description}: {files} файлов")
            else:
                print(f"   ❌ {description}: папка не найдена")
        except Exception as e:
            print(f"   ⚠️ {description}: ошибка {e}")

def main():
    """Основная проверка"""
    success = check_api_status()
    if success:
        check_file_activity()
        
        print(f"\n💡 Рекомендации:")
        print("   - Запускайте эту проверку каждые 10-15 минут")
        print("   - Следите за появлением результатов поиска")  
        print("   - Обучение 1168 файлов займёт 2-4 часа")
    
    print(f"\n🕐 Проверка завершена: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()