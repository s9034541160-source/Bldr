#!/usr/bin/env python3
"""
Fix Neo4j Training Issue
Диагностика и исправление проблемы с обучением RAG
"""

import os
import json
import shutil
from pathlib import Path

def diagnose_neo4j_issue():
    """Диагностика проблемы с Neo4j"""
    print("🔍 ДИАГНОСТИКА ПРОБЛЕМЫ NEO4J")
    print("=" * 50)
    
    print("1. Проверка состояния Neo4j...")
    
    # Проверка процессов Neo4j
    try:
        import psutil
        neo4j_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if 'neo4j' in proc.info['name'].lower() or any('neo4j' in str(cmd).lower() for cmd in proc.info['cmdline'] or []):
                neo4j_processes.append(proc.info)
        
        if neo4j_processes:
            print(f"✅ Найдено {len(neo4j_processes)} процессов Neo4j")
            for proc in neo4j_processes:
                print(f"   PID: {proc['pid']}, Name: {proc['name']}")
        else:
            print("❌ Процессы Neo4j не найдены")
    except ImportError:
        print("⚠️ psutil не установлен, пропускаем проверку процессов")
    
    print("\n2. Проверка файлов кэша...")
    
    # Проверка кэша обучения
    cache_dirs = [
        "I:/docs/downloaded/cache",
        "./cache",
        "./data/cache"
    ]
    
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            print(f"✅ Найден кэш: {cache_dir}")
            files = list(Path(cache_dir).glob("*.json"))
            print(f"   Файлов последовательностей: {len(files)}")
            
            # Проверка размера файлов
            total_size = sum(f.stat().st_size for f in files)
            print(f"   Общий размер: {total_size / 1024 / 1024:.2f} MB")
        else:
            print(f"❌ Кэш не найден: {cache_dir}")
    
    print("\n3. Анализ ошибки...")
    print("Ошибка 'object cannot be re-sized' обычно означает:")
    print("   • Конфликт данных в Neo4j")
    print("   • Проблемы с памятью")
    print("   • Незавершенные транзакции")
    print("   • Дублирование узлов/связей")

def suggest_solutions():
    """Предложение решений"""
    print("\n🛠️ ВАРИАНТЫ РЕШЕНИЯ")
    print("=" * 30)
    
    solutions = [
        {
            "level": "ЛЕГКИЙ",
            "title": "Перезапуск Neo4j",
            "description": "Перезапустить Neo4j для очистки памяти и транзакций",
            "steps": [
                "Остановить все процессы обучения (Ctrl+C)",
                "Перезапустить Neo4j сервис",
                "Продолжить обучение с того же места"
            ],
            "risk": "Низкий",
            "time": "2-3 минуты"
        },
        {
            "level": "СРЕДНИЙ", 
            "title": "Очистка кэша и продолжение",
            "description": "Очистить проблемные файлы кэша и продолжить",
            "steps": [
                "Остановить обучение",
                "Удалить файлы кэша для проблемного документа",
                "Перезапустить обучение с флагом --resume"
            ],
            "risk": "Средний",
            "time": "5-10 минут"
        },
        {
            "level": "РАДИКАЛЬНЫЙ",
            "title": "Полный сброс и переобучение",
            "description": "Сбросить все базы данных и начать заново",
            "steps": [
                "Остановить все процессы",
                "Очистить Neo4j базу данных",
                "Очистить векторную базу",
                "Запустить обучение заново"
            ],
            "risk": "Высокий - потеря всех данных",
            "time": "30+ минут"
        }
    ]
    
    for i, solution in enumerate(solutions, 1):
        print(f"\n{i}. {solution['level']}: {solution['title']}")
        print(f"   Описание: {solution['description']}")
        print(f"   Риск: {solution['risk']}")
        print(f"   Время: {solution['time']}")
        print("   Шаги:")
        for step in solution['steps']:
            print(f"     • {step}")

def create_recovery_script():
    """Создание скрипта восстановления"""
    print("\n📝 СОЗДАНИЕ СКРИПТА ВОССТАНОВЛЕНИЯ")
    print("=" * 40)
    
    recovery_script = '''#!/usr/bin/env python3
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
'''
    
    with open("recovery_script.py", "w", encoding="utf-8") as f:
        f.write(recovery_script)
    
    print("✅ Создан файл: recovery_script.py")

def main():
    """Главная функция"""
    diagnose_neo4j_issue()
    suggest_solutions()
    create_recovery_script()
    
    print("\n🎯 РЕКОМЕНДАЦИЯ")
    print("=" * 20)
    print("1. Сначала попробуйте ЛЕГКИЙ вариант (перезапуск Neo4j)")
    print("2. Если не поможет - СРЕДНИЙ (очистка кэша)")
    print("3. РАДИКАЛЬНЫЙ только в крайнем случае")
    print("\n📋 СЛЕДУЮЩИЕ ШАГИ:")
    print("1. Нажмите Ctrl+C для остановки текущего обучения")
    print("2. Запустите: python recovery_script.py")
    print("3. Выберите подходящий вариант восстановления")

if __name__ == "__main__":
    main()