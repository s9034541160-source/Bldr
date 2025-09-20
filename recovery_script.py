#!/usr/bin/env python3
"""
RAG Training Recovery Script
Скрипт для восстановления обучения RAG после ошибки Neo4j
"""

import os
import sys
import json
import shutil
from pathlib import Path

def stop_training():
    """Остановка процессов обучения"""
    print("🛑 Остановка процессов обучения...")
    # Здесь можно добавить код для graceful shutdown
    
def restart_neo4j():
    """Перезапуск Neo4j"""
    print("🔄 Перезапуск Neo4j...")
    # Команды для перезапуска Neo4j
    os.system("net stop neo4j")  # Windows
    os.system("net start neo4j")  # Windows
    # Для Linux: systemctl restart neo4j
    
def clean_problematic_cache():
    """Очистка проблемного кэша"""
    print("🧹 Очистка проблемного кэша...")
    
    problematic_file = "gesn_28_chast_28._zheleznye_dorogi.pdf"
    cache_patterns = [
        f"sequences_{problematic_file.replace('.pdf', '.json')}",
        f"embeddings_{problematic_file.replace('.pdf', '.json')}",
        f"chunks_{problematic_file.replace('.pdf', '.json')}"
    ]
    
    cache_dirs = [
        "I:/docs/downloaded/cache",
        "./cache", 
        "./data/cache"
    ]
    
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            for pattern in cache_patterns:
                cache_file = Path(cache_dir) / pattern
                if cache_file.exists():
                    print(f"   Удаляем: {cache_file}")
                    cache_file.unlink()

def resume_training():
    """Возобновление обучения"""
    print("▶️ Возобновление обучения...")
    
    # Команда для возобновления обучения
    resume_command = """
    python enterprise_rag_trainer_full.py --resume --skip-processed --neo4j-retry 3 --batch-size 1
    """
    
    print("Выполните команду:")
    print(resume_command)

def full_reset():
    """Полный сброс баз данных"""
    print("💥 ПОЛНЫЙ СБРОС БАЗДДАННЫХ")
    print("⚠️ ЭТО УДАЛИТ ВСЕ ОБУЧЕННЫЕ ДАННЫЕ!")
    
    confirm = input("Вы уверены? Введите 'YES' для подтверждения: ")
    if confirm != "YES":
        print("Отменено")
        return
        
    # Очистка Neo4j
    print("🗑️ Очистка Neo4j...")
    # Здесь код для очистки Neo4j
    
    # Очистка векторной базы
    print("🗑️ Очистка векторной базы...")
    # Здесь код для очистки Chroma/FAISS
    
    # Очистка кэша
    print("🗑️ Очистка кэша...")
    cache_dirs = ["./cache", "./data/cache", "I:/docs/downloaded/cache"]
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
            os.makedirs(cache_dir)
    
    print("✅ Полный сброс завершен")

if __name__ == "__main__":
    print("🚑 RAG TRAINING RECOVERY TOOL")
    print("=" * 40)
    
    print("Выберите действие:")
    print("1. Мягкое восстановление (перезапуск Neo4j)")
    print("2. Очистка проблемного кэша")
    print("3. Полный сброс баз данных")
    print("4. Выход")
    
    choice = input("Ваш выбор (1-4): ")
    
    if choice == "1":
        stop_training()
        restart_neo4j()
        resume_training()
    elif choice == "2":
        stop_training()
        clean_problematic_cache()
        restart_neo4j()
        resume_training()
    elif choice == "3":
        full_reset()
    else:
        print("Выход")
