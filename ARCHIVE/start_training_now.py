#!/usr/bin/env python3
"""
Быстрый запуск RAG обучения на 1168 файлах с новым долгосрочным токеном
"""

import requests
import json
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE = "http://localhost:8000"
API_TOKEN = os.getenv("API_TOKEN")

def start_training_now():
    """Запускаем обучение немедленно"""
    print("🚀 Быстрый запуск RAG обучения на 1168 файлах НТД")
    print("=" * 60)
    
    if not API_TOKEN:
        print("❌ Нет API токена")
        return False
    
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    
    # Проверяем API
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        if response.status_code != 200:
            print(f"❌ API недоступен: {response.status_code}")
            return False
        print("✅ API доступен")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False
    
    # Данные для обучения
    train_data = {
        "custom_dir": "I:/docs/downloaded"
    }
    
    print(f"📂 Папка: {train_data['custom_dir']}")
    print(f"📊 Файлов: 1168 документов НТД")
    print(f"🕐 Время запуска: {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        print("\n📤 Отправляем запрос на обучение...")
        
        response = requests.post(
            f"{API_BASE}/train",
            json=train_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Обучение запущено!")
            print(f"📋 Ответ: {result}")
            print("\n🎯 RAG обучение на 1168 файлах активно!")
            print("🔄 Процесс выполняется в фоновом режиме")
            print("⏱️  Ожидаемое время: 2-4 часа")
            return True
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(f"📄 Детали: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при запуске: {e}")
        return False

if __name__ == "__main__":
    success = start_training_now()
    if success:
        print("\n🎉 Обучение успешно запущено!")
        print("💡 Используйте python quick_search_test.py для проверки прогресса")
    else:
        print("\n❌ Не удалось запустить обучение")