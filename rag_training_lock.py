#!/usr/bin/env python3
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
                            print("\n💡 Для остановки активного обучения:")
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
