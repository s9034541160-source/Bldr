#!/usr/bin/env python3
"""
Тест исправлений фронтенда и бэкенда
Проверяет работу всех функций после применения патчей
"""

import requests
import json
import time
import os
import sys
from pathlib import Path

BASE_URL = "http://localhost:8001"

def test_api_health():
    """Проверить состояние API"""
    print("🔍 Проверяем состояние API...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API работает: {data}")
            return True
        else:
            print(f"❌ API проблема: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к API: {e}")
        return False

def test_rag_search():
    """Тестировать поиск RAG"""
    print("\n🔍 Тестируем поиск RAG...")
    try:
        search_data = {
            "query": "строительные нормы",
            "limit": 5,
            "include_metadata": True
        }
        
        response = requests.post(
            f"{BASE_URL}/api/search", 
            json=search_data,
            timeout=30
        )
        
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Поиск работает, найдено: {len(results.get('results', []))} результатов")
            if results.get('results'):
                for i, result in enumerate(results['results'][:2], 1):
                    score = result.get('score', 0)
                    text_preview = result.get('text', '')[:100] + '...'
                    print(f"   {i}. Score: {score:.3f} - {text_preview}")
            return True
        else:
            print(f"❌ Поиск не работает: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Ошибка поиска: {e}")
        return False

def test_training_status():
    """Проверить статус обучения"""
    print("\n🔍 Проверяем статус обучения...")
    try:
        response = requests.get(f"{BASE_URL}/api/training/status")
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Статус обучения: {status}")
            return status.get('is_training', False)
        else:
            print(f"❌ Не удалось получить статус: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка получения статуса: {e}")
        return False

def test_tender_analysis():
    """Тестировать анализ тендера"""
    print("\n🔍 Тестируем анализ тендера...")
    try:
        tender_data = {
            "tender_data": {
                "id": "test-tender-001",
                "name": "Строительство офисного здания", 
                "value": 5000000
            },
            "project_id": "test-project",
            "requirements": [
                "СП 31-13330",
                "ГОСТ Р 21.1101-2013"
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/analyze-tender",
            json=tender_data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Анализ тендера работает: {result.get('status', 'Unknown')}")
            return True
        else:
            print(f"❌ Анализ тендера не работает: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Ошибка анализа тендера: {e}")
        return False

def test_letter_generation():
    """Тестировать генерацию писем"""
    print("\n🔍 Тестируем генерацию писем...")
    try:
        letter_data = {
            "template_id": "compliance_sp31",
            "recipient": "Управление архитектуры",
            "sender": "АО БЛДР",
            "subject": "Соответствие проекта СП31",
            "problem_description": "Необходимо подтвердить соответствие проекта требованиям СП31"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/generate-letter",
            json=letter_data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Генерация писем работает: {result.get('status', 'Unknown')}")
            return True
        else:
            print(f"❌ Генерация писем не работает: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Ошибка генерации писем: {e}")
        return False

def test_file_scanning():
    """Тестировать сканирование файлов"""  
    print("\n🔍 Тестируем сканирование файлов...")
    try:
        scan_data = {
            "path": "I:/docs/downloaded"  # Используем дефолтный путь
        }
        
        response = requests.post(
            f"{BASE_URL}/api/scan-files",
            json=scan_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Сканирование файлов работает: просканировано {result.get('scanned', 0)}, скопировано {result.get('copied', 0)}")
            return True
        else:
            print(f"❌ Сканирование не работает: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Ошибка сканирования: {e}")
        return False

def check_frontend_files():
    """Проверить что файлы фронтенда существуют и исправлены"""
    print("\n🔍 Проверяем файлы фронтенда...")
    
    frontend_files = {
        "App.tsx": "C:\\Bldr\\web\\bldr_dashboard\\src\\App.tsx",
        "ProFeatures.tsx": "C:\\Bldr\\web\\bldr_dashboard\\src\\components\\ProFeatures.tsx", 
        "ProTools.tsx": "C:\\Bldr\\web\\bldr_dashboard\\src\\components\\ProTools.tsx",
        "FileManager.tsx": "C:\\Bldr\\web\\bldr_dashboard\\src\\components\\FileManager.tsx"
    }
    
    for name, path in frontend_files.items():
        if os.path.exists(path):
            print(f"✅ {name} найден")
            
            # Проверяем специфические исправления
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                if name == "App.tsx":
                    if "useAuthStore" in content and "localStorage.getItem('auth-token')" in content:
                        print(f"   ✅ {name} содержит исправления для токенов")
                    else:
                        print(f"   ⚠️ {name} может не содержать всех исправлений")
                        
                elif name == "ProFeatures.tsx":
                    if "tender_data:" in content and "problem_description" in content:
                        print(f"   ✅ {name} содержит исправления")
                    else:
                        print(f"   ⚠️ {name} может не содержать всех исправлений")
                        
                elif name == "FileManager.tsx":
                    if "trainingPath" in content and "custom_dir: trainingPath" in content:
                        print(f"   ✅ {name} содержит исправления")
                    else:
                        print(f"   ⚠️ {name} может не содержать всех исправлений")
        else:
            print(f"❌ {name} не найден по пути {path}")

def main():
    """Главная функция тестирования"""
    print("🚀 Запуск полного теста исправлений системы")
    print("=" * 60)
    
    # Проверяем файлы фронтенда
    check_frontend_files()
    
    # Тестируем API
    if not test_api_health():
        print("\n❌ API недоступен, прекращаем тесты")
        return
    
    # Тестируем различные функции
    tests = [
        test_training_status,
        test_rag_search, 
        test_file_scanning,
        test_tender_analysis,
        test_letter_generation,
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
            time.sleep(1)  # Небольшая пауза между тестами
        except Exception as e:
            print(f"❌ Ошибка в тесте {test_func.__name__}: {e}")
            results.append(False)
    
    # Итоговый отчет
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 60)
    
    passed = sum(1 for r in results if r)
    total = len(results)
    
    print(f"✅ Пройдено: {passed}/{total} тестов")
    
    if passed == total:
        print("🎉 Все тесты прошли успешно!")
    elif passed >= total * 0.7:
        print("⚠️ Большинство тестов прошли, есть мелкие проблемы")
    else:
        print("❌ Много проблем, требуется дополнительная диагностика")
        
    # Рекомендации
    print("\n📋 РЕКОМЕНДАЦИИ:")
    if not results[0]:  # training_status
        print("- Проверить статус обучения RAG")
    if not results[1]:  # rag_search  
        print("- Возможно, обучение RAG еще не завершено")
    if not results[2]:  # file_scanning
        print("- Проверить доступность папок для сканирования")
    if not results[3]:  # tender_analysis
        print("- Проверить работу анализа тендеров")
    if not results[4]:  # letter_generation
        print("- Проверить работу генерации писем")
        
    print("\n🔄 Для повторного запуска: python test_fixes.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ Тестирование прервано пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")