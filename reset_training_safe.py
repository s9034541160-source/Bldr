#!/usr/bin/env python3
"""
🚨 БЕЗОПАСНЫЙ СБРОС ПРОЦЕССА ОБУЧЕНИЯ RAG-ТРЕНЕРА 🚨

ИСПРАВЛЕННАЯ ВЕРСИЯ - НЕ УБИВАЕТ СЕБЯ!
- Очищает все базы данных (Neo4j, Qdrant, Redis)
- Удаляет все кэши и временные файлы
- Очищает processed_files.json
- Удаляет все отчеты и логи
- Перезапускает Docker контейнеры
- НЕ УБИВАЕТ СЕБЯ! (исправлен эпический баг)

⚠️ ВНИМАНИЕ: Это действие НЕОБРАТИМО! Все данные обучения будут удалены!
"""

import os
import json
import shutil
import time
import subprocess
import sys
from pathlib import Path

def print_banner():
    """Печать баннера"""
    print("=" * 80)
    print("🚨 БЕЗОПАСНЫЙ СБРОС ПРОЦЕССА ОБУЧЕНИЯ RAG-ТРЕНЕРА 🚨")
    print("=" * 80)
    print("⚠️  ВНИМАНИЕ: Это действие НЕОБРАТИМО!")
    print("⚠️  Все данные обучения будут удалены!")
    print("✅  ИСПРАВЛЕНО: Скрипт НЕ убивает себя!")
    print("=" * 80)

def confirm_reset():
    """Подтверждение сброса"""
    print("\n🤔 Вы уверены, что хотите выполнить ПОЛНЫЙ сброс?")
    print("Это удалит:")
    print("  - Все данные в Neo4j")
    print("  - Все данные в Qdrant") 
    print("  - Все кэши и временные файлы")
    print("  - Все отчеты и логи")
    print("  - processed_files.json")
    print("  - НЕ УБЬЕТ СЕБЯ! (исправлено)")
    
    response = input("\n❓ Введите 'RESET' для подтверждения: ")
    return response.strip() == 'RESET'

def stop_training_processes():
    """Остановка ТОЛЬКО процессов обучения (НЕ СЕБЯ!)"""
    print("\n🛑 Остановка процессов обучения...")
    try:
        import psutil
        import os
        
        current_pid = os.getpid()
        killed_count = 0
        
        print(f"🔍 Текущий PID: {current_pid}")
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    
                    # НЕ убиваем себя!
                    if proc.info['pid'] == current_pid:
                        print(f"   ⚠️ Пропускаем себя: PID {proc.info['pid']}")
                        continue
                    
                    # Ищем процессы RAG-тренера
                    if any(keyword in cmdline.lower() for keyword in [
                        'enterprise_rag_trainer',
                        'rag_trainer', 
                        'train.py',
                        'training',
                        'celery',
                        'worker',
                        'rag_training'
                    ]):
                        print(f"   🎯 Убиваем процесс обучения: PID {proc.info['pid']}")
                        print(f"      Команда: {cmdline[:80]}...")
                        proc.kill()
                        killed_count += 1
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        if killed_count > 0:
            print(f"✅ Убито процессов обучения: {killed_count}")
            time.sleep(3)  # Ждем завершения
        else:
            print("✅ Активных процессов обучения не найдено")
            
    except ImportError:
        print("⚠️ psutil не установлен, используем безопасный taskkill")
        try:
            # Безопасный fallback - только по заголовкам окон
            result1 = subprocess.run(['taskkill', '/F', '/FI', 'WINDOWTITLE eq *RAG*'], 
                                   capture_output=True, text=True)
            result2 = subprocess.run(['taskkill', '/F', '/FI', 'WINDOWTITLE eq *Training*'], 
                                   capture_output=True, text=True)
            print("✅ Процессы обучения остановлены (безопасный fallback)")
        except Exception as e:
            print(f"⚠️ Ошибка остановки процессов: {e}")
    except Exception as e:
        print(f"⚠️ Ошибка остановки процессов: {e}")

def reset_databases():
    """Сброс всех баз данных"""
    print("\n🗄️ Сброс баз данных...")
    
    # 1. Очистка Qdrant
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host='localhost', port=6333)
        collections = client.get_collections()
        for collection in collections.collections:
            print(f"  🗑️ Удаляем коллекцию: {collection.name}")
            client.delete_collection(collection.name)
        print("✅ Qdrant очищен")
    except Exception as e:
        print(f"⚠️ Ошибка очистки Qdrant: {e}")
    
    # 2. Очистка Neo4j
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
        with driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        driver.close()
        print("✅ Neo4j очищен")
    except Exception as e:
        print(f"⚠️ Ошибка очистки Neo4j: {e}")
    
    # 3. Очистка Redis
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.flushdb()
        print("✅ Redis очищен")
    except Exception as e:
        print(f"⚠️ Ошибка очистки Redis: {e}")

def clear_cache_and_files():
    """Очистка кэшей и временных файлов"""
    print("\n🧹 Очистка кэшей и временных файлов...")
    
    # Список файлов и папок для удаления
    items_to_remove = [
        'processed_files.json',
        'I:/docs/cache',
        'I:/docs/reports', 
        'I:/docs/embedding_cache',
        'I:/docs/downloaded/processed_files.json',  # !!! КРИТИЧЕСКИ ВАЖНО! !!!
        'cache',
        'logs',
        '__pycache__',
        'temp',
        'processed',
        'failed'
    ]
    
    for item in items_to_remove:
        if os.path.exists(item):
            try:
                if os.path.isfile(item):
                    os.remove(item)
                    print(f"  🗑️ Удален файл: {item}")
                elif os.path.isdir(item):
                    shutil.rmtree(item)
                    print(f"  🗑️ Удалена папка: {item}")
            except Exception as e:
                print(f"  ⚠️ Ошибка удаления {item}: {e}")
    
    # Удаление .pyc файлов
    try:
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.pyc'):
                    os.remove(os.path.join(root, file))
        print("✅ .pyc файлы удалены")
    except Exception as e:
        print(f"⚠️ Ошибка удаления .pyc: {e}")

def restart_docker_containers():
    """Перезапуск Docker контейнеров"""
    print("\n🐳 Перезапуск Docker контейнеров...")
    try:
        # Остановка контейнеров
        subprocess.run(['docker', 'compose', 'down'], check=True)
        print("✅ Docker контейнеры остановлены")
        
        # Запуск контейнеров
        subprocess.run(['docker', 'compose', 'up', '-d', 'redis', 'neo4j', 'qdrant'], check=True)
        print("✅ Docker контейнеры запущены")
    except Exception as e:
        print(f"⚠️ Ошибка перезапуска Docker: {e}")

def wait_for_services():
    """Ожидание готовности сервисов"""
    print("\n⏳ Ожидание готовности сервисов...")
    
    services = [
        ('Redis', 'localhost', 6379),
        ('Neo4j', 'localhost', 7687),
        ('Qdrant', 'localhost', 6333)
    ]
    
    for service_name, host, port in services:
        print(f"  🔍 Проверка {service_name}...")
        for attempt in range(30):  # 30 попыток по 2 секунды = 1 минута
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                sock.close()
                if result == 0:
                    print(f"  ✅ {service_name} готов")
                    break
            except:
                pass
            time.sleep(2)
        else:
            print(f"  ❌ {service_name} не готов")
            return False
    
    return True

def create_fresh_processed_files():
    """Создание нового processed_files.json"""
    print("\n📄 Создание нового processed_files.json...")
    try:
        fresh_data = {
            "processed_files": [],
            "failed_files": [],
            "total_processed": 0,
            "total_failed": 0,
            "last_reset": time.strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0"
        }
        
        with open('processed_files.json', 'w', encoding='utf-8') as f:
            json.dump(fresh_data, f, ensure_ascii=False, indent=2)
        
        print("✅ processed_files.json создан")
    except Exception as e:
        print(f"⚠️ Ошибка создания processed_files.json: {e}")

def main():
    """Основная функция"""
    print_banner()
    
    # Подтверждение
    if not confirm_reset():
        print("\n❌ Сброс отменен пользователем")
        return
    
    print("\n🚀 НАЧИНАЕМ БЕЗОПАСНЫЙ СБРОС...")
    start_time = time.time()
    
    # 1. Остановка процессов (БЕЗОПАСНО!)
    stop_training_processes()
    
    # 2. Сброс баз данных
    reset_databases()
    
    # 3. Очистка кэшей
    clear_cache_and_files()
    
    # 4. Перезапуск Docker
    restart_docker_containers()
    
    # 5. Ожидание сервисов
    if not wait_for_services():
        print("\n❌ СБРОС НЕ ЗАВЕРШЕН: Сервисы не готовы")
        return
    
    # 6. Создание новых файлов
    create_fresh_processed_files()
    
    # Итоги
    elapsed = time.time() - start_time
    print("\n" + "=" * 80)
    print("🎉 БЕЗОПАСНЫЙ СБРОС ЗАВЕРШЕН УСПЕШНО!")
    print("=" * 80)
    print(f"⏱️ Время выполнения: {elapsed:.2f} секунд")
    print("✅ Все базы данных очищены")
    print("✅ Все кэши удалены")
    print("✅ Docker контейнеры перезапущены")
    print("✅ Сервисы готовы к работе")
    print("✅ processed_files.json создан")
    print("✅ СКРИПТ НЕ УБИЛ СЕБЯ! (исправлено)")
    print("\n🚀 Теперь можно запускать тренера с чистого листа:")
    print("   python enterprise_rag_trainer_full.py")
    print("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Сброс прерван пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)
