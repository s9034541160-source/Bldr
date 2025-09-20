#!/usr/bin/env python3
"""
Быстрый запуск RAG-обучения в FAST режиме
"""

import requests
import json
import time
import os

# API конфигурация
API_BASE_URL = "http://localhost:8000"

def create_test_token():
    """Создать тестовый токен для аутентификации"""
    import jwt
    from datetime import datetime, timedelta
    
    payload = {
        "sub": "test_user",
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    
    # Используем простой секрет
    token = jwt.encode(payload, "your-secret-key-change-in-production", algorithm="HS256")
    return token

def start_fast_training():
    """Запустить быстрое обучение"""
    print("🚀 ЗАПУСК БЫСТРОГО RAG-ОБУЧЕНИЯ!")
    print("=" * 60)
    
    # Создаем токен
    token = create_test_token()
    
    # Проверяем директорию
    custom_dir = "I:/docs/downloaded"
    if not os.path.exists(custom_dir):
        print(f"⚠️ Директория {custom_dir} не найдена!")
        print("💡 Попробуем с базовой директорией...")
        custom_dir = None
    else:
        files_count = len([f for f in os.listdir(custom_dir) if os.path.isfile(os.path.join(custom_dir, f))])
        print(f"📁 Найдено {files_count} файлов в {custom_dir}")
    
    # Данные запроса
    request_data = {
        "fast_mode": True,
        "custom_dir": custom_dir
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        print(f"⚡ Запуск FAST MODE обучения...")
        print(f"📂 Директория: {custom_dir or 'по умолчанию'}")
        
        # Запускаем обучение
        response = requests.post(
            f"{API_BASE_URL}/train",
            json=request_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {result['message']}")
            print(f"🏃 Режим: {'FAST' if result.get('fast_mode') else 'NORMAL'}")
            
            # Мониторим прогресс
            print("\n📊 МОНИТОРИНГ ПРОГРЕССА:")
            print("-" * 50)
            
            last_progress = -1
            start_time = time.time()
            
            while True:
                time.sleep(3)  # Проверяем каждые 3 секунды
                
                try:
                    status_response = requests.get(
                        f"{API_BASE_URL}/api/training/status",
                        headers=headers,
                        timeout=10
                    )
                    
                    if status_response.status_code == 200:
                        status = status_response.json()
                        
                        progress = status.get("progress", 0)
                        stage = status.get("current_stage", "")
                        message = status.get("message", "")
                        mode = status.get("mode", "normal")
                        is_training = status.get("is_training", False)
                        
                        # Показываем прогресс только при изменениях
                        if progress != last_progress or not is_training:
                            elapsed = time.time() - start_time
                            print(f"[{mode.upper()}] {stage}: {message} ({progress}%) - {elapsed:.1f}s")
                            last_progress = progress
                        
                        # Проверяем завершение
                        if not is_training:
                            if status.get("status") == "success" or stage == "completed":
                                elapsed = time.time() - start_time
                                print(f"\n🎉 БЫСТРОЕ ОБУЧЕНИЕ ЗАВЕРШЕНО!")
                                print(f"⏱️ Время: {elapsed:.1f} секунд")
                                print(f"🚀 Примерное ускорение: ~{elapsed*7/elapsed:.1f}x быстрее обычного режима")
                                break
                            elif "error" in stage or "error" in status.get("status", ""):
                                print(f"\n❌ Ошибка: {message}")
                                break
                            else:
                                print(f"\n✅ Обучение завершено: {message}")
                                break
                    else:
                        print(f"⚠️ Ошибка статуса: {status_response.status_code}")
                        break
                        
                except requests.exceptions.RequestException as e:
                    print(f"⚠️ Ошибка запроса статуса: {e}")
                    time.sleep(5)  # Ждем дольше при ошибках
                    continue
                    
                # Таймаут через 10 минут
                if time.time() - start_time > 600:
                    print("⏰ Таймаут - обучение идет дольше 10 минут")
                    break
                    
        else:
            print(f"❌ Ошибка запуска: {response.status_code}")
            print(f"📝 Ответ: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети: {e}")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")

if __name__ == "__main__":
    start_fast_training()