#!/usr/bin/env python3
"""
Тестирование RAG обучения через API без фронтенда
"""

import requests
import json
import time
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API настройки
API_BASE = "http://localhost:8000"
TIMEOUT_SHORT = 30  # секунды для обычных запросов
TIMEOUT_TRAIN = 7200  # 2 часа для обучения

# Токен для аутентификации
API_TOKEN = os.getenv("API_TOKEN")

def get_auth_token():
    """Получение токена аутентификации"""
    global API_TOKEN
    
    # Попробуем использовать токен из .env файла
    if API_TOKEN:
        print(f"📋 Используем токен из .env файла")
        return API_TOKEN
    
    # Если токена нет, получаем новый через /token эндпоинт
    print("🔑 Получение нового токена...")
    try:
        response = requests.post(f"{API_BASE}/token", timeout=TIMEOUT_SHORT)
        if response.status_code == 200:
            data = response.json()
            API_TOKEN = data["access_token"]
            print("✅ Токен получен успешно")
            return API_TOKEN
        else:
            print(f"❌ Ошибка получения токена: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка при получении токена: {e}")
        return None

def get_auth_headers():
    """Получение заголовков авторизации"""
    token = get_auth_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def test_api_connection():
    """Тестирование подключения к API"""
    print("🔌 Тестирование подключения к API...")
    
    try:
        response = requests.get(f"{API_BASE}/health", timeout=TIMEOUT_SHORT)
        if response.status_code == 200:
            print("✅ API доступен")
            return True
        else:
            print(f"❌ API недоступен, статус: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка подключения к API: {e}")
        return False

def test_train_endpoint():
    """Тестирование эндпоинта обучения"""
    print("\n🎯 Тестирование эндпоинта /train...")
    
    # Получаем заголовки авторизации
    auth_headers = get_auth_headers()
    if not auth_headers:
        print("❌ Не удалось получить токен авторизации")
        return False
    
    # Данные для запроса обучения
    train_data = {
        "custom_dir": "I:/docs/downloaded"  # папка с 1168 необработанными файлами НТД
    }
    
    try:
        print(f"📤 Отправка запроса на обучение: {train_data['custom_dir']}")
        
        response = requests.post(
            f"{API_BASE}/train",
            json=train_data,
            headers=auth_headers,
            timeout=TIMEOUT_TRAIN,
            stream=True  # для получения потокового ответа
        )
        
        if response.status_code == 200:
            print("✅ Запрос на обучение принят")
            
            # Чтение потокового ответа
            print("📊 Прогресс обучения:")
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    try:
                        # Если это JSON, декодируем
                        if line.startswith('{'):
                            data = json.loads(line)
                            if 'stage' in data and 'message' in data:
                                progress = data.get('progress', 0)
                                print(f"  [{data['stage']}] {data['message']} ({progress}%)")
                        else:
                            # Обычный текст
                            print(f"  📝 {line}")
                    except json.JSONDecodeError:
                        print(f"  📝 {line}")
                        
            print("✅ Обучение завершено!")
            return True
            
        elif response.status_code == 422:
            print(f"❌ Ошибка валидации данных: {response.text}")
            return False
        else:
            print(f"❌ Ошибка API: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Тайм-аут запроса (это нормально для длительного обучения)")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка при отправке запроса: {e}")
        return False

def test_query_endpoint():
    """Тестирование эндпоинта поиска"""
    print("\n🔍 Тестирование эндпоинта /query...")
    
    # Получаем заголовки авторизации
    auth_headers = get_auth_headers()
    if not auth_headers:
        print("❌ Не удалось получить токен авторизации")
        return False
    
    query_data = {
        "query": "СП 45 железобетонные конструкции",
        "k": 3
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/query",
            json=query_data,
            headers=auth_headers,
            timeout=TIMEOUT_SHORT
        )
        
        if response.status_code == 200:
            results = response.json()
            print("✅ Поиск выполнен успешно")
            
            if 'results' in results and results['results']:
                print(f"📋 Найдено результатов: {len(results['results'])}")
                for i, result in enumerate(results['results'][:2], 1):
                    print(f"  {i}. {result.get('chunk', '')[:100]}...")
                    print(f"     Score: {result.get('score', 0):.3f}")
            else:
                print("❌ Поиск не вернул результатов")
                
            return True
        else:
            print(f"❌ Ошибка поиска: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка при поиске: {e}")
        return False

def check_data_directories():
    """Проверка наличия необходимых директорий"""
    print("\n📁 Проверка директорий данных...")
    
    directories = [
        "I:/docs/downloaded",
        "I:/docs/БАЗА",
        "I:/docs/clean_base", 
        "I:/docs/reports",
        "C:/Bldr/data"
    ]
    
    all_exist = True
    for directory in directories:
        if Path(directory).exists():
            print(f"✅ {directory}")
        else:
            print(f"❌ {directory} - не найдена")
            all_exist = False
            
    return all_exist

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестирования RAG API")
    print("=" * 50)
    
    # Проверка директорий
    if not check_data_directories():
        print("\n⚠️  Некоторые директории данных не найдены")
        print("Проверьте пути к данным перед запуском обучения")
    
    # Тестирование подключения
    if not test_api_connection():
        print("\n❌ API недоступен. Запустите бекенд сначала.")
        print("Команда: python main.py")
        return
    
    # Тестирование поиска (до обучения)
    print("\n🔍 Тест поиска до обучения:")
    test_query_endpoint()
    
    # Предложение запустить обучение
    print("\n" + "=" * 50)
    print("🎓 ОБУЧЕНИЕ")
    print("Запустить полное обучение RAG на базе НТД?")
    print("⚠️  ВНИМАНИЕ: Процесс может занять несколько часов!")
    
    user_input = input("Запустить обучение? (y/N): ").lower().strip()
    
    if user_input == 'y' or user_input == 'yes':
        if test_train_endpoint():
            print("\n🎉 Обучение завершено успешно!")
            
            # Повторное тестирование поиска
            print("\n🔍 Тест поиска после обучения:")
            test_query_endpoint()
        else:
            print("\n❌ Обучение завершилось с ошибкой")
    else:
        print("⏭️  Обучение пропущено")
    
    print("\n" + "=" * 50)
    print("✅ Тестирование завершено")

if __name__ == "__main__":
    main()