#!/usr/bin/env python3
"""
Check Neo4j Status
Проверка состояния Neo4j и диагностика проблем
"""

import os
import sys
import json
import requests
from pathlib import Path

def check_neo4j_connection():
    """Проверка подключения к Neo4j"""
    print("🔌 ПРОВЕРКА ПОДКЛЮЧЕНИЯ К NEO4J")
    print("=" * 40)
    
    # Стандартные настройки Neo4j
    neo4j_configs = [
        {"url": "http://localhost:7474", "bolt": "bolt://localhost:7687"},
        {"url": "http://localhost:7475", "bolt": "bolt://localhost:7688"},
        {"url": "http://127.0.0.1:7474", "bolt": "bolt://127.0.0.1:7687"}
    ]
    
    for config in neo4j_configs:
        try:
            print(f"Проверяем: {config['url']}")
            response = requests.get(config['url'], timeout=5)
            if response.status_code == 200:
                print(f"✅ Neo4j доступен на {config['url']}")
                print(f"   Bolt: {config['bolt']}")
                return config
            else:
                print(f"❌ Neo4j недоступен: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка подключения: {e}")
    
    print("❌ Neo4j недоступен на стандартных портах")
    return None

def check_training_progress():
    """Проверка прогресса обучения"""
    print("\n📊 ПРОВЕРКА ПРОГРЕССА ОБУЧЕНИЯ")
    print("=" * 35)
    
    cache_dir = Path("I:/docs/downloaded/cache")
    if not cache_dir.exists():
        print("❌ Кэш директория не найдена")
        return
    
    # Подсчет обработанных файлов
    sequence_files = list(cache_dir.glob("sequences_*.json"))
    embedding_files = list(cache_dir.glob("embeddings_*.json"))
    
    print(f"📁 Файлов последовательностей: {len(sequence_files)}")
    print(f"🧠 Файлов эмбеддингов: {len(embedding_files)}")
    
    # Анализ размеров
    total_sequences_size = sum(f.stat().st_size for f in sequence_files)
    total_embeddings_size = sum(f.stat().st_size for f in embedding_files)
    
    print(f"💾 Размер последовательностей: {total_sequences_size / 1024 / 1024:.2f} MB")
    print(f"💾 Размер эмбеддингов: {total_embeddings_size / 1024 / 1024:.2f} MB")
    
    # Поиск проблемного файла
    problematic_pattern = "*gesn_28_chast_28*"
    problematic_files = list(cache_dir.glob(problematic_pattern))
    
    if problematic_files:
        print(f"\n⚠️ Найдены файлы проблемного документа:")
        for f in problematic_files:
            print(f"   {f.name} ({f.stat().st_size} bytes)")
    else:
        print(f"\n✅ Проблемный файл не найден в кэше")

def suggest_action():
    """Предложение действий"""
    print("\n🎯 РЕКОМЕНДУЕМЫЕ ДЕЙСТВИЯ")
    print("=" * 30)
    
    neo4j_status = check_neo4j_connection()
    
    if neo4j_status:
        print("✅ Neo4j работает - можно продолжать обучение")
        print("\n📋 ПЛАН ДЕЙСТВИЙ:")
        print("1. Остановите текущее обучение (Ctrl+C)")
        print("2. Запустите: python quick_neo4j_fix.py")
        print("3. Следуйте инструкциям скрипта")
    else:
        print("❌ Neo4j не работает")
        print("\n📋 ПЛАН ДЕЙСТВИЙ:")
        print("1. Запустите Neo4j Desktop")
        print("2. Убедитесь что база данных запущена")
        print("3. Проверьте порты 7474 и 7687")
        print("4. Повторите проверку")

def main():
    """Главная функция"""
    print("🔍 NEO4J STATUS CHECKER")
    print("=" * 30)
    
    check_training_progress()
    suggest_action()
    
    print(f"\n💡 ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ")
    print("=" * 35)
    print("• Ошибка 'object cannot be re-sized' - это проблема Neo4j")
    print("• Обычно решается перезапуском Neo4j")
    print("• Данные в кэше сохранены и не потеряются")
    print("• Обучение можно продолжить с того же места")

if __name__ == "__main__":
    main()