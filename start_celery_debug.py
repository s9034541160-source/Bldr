#!/usr/bin/env python3
"""
Скрипт для запуска Celery с подробной диагностикой
"""

import os
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent))

def start_celery_worker():
    """Запуск Celery worker с диагностикой"""
    try:
        print("🚀 Запуск Celery Worker...")
        print("=" * 50)
        
        # Импортируем Celery app
        from core.celery_app import celery_app
        
        print(f"✅ Celery app загружен: {celery_app.main}")
        print(f"✅ Broker URL: {celery_app.conf.broker_url}")
        print(f"✅ Result backend: {celery_app.conf.result_backend}")
        
        # Запускаем worker
        print("\n🔄 Запуск worker...")
        celery_app.worker_main([
            'worker',
            '--loglevel=info',
            '--concurrency=1',  # Уменьшаем concurrency для стабильности
            '--pool=solo',       # Используем solo pool для Windows
            '--without-gossip',  # Отключаем gossip для простоты
            '--without-mingle',  # Отключаем mingle для простоты
            '--without-heartbeat' # Отключаем heartbeat для простоты
        ])
        
    except Exception as e:
        print(f"❌ Ошибка запуска Celery worker: {e}")
        import traceback
        traceback.print_exc()

def start_celery_beat():
    """Запуск Celery beat с диагностикой"""
    try:
        print("🚀 Запуск Celery Beat...")
        print("=" * 50)
        
        # Импортируем Celery app
        from core.celery_app import celery_app
        
        print(f"✅ Celery app загружен: {celery_app.main}")
        print(f"✅ Beat schedule: {celery_app.conf.beat_schedule}")
        
        # Запускаем beat
        print("\n🔄 Запуск beat...")
        celery_app.start([
            'beat',
            '--loglevel=info'
        ])
        
    except Exception as e:
        print(f"❌ Ошибка запуска Celery beat: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "worker":
            start_celery_worker()
        elif sys.argv[1] == "beat":
            start_celery_beat()
        else:
            print("Использование: python start_celery_debug.py [worker|beat]")
    else:
        print("Использование: python start_celery_debug.py [worker|beat]")
