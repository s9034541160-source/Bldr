#!/usr/bin/env python3
"""
🚨 ПОЛНЫЙ СБРОС ПРОЦЕССА ОБУЧЕНИЯ RAG-ТРЕНЕРА 🚨

Этот скрипт выполняет ПОЛНЫЙ сброс всех данных обучения:
- Очищает все базы данных (Neo4j, Qdrant, Redis)
- Удаляет все кэши и временные файлы
- Очищает processed_files.json
- Удаляет все отчеты и логи
- Перезапускает Docker контейнеры

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
    print("🚨 ПОЛНЫЙ СБРОС ПРОЦЕССА ОБУЧЕНИЯ RAG-ТРЕНЕРА 🚨")
    print("=" * 80)
    print("⚠️  ВНИМАНИЕ: Это действие НЕОБРАТИМО!")
    print("⚠️  Все данные обучения будут удалены!")
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
    
    response = input("\n❓ Введите 'RESET' для подтверждения: ")
    return response.strip() == 'RESET'

def stop_processes():
    """Остановка процессов обучения (НЕ СЕБЯ!)"""
    print("\n🛑 Остановка процессов обучения...")
    try:
        import psutil
        import os
        
        current_pid = os.getpid()
        killed_count = 0
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    
                    # НЕ убиваем себя!
                    if proc.info['pid'] == current_pid:
                        continue
                    
                    # Ищем процессы RAG-тренера
                    if any(keyword in cmdline.lower() for keyword in [
                        'enterprise_rag_trainer',
                        'rag_trainer', 
                        'train.py',
                        'training',
                        'celery',
                        'worker'
                    ]):
                        print(f"   Убиваем процесс: PID {proc.info['pid']} - {cmdline[:50]}...")
                        proc.kill()
                        killed_count += 1
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        if killed_count > 0:
            print(f"✅ Убито процессов обучения: {killed_count}")
            time.sleep(2)  # Ждем завершения
        else:
            print("✅ Активных процессов обучения не найдено")
            
    except ImportError:
        print("⚠️ psutil не установлен, используем taskkill (осторожно!)")
        try:
            # Fallback на taskkill, но только для конкретных процессов
            subprocess.run(['taskkill', '/F', '/FI', 'WINDOWTITLE eq *RAG*'], 
                          capture_output=True, text=True)
            subprocess.run(['taskkill', '/F', '/FI', 'WINDOWTITLE eq *Training*'], 
                          capture_output=True, text=True)
            print("✅ Процессы обучения остановлены (fallback)")
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
        print(f"❌ Ошибка очистки Qdrant: {e}")
    
    # 2. Очистка Neo4j
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'neopassword'))
        with driver.session() as session:
            result = session.run('MATCH (n) DETACH DELETE n RETURN count(n) as deleted')
            deleted_count = result.single()['deleted']
            print(f"✅ Neo4j очищен: удалено {deleted_count} узлов")
        driver.close()
    except Exception as e:
        print(f"❌ Ошибка очистки Neo4j: {e}")
    
    # 3. Очистка Redis
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.flushdb()
        print("✅ Redis очищен")
    except Exception as e:
        print(f"❌ Ошибка очистки Redis: {e}")

def clear_cache_and_files():
    """Очистка кэшей и временных файлов"""
    print("\n🧹 Очистка кэшей и временных файлов...")
    
    # Список файлов и папок для удаления
    items_to_remove = [
        'processed_files.json',
        'I:/docs/cache',
        'I:/docs/reports', 
        'I:/docs/embedding_cache',
        'cache',
        'reports',
        'embedding_cache',
        'logs',
        'temp',
        'tmp'
    ]
    
    removed_count = 0
    for item in items_to_remove:
        try:
            if os.path.exists(item):
                if os.path.isfile(item):
                    os.remove(item)
                    print(f"  🗑️ Удален файл: {item}")
                    removed_count += 1
                elif os.path.isdir(item):
                    shutil.rmtree(item)
                    print(f"  🗑️ Удалена папка: {item}")
                    removed_count += 1
        except Exception as e:
            print(f"  ⚠️ Ошибка удаления {item}: {e}")
    
    print(f"✅ Очищено {removed_count} элементов")

def restart_docker_containers():
    """Перезапуск Docker контейнеров"""
    print("\n🐳 Перезапуск Docker контейнеров...")
    
    try:
        # Остановка всех контейнеров
        print("  🛑 Остановка контейнеров...")
        subprocess.run(['docker-compose', 'down'], 
                      capture_output=True, text=True)
        
        # Удаление томов
        print("  🗑️ Удаление томов...")
        subprocess.run(['docker', 'volume', 'rm', '-f', 'bldr_neo4j_data', 'bldr_neo4j_logs', 'bldr_qdrant_data'], 
                      capture_output=True, text=True)
        
        # Запуск контейнеров
        print("  🚀 Запуск контейнеров...")
        subprocess.run(['docker-compose', 'up', '-d'], 
                      capture_output=True, text=True)
        
        print("✅ Docker контейнеры перезапущены")
        
    except Exception as e:
        print(f"❌ Ошибка перезапуска Docker: {e}")

def wait_for_services():
    """Ожидание готовности сервисов"""
    print("\n⏳ Ожидание готовности сервисов...")
    
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            # Проверка Qdrant
            from qdrant_client import QdrantClient
            client = QdrantClient(host='localhost', port=6333)
            client.get_collections()
            
            # Проверка Neo4j
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'neopassword'))
            with driver.session() as session:
                session.run('RETURN 1')
            driver.close()
            
            # Проверка Redis
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            
            print("✅ Все сервисы готовы к работе")
            return True
            
        except Exception as e:
            if attempt < max_attempts - 1:
                print(f"  ⏳ Попытка {attempt + 1}/{max_attempts}...")
                time.sleep(2)
            else:
                print(f"❌ Сервисы не готовы: {e}")
                return False
    
    return False

def create_fresh_processed_files():
    """Создание нового processed_files.json"""
    print("\n📄 Создание нового processed_files.json...")
    
    try:
        with open('processed_files.json', 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
        print("✅ Создан пустой processed_files.json")
    except Exception as e:
        print(f"❌ Ошибка создания processed_files.json: {e}")

def main():
    """Основная функция"""
    print_banner()
    
    # Подтверждение
    if not confirm_reset():
        print("\n❌ Сброс отменен пользователем")
        return
    
    print("\n🚀 НАЧИНАЕМ ПОЛНЫЙ СБРОС...")
    start_time = time.time()
    
    # 1. Остановка процессов
    stop_processes()
    
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
    print("🎉 ПОЛНЫЙ СБРОС ЗАВЕРШЕН УСПЕШНО!")
    print("=" * 80)
    print(f"⏱️ Время выполнения: {elapsed:.2f} секунд")
    print("✅ Все базы данных очищены")
    print("✅ Все кэши удалены")
    print("✅ Docker контейнеры перезапущены")
    print("✅ Сервисы готовы к работе")
    print("✅ processed_files.json создан")
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
