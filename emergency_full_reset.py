#!/usr/bin/env python3
"""
Emergency Full Reset
ЭКСТРЕННЫЙ ПОЛНЫЙ СБРОС ВСЕХ БАЗ ДАННЫХ
"""

import os
import sys
import shutil
import psutil
import time
import subprocess
from pathlib import Path

def kill_all_training_processes():
    """УБИВАЕМ ВСЕ ПРОЦЕССЫ ОБУЧЕНИЯ НЕМЕДЛЕННО"""
    print("💀 ЭКСТРЕННАЯ ОСТАНОВКА ВСЕХ ПРОЦЕССОВ")
    print("=" * 40)
    
    killed = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            
            # Ищем все процессы связанные с обучением
            if any(keyword in cmdline.lower() for keyword in [
                'rag_trainer', 'enterprise_rag', 'train', 'python'
            ]) and any(keyword in cmdline.lower() for keyword in [
                'enterprise', 'rag', 'trainer'
            ]):
                print(f"   💀 УБИВАЕМ: PID {proc.info['pid']} - {cmdline[:100]}")
                proc.kill()
                killed.append(proc.info['pid'])
                
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    if killed:
        print(f"✅ Убито процессов: {len(killed)}")
        time.sleep(5)
    else:
        print("✅ Активных процессов не найдено")

def force_stop_neo4j():
    """ПРИНУДИТЕЛЬНАЯ ОСТАНОВКА NEO4J"""
    print("\n💀 ПРИНУДИТЕЛЬНАЯ ОСТАНОВКА NEO4J")
    print("=" * 35)
    
    # Убиваем все Java процессы Neo4j
    os.system("taskkill /f /im java.exe 2>nul")
    os.system("taskkill /f /im \"Neo4j Desktop*.exe\" 2>nul")
    
    time.sleep(3)
    
    print("✅ Neo4j процессы остановлены")

def nuclear_reset_neo4j():
    """ЯДЕРНЫЙ СБРОС NEO4J - УДАЛЯЕМ ВСЕ ДАННЫЕ"""
    print("\n☢️ ЯДЕРНЫЙ СБРОС NEO4J")
    print("=" * 25)
    
    # Возможные пути к данным Neo4j
    neo4j_paths = [
        Path.home() / ".Neo4jDesktop",
        Path("C:/Users") / os.getenv('USERNAME', '') / "AppData/Roaming/Neo4j Desktop",
        Path("C:/neo4j"),
        Path("./neo4j-data"),
        Path("./data/neo4j")
    ]
    
    deleted_paths = []
    
    for neo4j_path in neo4j_paths:
        if neo4j_path.exists():
            print(f"   💣 УДАЛЯЕМ: {neo4j_path}")
            try:
                if neo4j_path.is_dir():
                    # Удаляем только папки с данными, не сам Neo4j Desktop
                    for item in neo4j_path.rglob("*"):
                        if any(keyword in str(item).lower() for keyword in [
                            'data', 'databases', 'graph.db', 'neo4j.db'
                        ]):
                            if item.is_dir():
                                shutil.rmtree(item, ignore_errors=True)
                            else:
                                item.unlink(missing_ok=True)
                            deleted_paths.append(str(item))
                else:
                    neo4j_path.unlink()
                    deleted_paths.append(str(neo4j_path))
            except Exception as e:
                print(f"   ⚠️ Ошибка удаления {neo4j_path}: {e}")
    
    if deleted_paths:
        print(f"✅ Удалено путей Neo4j: {len(deleted_paths)}")
    else:
        print("⚠️ Пути Neo4j не найдены")

def nuclear_reset_qdrant():
    """ЯДЕРНЫЙ СБРОС QDRANT"""
    print("\n☢️ ЯДЕРНЫЙ СБРОС QDRANT")
    print("=" * 25)
    
    # Останавливаем Qdrant процессы
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if 'qdrant' in cmdline.lower():
                print(f"   💀 Убиваем Qdrant: PID {proc.info['pid']}")
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    # Удаляем данные Qdrant
    qdrant_paths = [
        "./qdrant_storage",
        "./storage",
        "./qdrant_data",
        "I:/docs/qdrant_storage",
        Path.home() / ".qdrant",
        "./data/qdrant"
    ]
    
    deleted_qdrant = 0
    for qdrant_path in qdrant_paths:
        path = Path(qdrant_path)
        if path.exists():
            print(f"   💣 УДАЛЯЕМ Qdrant: {path}")
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                deleted_qdrant += 1
            except Exception as e:
                print(f"   ⚠️ Ошибка удаления Qdrant {path}: {e}")
    
    if deleted_qdrant > 0:
        print(f"✅ Удалено Qdrant хранилищ: {deleted_qdrant}")
    else:
        print("✅ Qdrant хранилища не найдены")

def nuclear_reset_all_caches():
    """ЯДЕРНЫЙ СБРОС ВСЕХ КЭШЕЙ"""
    print("\n☢️ ЯДЕРНЫЙ СБРОС ВСЕХ КЭШЕЙ")
    print("=" * 30)
    
    cache_paths = [
        "I:/docs/downloaded/cache",
        "I:/docs/cache", 
        "./cache",
        "./data",
        "./chroma_db",
        "./vector_db",
        "./embeddings",
        "./faiss_index",
        "./logs",
        "./training_logs",
        "./rag_logs",
        "./qdrant_storage",
        "./storage"
    ]
    
    total_deleted = 0
    
    for cache_path in cache_paths:
        path = Path(cache_path)
        if path.exists():
            print(f"   💣 УДАЛЯЕМ: {path}")
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                    total_deleted += 1
                else:
                    path.unlink()
                    total_deleted += 1
            except Exception as e:
                print(f"   ⚠️ Ошибка удаления {path}: {e}")
    
    print(f"✅ Удалено кэшей: {total_deleted}")

def delete_processed_files_json():
    """УДАЛЯЕМ processed_files.json"""
    print("\n🗑️ УДАЛЕНИЕ processed_files.json")
    print("=" * 30)
    
    json_files = [
        "I:/docs/downloaded/processed_files.json",
        "./processed_files.json",
        "./data/processed_files.json"
    ]
    
    deleted = 0
    for json_file in json_files:
        path = Path(json_file)
        if path.exists():
            print(f"   🗑️ Удаляем: {path}")
            path.unlink()
            deleted += 1
    
    if deleted > 0:
        print(f"✅ Удалено JSON файлов: {deleted}")
    else:
        print("✅ JSON файлы не найдены")

def restart_neo4j():
    """ПЕРЕЗАПУСК NEO4J"""
    print("\n🔄 ПЕРЕЗАПУСК NEO4J")
    print("=" * 20)
    
    neo4j_desktop_paths = [
        r"C:\Users\%USERNAME%\AppData\Local\Programs\Neo4j Desktop\Neo4j Desktop.exe",
        r"C:\Program Files\Neo4j Desktop\Neo4j Desktop.exe"
    ]
    
    for path in neo4j_desktop_paths:
        expanded_path = os.path.expandvars(path)
        if os.path.exists(expanded_path):
            print(f"   🚀 Запускаем: {expanded_path}")
            subprocess.Popen([expanded_path], shell=True)
            break
    
    print("⏳ Ждем запуска Neo4j (30 секунд)...")
    time.sleep(30)
    print("✅ Neo4j должен быть готов")

def main():
    """ЭКСТРЕННЫЙ ПОЛНЫЙ СБРОС"""
    print("☢️ ЭКСТРЕННЫЙ ПОЛНЫЙ СБРОС ВСЕХ БАЗ ДАННЫХ")
    print("=" * 60)
    print("⚠️ ЭТО УДАЛИТ АБСОЛЮТНО ВСЕ ДАННЫЕ!")
    print("⚠️ ВКЛЮЧАЯ ВСЕ ОБУЧЕННЫЕ МОДЕЛИ И КЭШИ!")
    print()
    
    print("🔥 НАЧИНАЕМ ЯДЕРНЫЙ СБРОС...")
    print("=" * 30)
    
    # 1. Убиваем все процессы
    kill_all_training_processes()
    
    # 2. Останавливаем Neo4j
    force_stop_neo4j()
    
    # 3. Ядерный сброс Neo4j
    nuclear_reset_neo4j()
    
    # 4. Ядерный сброс Qdrant
    nuclear_reset_qdrant()
    
    # 5. Ядерный сброс всех кэшей
    nuclear_reset_all_caches()
    
    # 6. Удаляем processed_files.json
    delete_processed_files_json()
    
    # 7. Перезапускаем Neo4j
    restart_neo4j()
    
    print("\n☢️ ЯДЕРНЫЙ СБРОС ЗАВЕРШЕН!")
    print("=" * 30)
    print("✅ ВСЕ базы данных уничтожены")
    print("✅ Neo4j полностью очищен")
    print("✅ Qdrant полностью очищен")
    print("✅ ВСЕ кэши удалены") 
    print("✅ ВСЕ логи очищены")
    print("✅ Neo4j перезапущен с чистой базой")
    print()
    print("🚀 ТЕПЕРЬ МОЖНО ЗАПУСКАТЬ ОБУЧЕНИЕ ЗАНОВО:")
    print("   python enterprise_rag_trainer_safe.py")
    print()
    print("💀 Обучение начнется с файла №1, а не с №231!")

if __name__ == "__main__":
    main()