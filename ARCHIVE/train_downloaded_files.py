#!/usr/bin/env python3
"""
Запуск RAG обучения на папке I:/docs/downloaded с 1168 файлами НТД
"""

import requests
import json
import time
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API настройки
API_BASE = "http://localhost:8000"
TIMEOUT_TRAIN = 14400  # 4 часа для обучения 1168 файлов
API_TOKEN = os.getenv("API_TOKEN")

def get_auth_headers():
    """Получение заголовков авторизации"""
    if API_TOKEN:
        return {"Authorization": f"Bearer {API_TOKEN}"}
    
    # Получаем новый токен
    try:
        response = requests.post(f"{API_BASE}/token", timeout=30)
        if response.status_code == 200:
            data = response.json()
            token = data["access_token"]
            return {"Authorization": f"Bearer {token}"}
    except Exception as e:
        print(f"❌ Ошибка получения токена: {e}")
    
    return {}

def start_training():
    """Запуск обучения RAG на папке downloaded"""
    print("🚀 Запуск полноценного RAG обучения на 1168 файлах НТД")
    print("=" * 80)
    
    # Проверяем доступность API
    try:
        response = requests.get(f"{API_BASE}/health", timeout=30)
        if response.status_code != 200:
            print(f"❌ API недоступен: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения к API: {e}")
        return False
    
    print("✅ API доступен")
    
    # Получаем заголовки авторизации
    auth_headers = get_auth_headers()
    if not auth_headers:
        print("❌ Не удалось получить токен авторизации")
        return False
    
    print("✅ Токен авторизации получен")
    
    # Данные для обучения
    train_data = {
        "custom_dir": "I:/docs/downloaded"
    }
    
    print(f"📂 Папка для обучения: {train_data['custom_dir']}")
    print(f"📊 Ожидаемое количество файлов: 1168")
    print(f"⏱️  Ожидаемое время обучения: 2-4 часа")
    print()
    
    # Подтверждение от пользователя
    confirm = input("🤔 Запустить полноценное обучение? Это займёт несколько часов! (y/N): ").lower().strip()
    if confirm not in ['y', 'yes']:
        print("⏭️  Обучение отменено пользователем")
        return False
    
    # Запуск обучения
    print("🎓 Запускаем обучение...")
    print("=" * 80)
    
    start_time = datetime.now()
    
    try:
        # Отправляем запрос на обучение
        response = requests.post(
            f"{API_BASE}/train",
            json=train_data,
            headers=auth_headers,
            timeout=TIMEOUT_TRAIN,
            stream=False  # Не используем stream для этого теста
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Запрос на обучение принят!")
            print(f"📋 Ответ сервера: {result}")
            
            # Обучение запущено в фоне, мониторим через логи или другой способ
            print("\n📊 Обучение запущено в фоновом режиме")
            print("🔄 Для отслеживания прогресса:")
            print("   - Проверьте логи сервера")
            print("   - Используйте WebSocket подключение")
            print("   - Мониторьте использование ресурсов системы")
            
            # Ждём некоторое время и проверяем статус
            print("\n⏳ Ждём 30 секунд и проверяем первичный статус...")
            time.sleep(30)
            
            # Тестируем поиск через некоторое время
            print("\n🔍 Тестируем поиск после запуска обучения...")
            test_query_after_training(auth_headers)
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            print("\n" + "=" * 80)
            print(f"✅ Процесс инициирован успешно!")
            print(f"⏱️  Время запуска: {duration}")
            print(f"🕐 Начало обучения: {start_time.strftime('%H:%M:%S')}")
            print("📝 Обучение продолжается в фоновом режиме")
            
            return True
            
        else:
            print(f"❌ Ошибка запуска обучения: {response.status_code}")
            print(f"📄 Ответ: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Тайм-аут запроса (это может быть нормально для долгого обучения)")
        return False
    except Exception as e:
        print(f"❌ Ошибка при запуске обучения: {e}")
        return False

def test_query_after_training(auth_headers):
    """Тестируем поиск после запуска обучения"""
    try:
        query_data = {
            "query": "строительные нормы и правила",
            "k": 5
        }
        
        response = requests.post(
            f"{API_BASE}/query",
            json=query_data,
            headers=auth_headers,
            timeout=30
        )
        
        if response.status_code == 200:
            results = response.json()
            if 'results' in results and results['results']:
                print(f"✅ Найдено результатов: {len(results['results'])}")
                print("📋 Первые результаты:")
                for i, result in enumerate(results['results'][:3], 1):
                    chunk = result.get('chunk', '')[:150]
                    score = result.get('score', 0)
                    print(f"  {i}. [{score:.3f}] {chunk}...")
            else:
                print("ℹ️  Результатов пока нет (обучение ещё не завершено)")
        else:
            print(f"⚠️  Ошибка поиска: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️  Ошибка тестового поиска: {e}")

def main():
    """Основная функция"""
    print("🏗️  Bldr RAG Training для 1168 файлов НТД")
    print("🎯 Цель: Полноценное обучение RAG-системы на реальной базе документов")
    print()
    
    success = start_training()
    
    if success:
        print("\n🎉 Обучение успешно запущено!")
        print("💡 Рекомендации:")
        print("   - Не закрывайте бекенд-сервер")
        print("   - Мониторьте использование диска и памяти")
        print("   - Периодически тестируйте поиск")
        print("   - Проверяйте логи на наличие ошибок")
    else:
        print("\n❌ Не удалось запустить обучение")
        print("🔧 Проверьте:")
        print("   - Работает ли бекенд-сервер")
        print("   - Доступна ли папка I:/docs/downloaded")
        print("   - Корректен ли токен авторизации")

if __name__ == "__main__":
    main()