#!/usr/bin/env python3
"""
Simple training test without WebSocket complexity
Focus on core training functionality
"""

import requests
import time
from dotenv import load_dotenv
import os

load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')
headers = {
    'Authorization': f'Bearer {API_TOKEN}',
    'Content-Type': 'application/json'
}

def test_simple_training():
    print("🔧 Простой тест обучения без WebSocket")
    print("=" * 50)
    
    # Test 1: API health
    print("📡 Шаг 1: Проверка API...")
    try:
        health_response = requests.get('http://localhost:8000/health', timeout=10)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"✅ API статус: {health_data.get('status', 'unknown')}")
            
            # Show components
            components = health_data.get('components', {})
            for component, status in components.items():
                print(f"   📦 {component}: {status}")
        else:
            print(f"❌ API недоступен: {health_response.status_code}")
            return
    except Exception as e:
        print(f"❌ Ошибка подключения к API: {str(e)}")
        return
    
    # Test 2: Initial training status
    print("\n📊 Шаг 2: Начальный статус обучения...")
    try:
        status_response = requests.get(
            'http://localhost:8000/api/training/status',
            headers=headers,
            timeout=10
        )
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            print(f"✅ Статус:")
            print(f"   🔄 is_training: {status_data.get('is_training', False)}")
            print(f"   📈 progress: {status_data.get('progress', 0)}%")
            print(f"   🏷️ stage: {status_data.get('current_stage', 'unknown')}")
            
            if status_data.get('is_training'):
                print("⚠️ Система уже обучается, дождитесь завершения")
                return
                
        else:
            print(f"❌ Ошибка получения статуса: {status_response.status_code}")
            
    except Exception as e:
        print(f"❌ Исключение статуса: {str(e)}")
    
    # Test 3: Check if we have a small test directory
    test_dirs = [
        "C:\\Bldr\\docs",
        "C:\\Bldr\\test_docs"
    ]
    
    test_dir = None
    for directory in test_dirs:
        if os.path.exists(directory):
            # Count files in directory
            import glob
            files = glob.glob(os.path.join(directory, '**', '*.*'), recursive=True)
            doc_files = [f for f in files if f.lower().endswith(('.pdf', '.doc', '.docx', '.txt'))]
            
            if len(doc_files) > 0 and len(doc_files) < 20:  # Small directory
                test_dir = directory
                print(f"✅ Найдена тестовая директория: {test_dir} ({len(doc_files)} документов)")
                break
    
    if not test_dir:
        print("⚠️ Используем большую директорию для полного теста...")
        test_dir = "I:\\docs\\downloaded"
    
    # Test 4: Start training
    print(f"\n🚀 Шаг 3: Запуск обучения на {test_dir}...")
    
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
    
    # Test 5: Monitor for 5 minutes
    print(f"\n📊 Шаг 4: Мониторинг прогресса (5 минут)...")
    
    start_time = time.time()
    max_duration = 300  # 5 minutes
    check_interval = 15  # Check every 15 seconds
    
    training_started = False
    training_completed = False
    last_stage = None
    last_progress = 0
    
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
                
                # Only print if something changed
                if stage != last_stage or progress != last_progress:
                    print(f"   [{elapsed_test:3}s] 📈 {stage}: {message}")
                    print(f"           🎯 Progress: {progress}% | Training: {is_training}")
                    
                    if elapsed_api > 0:
                        print(f"           ⏱️ API elapsed: {elapsed_api}s")
                
                # Track changes
                last_stage = stage
                last_progress = progress
                
                # Check if training actually started
                if is_training and not training_started:
                    print("🎉 Обучение действительно началось!")
                    training_started = True
                
                # Check completion conditions
                if not is_training and training_started:
                    if stage in ["completed", "complete"] or progress >= 100:
                        print("🎉 Обучение завершено!")
                        training_completed = True
                        break
                    elif stage == "error":
                        print(f"❌ Ошибка обучения: {message}")
                        break
                
                # Special case: if we never started training but time passed
                if not training_started and elapsed_test > 30:
                    print("⚠️ Обучение не началось в течение 30 секунд")
                    if stage == "error":
                        print(f"   💥 Ошибка: {message}")
                        break
                    
            else:
                print(f"⚠️ Ошибка получения статуса: {status_response.status_code}")
                
        except Exception as e:
            print(f"❌ Исключение при проверке статуса: {str(e)}")
        
        time.sleep(check_interval)
    
    # Final summary
    print(f"\n📋 Итоговый результат:")
    final_time = time.time() - start_time
    print(f"   ⏱️ Время тестирования: {int(final_time)}s")
    print(f"   🚀 Обучение запускалось: {'✅' if training_started else '❌'}")
    print(f"   🏁 Обучение завершилось: {'✅' if training_completed else '❌'}")
    
    if not training_started:
        print("\n💡 Проблема: Обучение не запустилось")
        print("   - Проверьте логи API сервера")
        print("   - Возможна проблема с trainer инициализацией")
        print("   - Или проблема с callback функциями")
    
    elif training_started and not training_completed:
        print("\n💡 Обучение запустилось, но не завершилось за 5 минут")
        print("   - Это нормально для большой директории")
        print("   - Можете проверить статус позже")
    
    else:
        print("\n🎉 Успех! Система обучения работает корректно")
        
        # Quick query test
        print(f"\n🔍 Бонус: Тест запроса...")
        try:
            query_response = requests.post(
                'http://localhost:8000/query',
                json={'query': 'строительство', 'k': 3},
                headers=headers,
                timeout=30
            )
            
            if query_response.status_code == 200:
                query_data = query_response.json()
                results = query_data.get('results', [])
                ndcg = query_data.get('ndcg', 0)
                
                print(f"   📊 Результатов: {len(results)}, NDCG: {ndcg:.3f}")
                
                if results:
                    best_score = results[0].get('score', 0)
                    print(f"   🎯 Лучший score: {best_score:.3f}")
                    if best_score > 0:
                        print("   ✅ Система действительно обучена!")
                    else:
                        print("   ⚠️ Score низкий, возможно нужно больше времени")
                else:
                    print("   ⚠️ Результатов нет - система не обучена")
            else:
                print(f"   ❌ Ошибка запроса: {query_response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Исключение запроса: {str(e)}")

if __name__ == '__main__':
    test_simple_training()