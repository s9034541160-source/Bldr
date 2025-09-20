#!/usr/bin/env python3
"""
🧪 ТЕСТОВЫЙ ЗАПУСК MONSTER RAG TRAINER - ОГРАНИЧЕННАЯ ВЕРСИЯ
==========================================================
Запускает монстра на ограниченном количестве файлов для тестирования
"""

import sys
sys.path.append('C:/Bldr')

from monster_rag_trainer_full_power import launch_monster
import time

print("🧪" * 60)
print("🔬 ТЕСТОВЫЙ ЗАПУСК MONSTER RAG TRAINER")  
print("🧪" * 60)

# Тестовые параметры
BASE_DIR = "I:/docs"
MAX_FILES = 10  # Только 10 файлов для теста
MAX_WORKERS = 2  # Меньше воркеров для теста

print(f"📁 Target Directory: {BASE_DIR}")
print(f"📊 Max Files: {MAX_FILES} (TEST MODE)")
print(f"👥 Workers: {MAX_WORKERS} (LIMITED)")

try:
    print("\n🔬 Starting test run...")
    start_time = time.time()
    
    monster = launch_monster(
        base_dir=BASE_DIR,
        max_files=MAX_FILES,
        max_workers=MAX_WORKERS
    )
    
    end_time = time.time()
    
    print("\n" + "🎉" * 60)
    print(f"✅ TEST COMPLETED in {end_time - start_time:.1f} seconds!")
    print("🎉" * 60)

except Exception as e:
    print(f"\n❌ TEST FAILED: {e}")
    import traceback
    traceback.print_exc()