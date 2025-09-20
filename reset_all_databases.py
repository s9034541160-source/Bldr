#!/usr/bin/env python3
"""
Reset All Databases Script
Полный сброс всех баз данных и кэша для чистого старта
"""

import os
import sys
import shutil
import json
import time
import psutil
from pathlib import Path
import subprocess

def kill_training_processes():
    """Убиваем все процессы обучения"""
    print("🔪 ОСТАНОВКА ВСЕХ ПРОЦЕССОВ ОБУЧЕНИЯ")
    print("=" * 40)
    
    killed_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            
            # Ищем процессы RAG-тренера
            if any(keyword in cmdline.lower() for keyword in [
                'enterprise_rag_trainer',
                'rag_trainer',
                'train.py',
                'training'
            ]):
                print(f"   Убиваем процесс: PID {proc.info['pid']} - {proc.info['name']}")
                proc.kill()
                killed_processes.append(proc.info['pid'])
                
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    if killed_processes:
        print(f"✅ Убито процессов: {len(killed_processes)}")
        time.sleep(3)  # Ждем завершения процессов
    else:
        print("✅ Активных процессов обучения не найдено")

def reset_neo4j_database():
    """Сброс базы данных Neo4j"""
    print("\n🗑️ СБРОС NEO4J БАЗЫ ДАННЫХ")
    print("=" * 35)
    
    try:
        # Останавливаем Neo4j
        print("   Остановка Neo4j...")
        os.system("taskkill /f /im java.exe /fi \"WINDOWTITLE eq Neo4j*\" 2>nul")
        time.sleep(5)
        
        # Ищем директории данных Neo4j
        neo4j_data_paths = [
            Path.home() / ".Neo4jDesktop" / "relate-data" / "dbmss",
            Path("C:/Users") / os.getenv('USERNAME', '') / "AppData/Roaming/Neo4j Desktop/Application/relate-data/dbmss",
            Path("C:/neo4j/data"),
            Path("./neo4j-data")
        ]
        
        databases_cleared = 0
        
        for data_path in neo4j_data_paths:
            if data_path.exists():
                print(f"   Найдена директория Neo4j: {data_path}")
                
                # Ищем базы данных
                for db_dir in data_path.rglob("*/data/databases"):
                    if db_dir.exists():
                        print(f"   Очистка базы: {db_dir}")
                        try:
                            # Удаляем содержимое директории баз данных
                            for item in db_dir.iterdir():
                                if item.is_dir():
                                    shutil.rmtree(item)
                                else:
                                    item.unlink()
                            databases_cleared += 1
                        except Exception as e:
                            print(f"   ⚠️ Ошибка очистки {db_dir}: {e}")
        
        if databases_cleared > 0:
            print(f"✅ Очищено баз данных Neo4j: {databases_cleared}")
        else:
            print("⚠️ Базы данных Neo4j не найдены или недоступны")
            
        # Запускаем Neo4j обратно
        print("   Запуск Neo4j...")
        neo4j_desktop_paths = [
            r"C:\Users\%USERNAME%\AppData\Local\Programs\Neo4j Desktop\Neo4j Desktop.exe",
            r"C:\Program Files\Neo4j Desktop\Neo4j Desktop.exe"
        ]
        
        for path in neo4j_desktop_paths:
            expanded_path = os.path.expandvars(path)
            if os.path.exists(expanded_path):
                subprocess.Popen([expanded_path], shell=True)
                print(f"   ✅ Neo4j Desktop запущен: {expanded_path}")
                break
        
        time.sleep(10)  # Ждем запуска
        
    except Exception as e:
        print(f"❌ Ошибка сброса Neo4j: {e}")

def reset_vector_database():
    """Сброс векторной базы данных"""
    print("\n🗑️ СБРОС ВЕКТОРНОЙ БАЗЫ ДАННЫХ")
    print("=" * 40)
    
    vector_db_paths = [
        "./chroma_db",
        "./vector_db", 
        "./embeddings",
        "./faiss_index",
        "I:/docs/vector_db",
        "I:/docs/chroma_db"
    ]
    
    cleared_dbs = 0
    
    for db_path in vector_db_paths:
        path = Path(db_path)
        if path.exists():
            print(f"   Удаление: {path}")
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                cleared_dbs += 1
            except Exception as e:
                print(f"   ⚠️ Ошибка удаления {path}: {e}")
    
    if cleared_dbs > 0:
        print(f"✅ Очищено векторных баз: {cleared_dbs}")
    else:
        print("✅ Векторные базы не найдены")

def reset_json_cache():
    """Сброс JSON кэша"""
    print("\n🗑️ СБРОС JSON КЭША")
    print("=" * 25)
    
    cache_paths = [
        "I:/docs/downloaded/cache",
        "./cache",
        "./data/cache",
        "./training_cache"
    ]
    
    total_files_removed = 0
    total_size_removed = 0
    
    for cache_path in cache_paths:
        path = Path(cache_path)
        if path.exists():
            print(f"   Очистка кэша: {path}")
            
            files_removed = 0
            size_removed = 0
            
            try:
                for file in path.rglob("*.json"):
                    size_removed += file.stat().st_size
                    file.unlink()
                    files_removed += 1
                
                # Также удаляем другие файлы кэша
                for pattern in ["*.pkl", "*.cache", "*.tmp"]:
                    for file in path.rglob(pattern):
                        size_removed += file.stat().st_size
                        file.unlink()
                        files_removed += 1
                
                total_files_removed += files_removed
                total_size_removed += size_removed
                
                print(f"   ✅ Удалено файлов: {files_removed}, размер: {size_removed / 1024 / 1024:.2f} MB")
                
            except Exception as e:
                print(f"   ⚠️ Ошибка очистки {path}: {e}")
    
    print(f"✅ Всего удалено: {total_files_removed} файлов, {total_size_removed / 1024 / 1024:.2f} MB")

def reset_training_logs():
    """Сброс логов обучения"""
    print("\n🗑️ СБРОС ЛОГОВ ОБУЧЕНИЯ")
    print("=" * 30)
    
    log_paths = [
        "./logs",
        "./training_logs",
        "./rag_logs",
        "I:/docs/logs"
    ]
    
    logs_cleared = 0
    
    for log_path in log_paths:
        path = Path(log_path)
        if path.exists():
            print(f"   Очистка логов: {path}")
            try:
                for log_file in path.rglob("*.log"):
                    log_file.unlink()
                    logs_cleared += 1
                for log_file in path.rglob("*.txt"):
                    if 'log' in log_file.name.lower():
                        log_file.unlink()
                        logs_cleared += 1
            except Exception as e:
                print(f"   ⚠️ Ошибка очистки логов {path}: {e}")
    
    if logs_cleared > 0:
        print(f"✅ Очищено логов: {logs_cleared}")
    else:
        print("✅ Логи не найдены")

def create_lockfile_system():
    """Создание системы блокировки для предотвращения одновременного запуска"""
    print("\n🔒 СОЗДАНИЕ СИСТЕМЫ БЛОКИРОВКИ")
    print("=" * 40)
    
    lockfile_code = '''#!/usr/bin/env python3
"""
RAG Training Lockfile System
Система блокировки для предотвращения одновременного запуска обучения
"""

import os
import sys
import time
import psutil
from pathlib import Path
import json
from datetime import datetime

class RAGTrainingLock:
    """Система блокировки RAG обучения"""
    
    def __init__(self, lockfile_path="./rag_training.lock"):
        self.lockfile_path = Path(lockfile_path)
        self.pid = os.getpid()
        
    def acquire_lock(self):
        """Получение блокировки"""
        if self.lockfile_path.exists():
            # Проверяем, активен ли процесс из lockfile
            try:
                with open(self.lockfile_path, 'r') as f:
                    lock_data = json.load(f)
                
                old_pid = lock_data.get('pid')
                if old_pid and psutil.pid_exists(old_pid):
                    # Проверяем, что это действительно процесс обучения
                    try:
                        proc = psutil.Process(old_pid)
                        cmdline = ' '.join(proc.cmdline())
                        if 'rag_trainer' in cmdline.lower() or 'enterprise_rag' in cmdline.lower():
                            print(f"❌ ОШИБКА: Обучение уже запущено!")
                            print(f"   PID активного процесса: {old_pid}")
                            print(f"   Время запуска: {lock_data.get('start_time')}")
                            print(f"   Команда: {cmdline}")
                            print("\\n💡 Для остановки активного обучения:")
                            print(f"   kill {old_pid}  # Linux/Mac")
                            print(f"   taskkill /PID {old_pid} /F  # Windows")
                            return False
                    except psutil.NoSuchProcess:
                        # Процесс не существует, удаляем старый lockfile
                        self.lockfile_path.unlink()
                else:
                    # PID не существует, удаляем старый lockfile
                    self.lockfile_path.unlink()
                    
            except (json.JSONDecodeError, KeyError):
                # Поврежденный lockfile, удаляем
                self.lockfile_path.unlink()
        
        # Создаем новый lockfile
        lock_data = {
            'pid': self.pid,
            'start_time': datetime.now().isoformat(),
            'hostname': os.uname().nodename if hasattr(os, 'uname') else 'windows',
            'command': ' '.join(sys.argv)
        }
        
        try:
            with open(self.lockfile_path, 'w') as f:
                json.dump(lock_data, f, indent=2)
            print(f"🔒 Блокировка получена: PID {self.pid}")
            return True
        except Exception as e:
            print(f"❌ Ошибка создания lockfile: {e}")
            return False
    
    def release_lock(self):
        """Освобождение блокировки"""
        try:
            if self.lockfile_path.exists():
                self.lockfile_path.unlink()
                print(f"🔓 Блокировка освобождена: PID {self.pid}")
        except Exception as e:
            print(f"⚠️ Ошибка освобождения блокировки: {e}")
    
    def __enter__(self):
        if not self.acquire_lock():
            sys.exit(1)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release_lock()

# Функция для использования в других скриптах
def ensure_single_training_instance():
    """Убеждаемся что запущен только один экземпляр обучения"""
    lock = RAGTrainingLock()
    return lock.acquire_lock()

if __name__ == "__main__":
    # Тест системы блокировки
    with RAGTrainingLock() as lock:
        print("Обучение запущено...")
        time.sleep(5)
        print("Обучение завершено")
'''
    
    with open("rag_training_lock.py", "w", encoding="utf-8") as f:
        f.write(lockfile_code)
    
    print("✅ Создан файл: rag_training_lock.py")

def create_safe_training_script():
    """Создание безопасного скрипта запуска обучения"""
    print("\n📝 СОЗДАНИЕ БЕЗОПАСНОГО СКРИПТА ЗАПУСКА")
    print("=" * 45)
    
    safe_script = '''#!/usr/bin/env python3
"""
Safe RAG Training Launcher
Безопасный запуск обучения RAG с блокировкой
"""

import sys
import os
from rag_training_lock import RAGTrainingLock

def main():
    print("🚀 БЕЗОПАСНЫЙ ЗАПУСК RAG ОБУЧЕНИЯ")
    print("=" * 40)
    
    # Проверяем блокировку
    with RAGTrainingLock() as lock:
        print("✅ Блокировка получена, запускаем обучение...")
        
        # Импортируем и запускаем основной тренер
        try:
            # Здесь должен быть импорт вашего основного тренера
            # import enterprise_rag_trainer_full
            # enterprise_rag_trainer_full.main()
            
            # Пока что запускаем через subprocess для безопасности
            import subprocess
            
            cmd = [
                sys.executable, 
                "enterprise_rag_trainer_full.py",
                "--custom_dir", "I:/docs/downloaded",
                "--fast_mode"
            ]
            
            print(f"Выполняем команду: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=False)
            
            if result.returncode == 0:
                print("✅ Обучение завершено успешно!")
            else:
                print(f"❌ Обучение завершилось с ошибкой: код {result.returncode}")
                
        except KeyboardInterrupt:
            print("\\n⚠️ Обучение прервано пользователем")
        except Exception as e:
            print(f"❌ Ошибка во время обучения: {e}")
        finally:
            print("🔓 Освобождаем блокировку...")

if __name__ == "__main__":
    main()
'''
    
    with open("safe_rag_training.py", "w", encoding="utf-8") as f:
        f.write(safe_script)
    
    print("✅ Создан файл: safe_rag_training.py")

def create_reset_and_train_script():
    """Создание скрипта для сброса и запуска обучения"""
    print("\n📝 СОЗДАНИЕ СКРИПТА СБРОСА И ОБУЧЕНИЯ")
    print("=" * 45)
    
    reset_and_train = '''@echo off
echo 🔥 ПОЛНЫЙ СБРОС И ПЕРЕЗАПУСК ОБУЧЕНИЯ RAG
echo ==========================================

echo.
echo ⚠️ ВНИМАНИЕ: Это удалит ВСЕ обученные данные!
echo Вы уверены что хотите продолжить?
pause

echo.
echo 🗑️ Сброс всех баз данных...
python reset_all_databases.py

echo.
echo ⏳ Ожидание 10 секунд для стабилизации системы...
timeout /t 10 /nobreak

echo.
echo 🚀 Запуск безопасного обучения...
python safe_rag_training.py

echo.
echo ✅ Процесс завершен!
pause
'''
    
    with open("reset_and_train.bat", "w", encoding="utf-8") as f:
        f.write(reset_and_train)
    
    print("✅ Создан файл: reset_and_train.bat")

def main():
    """Главная функция полного сброса"""
    print("💥 ПОЛНЫЙ СБРОС ВСЕХ БАЗ ДАННЫХ")
    print("=" * 50)
    print("⚠️ ВНИМАНИЕ: Это удалит ВСЕ обученные данные!")
    print("Включая Neo4j, векторные базы, JSON кэш и логи")
    print()
    
    confirm = input("Вы уверены? Введите 'YES' для подтверждения: ")
    if confirm != "YES":
        print("❌ Отменено пользователем")
        return
    
    print("\n🔥 НАЧИНАЕМ ПОЛНЫЙ СБРОС...")
    print("=" * 35)
    
    # Выполняем сброс по порядку
    kill_training_processes()
    reset_neo4j_database()
    reset_vector_database()
    reset_json_cache()
    reset_training_logs()
    
    # Создаем систему защиты
    create_lockfile_system()
    create_safe_training_script()
    create_reset_and_train_script()
    
    print("\n🎉 ПОЛНЫЙ СБРОС ЗАВЕРШЕН!")
    print("=" * 30)
    print("✅ Все базы данных очищены")
    print("✅ Система блокировки создана")
    print("✅ Безопасные скрипты созданы")
    print()
    print("📋 ЧТО ДЕЛАТЬ ДАЛЬШЕ:")
    print("1. Убедитесь что Neo4j Desktop запущен")
    print("2. Запустите: python safe_rag_training.py")
    print("   ИЛИ")
    print("   Запустите: reset_and_train.bat")
    print()
    print("💡 НОВЫЕ ВОЗМОЖНОСТИ:")
    print("• Защита от одновременного запуска")
    print("• Автоматическое определение активных процессов")
    print("• Безопасное завершение при ошибках")

if __name__ == "__main__":
    main()