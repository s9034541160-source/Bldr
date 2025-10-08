#!/usr/bin/env python3
"""
Скрипт для проверки состояния Celery и Redis
"""

import os
import sys
import time
from pathlib import Path

def check_redis():
    """Проверка Redis"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis доступен")
        return True
    except Exception as e:
        print(f"❌ Redis недоступен: {e}")
        return False

def check_celery_config():
    """Проверка конфигурации Celery"""
    try:
        sys.path.append(str(Path(__file__).parent))
        from core.celery_app import celery_app
        
        print(f"✅ Celery app: {celery_app.main}")
        print(f"✅ Broker: {celery_app.conf.broker_url}")
        print(f"✅ Backend: {celery_app.conf.result_backend}")
        
        # Проверка подключения к брокеру
        try:
            celery_app.control.inspect().stats()
            print("✅ Celery может подключиться к брокеру")
            return True
        except Exception as e:
            print(f"❌ Celery не может подключиться к брокеру: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка конфигурации Celery: {e}")
        return False

def main():
    print("🔍 Проверка состояния Celery и Redis...")
    print("=" * 50)
    
    # Проверка Redis
    redis_ok = check_redis()
    print()
    
    # Проверка Celery
    celery_ok = check_celery_config()
    print()
    
    if redis_ok and celery_ok:
        print("✅ Все проверки пройдены успешно!")
        print("💡 Celery должен работать корректно")
    else:
        print("❌ Обнаружены проблемы:")
        if not redis_ok:
            print("   - Redis недоступен")
        if not celery_ok:
            print("   - Celery не может подключиться")
        
        print("\n🛠️ Рекомендации:")
        print("   1. Убедитесь, что Redis запущен: docker ps | grep redis")
        print("   2. Проверьте переменные окружения CELERY_BROKER_URL")
        print("   3. Попробуйте запустить Redis: docker start redis")

if __name__ == "__main__":
    main()
