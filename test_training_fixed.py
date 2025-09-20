#!/usr/bin/env python3
"""
Test script for the fixed training functionality
Tests the corrected background task execution and status tracking
"""

import requests
import time
import json
from dotenv import load_dotenv
import os

load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')
headers = {
    'Authorization': f'Bearer {API_TOKEN}',
    'Content-Type': 'application/json'
}

def test_training_functionality():
    print("🔧 Тестирование исправленной функциональности обучения")
    print("=" * 60)
    
    # Test 1: Check API health
    print("📡 Шаг 1: Проверка API...")
    try:
        health_response = requests.get('http://localhost:8000/health', timeout=10)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"✅ API статус: {health_data.get('status', 'unknown')}")
        else:
            print(f"❌ API недоступен: {health_response.status_code}")
            return
    except Exception as e:
        print(f"❌ Ошибка подключения к API: {str(e)}")
        return
    
    # Test 2: Check initial training status
    print("\n📊 Шаг 2: Проверка начального статуса обучения...")
    try:
        status_response = requests.get(
            'http://localhost:8000/api/training/status',
            headers=headers,
            timeout=10
        )
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            print(f"✅ Статус получен:")
            print(f"   🔄 is_training: {status_data.get('is_training', False)}")
            print(f"   📈 progress: {status_data.get('progress', 0)}%")
            print(f"   🏷️ stage: {status_data.get('current_stage', 'unknown')}")
            print(f"   💬 message: {status_data.get('message', 'No message')}")
        else:
            print(f"❌ Ошибка получения статуса: {status_response.status_code}")
            
    except Exception as e:
        print(f"❌ Исключение статуса: {str(e)}")
    
    # Test 3: Start training on a small test directory
    print("\n🚀 Шаг 3: Запуск обучения на тестовой директории...")
    
    # Use a smaller directory for testing
    test_directories = [
        "C:\\Bldr\\test_docs",
        "C:\\Bldr\\docs", 
        "I:\\docs\\база"
    ]
    
    test_dir = None
    for directory in test_directories:
        if os.path.exists(directory):
            test_dir = directory
            print(f"✅ Используем тестовую директорию: {test_dir}")
            break
    
    if not test_dir:
        print("⚠️ Не найдено тестовых директорий, используем основную:")
        test_dir = "I:\\docs\\downloaded"
    
    try:
        train_response = requests.post(
            'http://localhost:8000/train',
            json={'custom_dir': test_dir},
            headers=headers,
            timeout=30
        )
        
        if train_response.status_code == 200:
            train_data = train_response.json()
            print(f"✅ Обучение запущено:")
            print(f"   📁 Директория: {train_data.get('custom_dir', 'N/A')}")
            print(f"   💬 Сообщение: {train_data.get('message', 'N/A')}")
        else:
            print(f"❌ Ошибка запуска обучения: {train_response.status_code}")
            print(f"   Ответ: {train_response.text}")
            return
            
    except Exception as e:
        print(f"❌ Исключение при запуске обучения: {str(e)}")
        return
    
    # Test 4: Monitor training progress
    print(f"\n📊 Шаг 4: Мониторинг прогресса обучения (3 минуты)...")
    
    start_time = time.time()
    max_duration = 180  # 3 minutes
    check_interval = 10  # Check every 10 seconds
    
    training_started = False
    training_completed = False
    
    while (time.time() - start_time) < max_duration and not training_completed:
        try:
            status_response = requests.get(
                'http://localhost:8000/api/training/status',
                headers=headers,
                timeout=10
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                is_training = status_data.get('is_training', False)
                progress = status_data.get('progress', 0)
                stage = status_data.get('current_stage', 'unknown')
                message = status_data.get('message', 'No message')
                elapsed_api = status_data.get('elapsed_seconds', 0)
                
                elapsed_test = int(time.time() - start_time)
                
                print(f"   [{elapsed_test:3}s] 📈 {stage}: {message}")
                print(f"           🎯 Progress: {progress}% | Training: {is_training} | API elapsed: {elapsed_api}s")
                
                # Check if training actually started
                if is_training and not training_started:
                    print("🎉 Обучение действительно началось!")
                    training_started = True
                
                # Check if training completed
                if not is_training and training_started and progress >= 100:
                    print("🎉 Обучение завершено!")
                    training_completed = True
                    break
                elif not is_training and training_started and stage == "completed":
                    print("🎉 Обучение завершено (по статусу)!")
                    training_completed = True
                    break
                elif stage == "error":
                    print(f"❌ Ошибка обучения: {message}")
                    break
                    
            else:
                print(f"⚠️ Ошибка получения статуса: {status_response.status_code}")
                
        except Exception as e:
            print(f"❌ Исключение при проверке статуса: {str(e)}")
        
        time.sleep(check_interval)
    
    # Test 5: Final status check
    print(f"\n📋 Шаг 5: Итоговая проверка...")
    
    final_time = time.time() - start_time
    print(f"⏱️ Общее время тестирования: {int(final_time)}s")
    print(f"🚀 Обучение запускалось: {'✅ Да' if training_started else '❌ Нет'}")
    print(f"🏁 Обучение завершилось: {'✅ Да' if training_completed else '❌ Нет'}")
    
    # Test 6: Quick query test after training
    if training_completed:
        print(f"\n🔍 Шаг 6: Тест запросов после обучения...")
        
        test_queries = ["строительство", "документ"]
        
        for query in test_queries:
            try:
                query_response = requests.post(
                    'http://localhost:8000/query',
                    json={'query': query, 'k': 3},
                    headers=headers,
                    timeout=30
                )
                
                if query_response.status_code == 200:
                    query_data = query_response.json()
                    results = query_data.get('results', [])
                    ndcg = query_data.get('ndcg', 0)
                    
                    print(f"   🎯 '{query}': {len(results)} результатов, NDCG: {ndcg:.3f}")
                    
                    if results:
                        best_score = results[0].get('score', 0)
                        print(f"      📊 Лучший score: {best_score:.3f}")
                    
                else:
                    print(f"   ❌ Ошибка запроса '{query}': {query_response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Исключение запроса '{query}': {str(e)}")
        
    print(f"\n✨ Тестирование завершено!")
    
    # Summary
    print(f"\n📋 Резюме исправлений:")
    print(f"   🔧 Исправлен синтаксис background_tasks.add_task()")
    print(f"   📊 Добавлено глобальное отслеживание статуса обучения")
    print(f"   ⏱️ Добавлено отслеживание времени выполнения")
    print(f"   🔄 Улучшена функция run_training_with_updates()")
    print(f"   📡 Обновлен эндпоинт /api/training/status")

if __name__ == '__main__':
    test_training_functionality()