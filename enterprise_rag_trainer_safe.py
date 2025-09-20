#!/usr/bin/env python3
"""
Enterprise RAG Trainer - Safe Version
Безопасная версия с защитой от одновременного запуска
"""

import os
import sys
import json
import time
import psutil
import signal
import atexit
from pathlib import Path
from datetime import datetime
from typing import Optional

# Добавляем текущую директорию в путь для импорта
sys.path.append(str(Path(__file__).parent))

class RAGTrainingLock:
    """Система блокировки RAG обучения"""
    
    def __init__(self, lockfile_path="./rag_training.lock"):
        self.lockfile_path = Path(lockfile_path)
        self.pid = os.getpid()
        self.locked = False
        
        # Регистрируем обработчики для корректного завершения
        atexit.register(self.release_lock)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов для корректного завершения"""
        print(f"\n⚠️ Получен сигнал {signum}, завершаем обучение...")
        self.release_lock()
        sys.exit(0)
        
    def acquire_lock(self) -> bool:
        """Получение блокировки"""
        if self.lockfile_path.exists():
            try:
                with open(self.lockfile_path, 'r', encoding='utf-8') as f:
                    lock_data = json.load(f)
                
                old_pid = lock_data.get('pid')
                if old_pid and psutil.pid_exists(old_pid):
                    try:
                        proc = psutil.Process(old_pid)
                        cmdline = ' '.join(proc.cmdline())
                        
                        # Проверяем, что это действительно процесс обучения RAG
                        if any(keyword in cmdline.lower() for keyword in [
                            'rag_trainer', 'enterprise_rag', 'train'
                        ]):
                            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Обучение RAG уже запущено!")
                            print("=" * 60)
                            print(f"🔒 PID активного процесса: {old_pid}")
                            print(f"📅 Время запуска: {lock_data.get('start_time')}")
                            print(f"💻 Хост: {lock_data.get('hostname', 'unknown')}")
                            print(f"⚡ Команда: {cmdline}")
                            print()
                            print("🛑 ОДНОВРЕМЕННЫЙ ЗАПУСК ЗАПРЕЩЕН!")
                            print("   Это может привести к:")
                            print("   • Конфликтам в базах данных")
                            print("   • Повреждению данных")
                            print("   • Ошибкам 'object cannot be re-sized'")
                            print()
                            print("💡 Для остановки активного обучения:")
                            if os.name == 'nt':  # Windows
                                print(f"   taskkill /PID {old_pid} /F")
                            else:  # Linux/Mac
                                print(f"   kill {old_pid}")
                            print("   ИЛИ нажмите Ctrl+C в окне активного обучения")
                            print()
                            return False
                    except psutil.NoSuchProcess:
                        # Процесс не существует, удаляем старый lockfile
                        print("🧹 Удаляем устаревший lockfile...")
                        self.lockfile_path.unlink()
                else:
                    # PID не существует, удаляем старый lockfile
                    print("🧹 Удаляем устаревший lockfile...")
                    self.lockfile_path.unlink()
                    
            except (json.JSONDecodeError, KeyError, FileNotFoundError):
                # Поврежденный lockfile, удаляем
                print("🧹 Удаляем поврежденный lockfile...")
                if self.lockfile_path.exists():
                    self.lockfile_path.unlink()
        
        # Создаем новый lockfile
        lock_data = {
            'pid': self.pid,
            'start_time': datetime.now().isoformat(),
            'hostname': os.uname().nodename if hasattr(os, 'uname') else os.getenv('COMPUTERNAME', 'windows'),
            'command': ' '.join(sys.argv),
            'working_dir': str(Path.cwd()),
            'python_version': sys.version
        }
        
        try:
            with open(self.lockfile_path, 'w', encoding='utf-8') as f:
                json.dump(lock_data, f, indent=2, ensure_ascii=False)
            
            self.locked = True
            print(f"🔒 Блокировка получена успешно!")
            print(f"   PID: {self.pid}")
            print(f"   Lockfile: {self.lockfile_path.absolute()}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка создания lockfile: {e}")
            return False
    
    def release_lock(self):
        """Освобождение блокировки"""
        if self.locked:
            try:
                if self.lockfile_path.exists():
                    self.lockfile_path.unlink()
                    print(f"🔓 Блокировка освобождена: PID {self.pid}")
                self.locked = False
            except Exception as e:
                print(f"⚠️ Ошибка освобождения блокировки: {e}")
    
    def __enter__(self):
        if not self.acquire_lock():
            sys.exit(1)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release_lock()

def check_system_requirements():
    """Проверка системных требований"""
    print("🔍 ПРОВЕРКА СИСТЕМНЫХ ТРЕБОВАНИЙ")
    print("=" * 40)
    
    # Проверка памяти
    memory = psutil.virtual_memory()
    print(f"💾 Оперативная память: {memory.total / 1024**3:.1f} GB")
    print(f"   Доступно: {memory.available / 1024**3:.1f} GB ({memory.percent:.1f}% используется)")
    
    if memory.available < 4 * 1024**3:  # Меньше 4 GB
        print("⚠️ ПРЕДУПРЕЖДЕНИЕ: Мало свободной памяти!")
        print("   Рекомендуется освободить память перед обучением")
    
    # Проверка диска
    disk = psutil.disk_usage('.')
    print(f"💿 Дисковое пространство: {disk.total / 1024**3:.1f} GB")
    print(f"   Свободно: {disk.free / 1024**3:.1f} GB ({(disk.free/disk.total)*100:.1f}%)")
    
    if disk.free < 10 * 1024**3:  # Меньше 10 GB
        print("⚠️ ПРЕДУПРЕЖДЕНИЕ: Мало свободного места на диске!")
        print("   Рекомендуется освободить место перед обучением")
    
    # Проверка процессора
    cpu_count = psutil.cpu_count()
    cpu_percent = psutil.cpu_percent(interval=1)
    print(f"🖥️ Процессор: {cpu_count} ядер, загрузка {cpu_percent:.1f}%")
    
    print("✅ Проверка системы завершена")

def check_neo4j_connection():
    """Проверка подключения к Neo4j"""
    print("\n🔌 ПРОВЕРКА NEO4J")
    print("=" * 20)
    
    try:
        import requests
        
        neo4j_urls = [
            "http://localhost:7474",
            "http://127.0.0.1:7474",
            "http://localhost:7475"
        ]
        
        for url in neo4j_urls:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ Neo4j доступен: {url}")
                    return True
            except requests.exceptions.RequestException:
                continue
        
        print("❌ Neo4j недоступен!")
        print("💡 Убедитесь что Neo4j Desktop запущен")
        return False
        
    except ImportError:
        print("⚠️ Модуль requests не найден, пропускаем проверку Neo4j")
        return True

def safe_import_trainer():
    """Безопасный импорт основного тренера"""
    print("\n📦 ИМПОРТ ОСНОВНОГО ТРЕНЕРА")
    print("=" * 30)
    
    try:
        # Пытаемся импортировать основной тренер
        trainer_files = [
            "enterprise_rag_trainer_full.py",
            "enterprise_rag_trainer.py", 
            "rag_trainer.py"
        ]
        
        for trainer_file in trainer_files:
            if Path(trainer_file).exists():
                print(f"✅ Найден тренер: {trainer_file}")
                
                # Импортируем как модуль
                import importlib.util
                spec = importlib.util.spec_from_file_location("trainer", trainer_file)
                trainer_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(trainer_module)
                
                return trainer_module
        
        print("❌ Основной тренер не найден!")
        print("💡 Убедитесь что файл enterprise_rag_trainer_full.py существует")
        return None
        
    except Exception as e:
        print(f"❌ Ошибка импорта тренера: {e}")
        return None

def main():
    """Главная функция безопасного запуска"""
    print("🛡️ БЕЗОПАСНЫЙ ЗАПУСК RAG ОБУЧЕНИЯ")
    print("=" * 50)
    print(f"🕐 Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python: {sys.version}")
    print(f"📁 Рабочая директория: {Path.cwd()}")
    print()
    
    # Получаем блокировку
    with RAGTrainingLock() as lock:
        print("\n✅ Эксклюзивная блокировка получена!")
        
        # Проверяем системные требования
        check_system_requirements()
        
        # Проверяем Neo4j
        if not check_neo4j_connection():
            print("\n❌ Neo4j недоступен, обучение невозможно")
            return 1
        
        # Импортируем основной тренер
        trainer_module = safe_import_trainer()
        if not trainer_module:
            print("\n❌ Не удалось загрузить основной тренер")
            return 1
        
        print("\n🚀 ЗАПУСК ОБУЧЕНИЯ")
        print("=" * 20)
        print("⚠️ НЕ ЗАПУСКАЙТЕ ДРУГИЕ ЭКЗЕМПЛЯРЫ ТРЕНЕРА!")
        print("   Это может привести к ошибкам в базах данных")
        print()
        
        try:
            # Запускаем основное обучение
            if hasattr(trainer_module, 'start_enterprise_training'):
                # Получаем параметры из аргументов командной строки или используем по умолчанию
                import argparse
                parser = argparse.ArgumentParser()
                parser.add_argument('--custom_dir', default='I:/docs/downloaded')
                parser.add_argument('--max_files', type=int, default=None)
                parser.add_argument('--fast_mode', action='store_true')
                args, _ = parser.parse_known_args()
                
                print(f"📁 Директория: {args.custom_dir}")
                print(f"📊 Макс. файлов: {'ALL' if args.max_files is None else args.max_files}")
                print(f"⚡ Быстрый режим: {'ДА' if args.fast_mode else 'НЕТ'}")
                print()
                
                # Запускаем обучение
                result = trainer_module.start_enterprise_training(args.custom_dir, args.max_files)
            else:
                print("❌ Функция start_enterprise_training() не найдена в тренере")
                return 1
            
            print("\n🎉 ОБУЧЕНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            return 0
            
        except KeyboardInterrupt:
            print("\n⚠️ Обучение прервано пользователем (Ctrl+C)")
            return 130
            
        except Exception as e:
            print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА ОБУЧЕНИЯ: {e}")
            import traceback
            traceback.print_exc()
            return 1
            
        finally:
            print("\n🔓 Освобождаем эксклюзивную блокировку...")

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n💥 ФАТАЛЬНАЯ ОШИБКА: {e}")
        sys.exit(1)