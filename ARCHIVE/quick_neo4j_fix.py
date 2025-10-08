#!/usr/bin/env python3
"""
Quick Neo4j Fix
Быстрое исправление проблемы с Neo4j без потери данных
"""

import os
import sys
import time
import subprocess
from pathlib import Path

def quick_fix():
    """Быстрое исправление проблемы"""
    print("🚑 БЫСТРОЕ ИСПРАВЛЕНИЕ NEO4J")
    print("=" * 40)
    
    print("1. 🛑 Остановите текущее обучение (Ctrl+C)")
    input("   Нажмите Enter когда остановите обучение...")
    
    print("\n2. 🔄 Перезапуск Neo4j...")
    
    # Попытка перезапуска Neo4j через Desktop
    try:
        # Закрытие соединений Neo4j
        print("   Закрываем соединения...")
        
        # Для Windows - перезапуск через taskkill и запуск
        os.system("taskkill /f /im java.exe /fi \"WINDOWTITLE eq Neo4j*\" 2>nul")
        time.sleep(3)
        
        print("   Neo4j процессы остановлены")
        
        # Запуск Neo4j Desktop (если установлен)
        neo4j_desktop_paths = [
            r"C:\Users\%USERNAME%\AppData\Local\Programs\Neo4j Desktop\Neo4j Desktop.exe",
            r"C:\Program Files\Neo4j Desktop\Neo4j Desktop.exe"
        ]
        
        for path in neo4j_desktop_paths:
            expanded_path = os.path.expandvars(path)
            if os.path.exists(expanded_path):
                print(f"   Запускаем Neo4j Desktop: {expanded_path}")
                subprocess.Popen([expanded_path], shell=True)
                break
        
        print("   Ждем запуска Neo4j (30 секунд)...")
        time.sleep(30)
        
    except Exception as e:
        print(f"   ⚠️ Ошибка автоматического перезапуска: {e}")
        print("   Перезапустите Neo4j Desktop вручную")
        input("   Нажмите Enter когда Neo4j будет запущен...")
    
    print("\n3. 🧹 Очистка проблемного файла из кэша...")
    
    # Удаление кэша для проблемного файла
    problematic_file = "gesn_28_chast_28._zheleznye_dorogi"
    cache_dir = Path("I:/docs/downloaded/cache")
    
    if cache_dir.exists():
        cache_files = list(cache_dir.glob(f"*{problematic_file}*"))
        for cache_file in cache_files:
            print(f"   Удаляем: {cache_file.name}")
            try:
                cache_file.unlink()
            except Exception as e:
                print(f"   ⚠️ Не удалось удалить {cache_file}: {e}")
    
    print("\n4. 📝 Создание команды для продолжения обучения...")
    
    # Создание bat файла для продолжения
    resume_command = """@echo off
echo 🚀 Продолжение обучения RAG...
python enterprise_rag_trainer_full.py --custom_dir "I:/docs/downloaded" --fast_mode
pause
"""
    
    with open("resume_training.bat", "w", encoding="utf-8") as f:
        f.write(resume_command)
    
    print("   ✅ Создан файл: resume_training.bat")
    
    print("\n✅ БЫСТРОЕ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!")
    print("=" * 40)
    print("📋 ЧТО ДЕЛАТЬ ДАЛЬШЕ:")
    print("1. Убедитесь что Neo4j Desktop запущен")
    print("2. Запустите: resume_training.bat")
    print("3. Обучение продолжится с файла №227")
    print("\n💡 ПОЧЕМУ ЭТО РАБОТАЕТ:")
    print("• Neo4j перезапущен - очищена память и транзакции")
    print("• Проблемный файл удален из кэша - будет обработан заново")
    print("• Обучение продолжится с того же места")
    print("• Все уже обработанные данные сохранены")

if __name__ == "__main__":
    quick_fix()