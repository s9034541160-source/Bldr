#!/usr/bin/env python3
"""
Временный запуск RAG обучения без Neo4j 
(с пониженной функциональностью, но работает)
"""

import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_BASE = "http://localhost:8000"
API_TOKEN = os.getenv("API_TOKEN")

def start_training_without_neo4j():
    """Запуск обучения без Neo4j"""
    print("⚠️  ВРЕМЕННЫЙ запуск RAG обучения без Neo4j")
    print("=" * 55)
    print("🔧 Функциональность будет ограничена:")
    print("   ❌ Нет графа связей между документами") 
    print("   ❌ Нет извлечения последовательностей работ")
    print("   ❌ Нет структурного анализа связей")
    print("   ✅ Есть векторный поиск через Qdrant")
    print("   ✅ Есть Stage 0 НТД предобработка")
    print("   ✅ Есть базовое чанкинг и эмбеддинги")
    print()
    
    # Временно отключаем Neo4j в .env
    print("🔧 Временно отключаем Neo4j...")
    update_env_skip_neo4j(True)
    
    # Перезапуск бекенда потребуется
    print("⚠️  ВНИМАНИЕ: Нужно перезапустить бекенд чтобы изменения вступили в силу")
    print("   1. Закройте окно FastAPI Backend")
    print("   2. Запустите снова: python -m uvicorn core.bldr_api:app --host 127.0.0.1 --port 8000 --reload")
    print()
    
    # Подтверждение
    user_input = input("Продолжить с ограниченной функциональностью? (y/N): ").lower().strip()
    if user_input not in ['y', 'yes']:
        print("❌ Отменено пользователем")
        return False
    
    print("\n⏳ Подождите пока перезапустите бекенд, затем нажмите Enter...")
    input("Нажмите Enter когда бекенд перезапущен...")
    
    # Запуск обучения
    if not API_TOKEN:
        print("❌ Нет API токена")
        return False
    
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    
    # Проверка API
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10, headers=headers)
        if response.status_code != 200:
            print(f"❌ API недоступен: {response.status_code}")
            return False
        print("✅ API доступен")
    except Exception as e:
        print(f"❌ Ошибка API: {e}")
        return False
    
    # Данные для обучения
    train_data = {
        "custom_dir": "I:/docs/downloaded"
    }
    
    print(f"📂 Папка: {train_data['custom_dir']}")
    print(f"📊 Файлов: 1168 документов НТД")
    print(f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        print("\n📤 Запускаем ограниченное RAG обучение...")
        
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
            print("\n🎯 RAG обучение активно (без Neo4j)")
            print("🔄 Процесс выполняется в фоновом режиме")
            print("⏱️  Время: ~2-4 часа")
            print("\n💡 Когда Neo4j заработает:")
            print("   1. Установите SKIP_NEO4J=false в .env")
            print("   2. Перезапустите бекенд")
            print("   3. Запустите полное обучение снова")
            return True
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(f"📄 Детали: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        return False

def update_env_skip_neo4j(skip):
    """Обновление SKIP_NEO4J в .env файле"""
    try:
        with open(".env", 'r') as f:
            lines = f.readlines()
        
        # Обновляем или добавляем SKIP_NEO4J
        updated = False
        for i, line in enumerate(lines):
            if line.startswith("SKIP_NEO4J="):
                lines[i] = f"SKIP_NEO4J={'true' if skip else 'false'}\r\n"
                updated = True
                break
        
        if not updated:
            lines.append(f"SKIP_NEO4J={'true' if skip else 'false'}\r\n")
        
        with open(".env", 'w') as f:
            f.writelines(lines)
        
        print(f"✅ SKIP_NEO4J установлен в {'true' if skip else 'false'}")
        
    except Exception as e:
        print(f"⚠️  Ошибка обновления .env: {e}")

def main():
    success = start_training_without_neo4j()
    if success:
        print("\n🚀 Ограниченное RAG обучение запущено!")
        print("📝 Используйте python quick_search_test.py для проверки")
    else:
        print("\n❌ Не удалось запустить обучение")

if __name__ == "__main__":
    main()