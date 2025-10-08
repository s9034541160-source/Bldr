#!/usr/bin/env python3
"""
Clean Start Training
Чистый старт обучения с проверками
"""

import os
import time
import requests
import subprocess
from pathlib import Path

def check_neo4j_status():
    """Проверка статуса Neo4j"""
    print("🔌 ПРОВЕРКА NEO4J")
    print("=" * 20)
    
    neo4j_urls = ["http://localhost:7474", "http://127.0.0.1:7474"]
    
    for url in neo4j_urls:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ Neo4j работает: {url}")
                return True
        except requests.exceptions.RequestException:
            continue
    
    print("❌ Neo4j не работает!")
    return False

def start_neo4j():
    """Запуск Neo4j Desktop"""
    print("🚀 ЗАПУСК NEO4J DESKTOP")
    print("=" * 25)
    
    neo4j_paths = [
        r"C:\Users\%USERNAME%\AppData\Local\Programs\Neo4j Desktop\Neo4j Desktop.exe",
        r"C:\Program Files\Neo4j Desktop\Neo4j Desktop.exe"
    ]
    
    for path in neo4j_paths:
        expanded_path = os.path.expandvars(path)
        if os.path.exists(expanded_path):
            print(f"   Запускаем: {expanded_path}")
            subprocess.Popen([expanded_path])
            return True
    
    print("❌ Neo4j Desktop не найден!")
    return False

def wait_for_neo4j():
    """Ожидание запуска Neo4j"""
    print("⏳ ОЖИДАНИЕ ЗАПУСКА NEO4J")
    print("=" * 30)
    
    max_attempts = 12  # 60 секунд
    for attempt in range(max_attempts):
        if check_neo4j_status():
            print("✅ Neo4j готов к работе!")
            return True
        
        print(f"   Попытка {attempt + 1}/{max_attempts}... (через 5 сек)")
        time.sleep(5)
    
    print("❌ Neo4j не запустился за 60 секунд")
    return False

def verify_clean_state():
    """Проверка чистого состояния"""
    print("🧹 ПРОВЕРКА ЧИСТОГО СОСТОЯНИЯ")
    print("=" * 35)
    
    # Проверяем что кэш очищен
    cache_dir = Path("I:/docs/downloaded/cache")
    if cache_dir.exists():
        cache_files = list(cache_dir.glob("*.json"))
        if cache_files:
            print(f"⚠️ Найдены файлы кэша: {len(cache_files)}")
            return False
    
    # Проверяем processed_files.json
    processed_file = Path("I:/docs/downloaded/processed_files.json")
    if processed_file.exists():
        print("⚠️ Найден processed_files.json")
        return False
    
    print("✅ Состояние чистое - можно начинать обучение")
    return True

def start_safe_training():
    """Запуск безопасного обучения"""
    print("🛡️ ЗАПУСК БЕЗОПАСНОГО ОБУЧЕНИЯ")
    print("=" * 35)
    
    try:
        # Запускаем безопасный тренер
        result = subprocess.run([
            "python", 
            "enterprise_rag_trainer_safe.py",
            "--custom_dir", "I:/docs/downloaded",
            "--fast_mode"
        ], capture_output=False, text=True)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Ошибка запуска обучения: {e}")
        return False

def main():
    """Главная функция чистого старта"""
    print("🧹 ЧИСТЫЙ СТАРТ ОБУЧЕНИЯ RAG")
    print("=" * 40)
    print("После ядерного сброса всех баз данных")
    print()
    
    # 1. Проверяем чистое состояние
    if not verify_clean_state():
        print("❌ Состояние не чистое! Запустите emergency_full_reset.py")
        return False
    
    # 2. Проверяем Neo4j
    if not check_neo4j_status():
        print("Neo4j не работает, пытаемся запустить...")
        
        if not start_neo4j():
            print("❌ Не удалось запустить Neo4j Desktop")
            print("💡 Запустите Neo4j Desktop вручную и повторите")
            return False
        
        if not wait_for_neo4j():
            print("❌ Neo4j не запустился")
            print("💡 Проверьте Neo4j Desktop и повторите")
            return False
    
    # 3. Запускаем обучение
    print("\n🚀 ВСЕ ГОТОВО! ЗАПУСКАЕМ ОБУЧЕНИЕ...")
    print("=" * 40)
    print("⚠️ Обучение начнется с файла №1")
    print("⚠️ Все файлы будут организованы по папкам")
    print("⚠️ Защита от одновременного запуска активна")
    print()
    
    input("Нажмите Enter для начала обучения...")
    
    success = start_safe_training()
    
    if success:
        print("\n🎉 ОБУЧЕНИЕ ЗАВЕРШЕНО УСПЕШНО!")
    else:
        print("\n❌ ОБУЧЕНИЕ ЗАВЕРШИЛОСЬ С ОШИБКОЙ")
    
    return success

if __name__ == "__main__":
    main()