#!/usr/bin/env python3
"""
Быстрая проверка статуса системы и исправлений
"""

import requests
import json
import os
from pathlib import Path

BASE_URL = "http://localhost:8001"

def check_api():
    """Быстрая проверка API"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API работает")
            return True
        else:
            print(f"❌ API проблема: {response.status_code}")
            return False
    except:
        print("❌ API недоступен")
        return False

def check_training():
    """Проверить статус обучения"""
    try:
        response = requests.get(f"{BASE_URL}/api/training/status", timeout=5)
        if response.status_code == 200:
            status = response.json()
            is_training = status.get('is_training', False)
            progress = status.get('progress', 0)
            stage = status.get('current_stage', 'unknown')
            
            if is_training:
                print(f"🔄 Обучение в процессе: {progress}% - {stage}")
            else:
                print("⏸️ Обучение не активно")
            return True
        else:
            print("❌ Не удалось получить статус обучения")
            return False
    except:
        print("❌ Ошибка проверки обучения")
        return False

def check_search():
    """Быстрый тест поиска"""
    try:
        search_data = {
            "query": "СП 31",
            "limit": 3
        }
        
        response = requests.post(
            f"{BASE_URL}/api/search", 
            json=search_data,
            timeout=10
        )
        
        if response.status_code == 200:
            results = response.json()
            count = len(results.get('results', []))
            if count > 0:
                print(f"✅ Поиск работает: найдено {count} результатов")
            else:
                print("⚠️ Поиск работает, но результатов нет (обучение не завершено?)")
            return True
        else:
            print("❌ Поиск не работает")
            return False
    except:
        print("❌ Ошибка поиска")
        return False

def check_files():
    """Проверить ключевые файлы"""
    files_to_check = [
        ("App.tsx", "C:\\Bldr\\web\\bldr_dashboard\\src\\App.tsx"),
        ("ProFeatures.tsx", "C:\\Bldr\\web\\bldr_dashboard\\src\\components\\ProFeatures.tsx"),
        ("FileManager.tsx", "C:\\Bldr\\web\\bldr_dashboard\\src\\components\\FileManager.tsx"),
        ("api.ts", "C:\\Bldr\\web\\bldr_dashboard\\src\\services\\api.ts"),
    ]
    
    print("\n📁 Проверка файлов:")
    for name, path in files_to_check:
        if os.path.exists(path):
            print(f"   ✅ {name}")
        else:
            print(f"   ❌ {name} отсутствует")

def main():
    print("⚡ Быстрая проверка статуса системы")
    print("=" * 40)
    
    # Проверяем файлы
    check_files()
    
    print("\n🌐 Проверка API:")
    
    # Проверяем API
    if check_api():
        check_training()
        check_search()
    else:
        print("\n💡 Для запуска сервера:")
        print("   python start_api_server.py")
    
    print("\n🔍 Для полного тестирования:")
    print("   python test_fixes.py")

if __name__ == "__main__":
    main()