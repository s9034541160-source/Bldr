#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для переноса моделей с диска C:\\ на диск I:\\
Находит существующие модели Hugging Face и переносит их на диск I:\\
"""

import os
import shutil
import sys
from pathlib import Path
import time
from typing import List, Dict, Tuple

def find_huggingface_cache_dirs() -> List[Path]:
    """Находит все папки кэша Hugging Face на диске C:\\"""
    cache_dirs = []
    
    # Стандартные пути кэша Hugging Face
    possible_paths = [
        Path.home() / ".cache" / "huggingface",
        Path.home() / ".cache" / "transformers", 
        Path.home() / ".cache" / "torch",
        Path("C:/Users") / os.getenv("USERNAME", "user") / ".cache" / "huggingface",
        Path("C:/Users") / os.getenv("USERNAME", "user") / ".cache" / "transformers",
        Path("C:/Users") / os.getenv("USERNAME", "user") / ".cache" / "torch",
        Path("C:/") / ".cache" / "huggingface",
        Path("C:/") / ".cache" / "transformers",
    ]
    
    print("Поиск папок кэша Hugging Face...")
    
    for path in possible_paths:
        if path.exists() and path.is_dir():
            cache_dirs.append(path)
            print(f"Найдена папка: {path}")
    
    return cache_dirs

def find_model_directories(cache_dirs: List[Path]) -> List[Tuple[Path, str]]:
    """Находит папки с моделями в кэше"""
    model_dirs = []
    
    # Ключевые слова для поиска моделей
    model_keywords = [
        "qwen", "layoutlm", "rugpt", "sentence-transformers", 
        "microsoft", "ai-forever", "transformers", "models"
    ]
    
    print("\n🔍 Поиск папок с моделями...")
    
    for cache_dir in cache_dirs:
        try:
            for item in cache_dir.rglob("*"):
                if item.is_dir():
                    dir_name = item.name.lower()
                    for keyword in model_keywords:
                        if keyword in dir_name:
                            # Проверяем размер папки (больше 100MB)
                            size_mb = get_directory_size_mb(item)
                            if size_mb > 100:  # Больше 100MB
                                model_dirs.append((item, f"{size_mb:.1f}MB"))
                                print(f"✅ Найдена модель: {item} ({size_mb:.1f}MB)")
                                break
        except PermissionError:
            print(f"⚠️ Нет доступа к папке: {cache_dir}")
        except Exception as e:
            print(f"⚠️ Ошибка при сканировании {cache_dir}: {e}")
    
    return model_dirs

def get_directory_size_mb(path: Path) -> float:
    """Получает размер папки в MB"""
    try:
        total_size = 0
        for file_path in path.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size / (1024 * 1024)  # Конвертируем в MB
    except:
        return 0

def create_destination_dirs():
    """Создает папки назначения на диске I:\\"""
    dest_dirs = [
        Path("I:/huggingface_cache"),
        Path("I:/models_cache"),
        Path("I:/huggingface_cache/models"),
        Path("I:/huggingface_cache/datasets"),
        Path("I:/huggingface_cache/tokenizers"),
    ]
    
    print("\n📁 Создание папок назначения на диске I:\\...")
    
    for dest_dir in dest_dirs:
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
            print(f"✅ Создана папка: {dest_dir}")
        except Exception as e:
            print(f"❌ Ошибка создания папки {dest_dir}: {e}")
            return False
    
    return True

def migrate_models(model_dirs: List[Tuple[Path, str]]) -> Dict[str, bool]:
    """Переносит модели на диск I:\\"""
    results = {}
    
    print(f"\n🚀 Начинаем перенос {len(model_dirs)} моделей...")
    
    for i, (source_path, size_info) in enumerate(model_dirs, 1):
        print(f"\n📦 [{i}/{len(model_dirs)}] Перенос: {source_path.name} ({size_info})")
        
        try:
            # Определяем папку назначения
            if "models" in str(source_path) or any(keyword in source_path.name.lower() 
                                                 for keyword in ["qwen", "layoutlm", "rugpt", "microsoft", "ai-forever"]):
                dest_path = Path("I:/huggingface_cache/models") / source_path.name
            elif "datasets" in str(source_path):
                dest_path = Path("I:/huggingface_cache/datasets") / source_path.name
            elif "tokenizers" in str(source_path):
                dest_path = Path("I:/huggingface_cache/tokenizers") / source_path.name
            else:
                dest_path = Path("I:/huggingface_cache") / source_path.name
            
            # Проверяем, не существует ли уже папка назначения
            if dest_path.exists():
                print(f"⚠️ Папка уже существует: {dest_path}")
                results[str(source_path)] = True
                continue
            
            print(f"📂 Источник: {source_path}")
            print(f"📂 Назначение: {dest_path}")
            
            # Переносим папку
            start_time = time.time()
            shutil.copytree(source_path, dest_path)
            elapsed = time.time() - start_time
            
            print(f"✅ Успешно перенесено за {elapsed:.1f}с")
            results[str(source_path)] = True
            
        except Exception as e:
            print(f"❌ Ошибка переноса {source_path}: {e}")
            results[str(source_path)] = False
    
    return results

def update_environment_variables():
    """Обновляет переменные окружения для использования диска I:\\"""
    print("\n🔧 Настройка переменных окружения...")
    
    env_vars = {
        "HF_HOME": "I:/huggingface_cache",
        "TRANSFORMERS_CACHE": "I:/huggingface_cache", 
        "HF_DATASETS_CACHE": "I:/huggingface_cache",
        "LLM_CACHE_DIR": "I:/models_cache"
    }
    
    try:
        import winreg
        
        # Открываем реестр для записи переменных пользователя
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS) as key:
            for var_name, var_value in env_vars.items():
                winreg.SetValueEx(key, var_name, 0, winreg.REG_SZ, var_value)
                print(f"✅ Установлена переменная: {var_name}={var_value}")
        
        print("✅ Переменные окружения обновлены в реестре")
        print("📝 Перезапустите терминал для применения изменений")
        
    except Exception as e:
        print(f"⚠️ Не удалось обновить переменные окружения: {e}")
        print("📝 Установите переменные вручную:")
        for var_name, var_value in env_vars.items():
            print(f"   setx {var_name} \"{var_value}\"")

def cleanup_old_cache(model_dirs: List[Tuple[Path, str]], results: Dict[str, bool]):
    """Очищает старые папки кэша после успешного переноса"""
    print("\n🧹 Очистка старых папок кэша...")
    
    cleaned_count = 0
    for source_path, _ in model_dirs:
        if results.get(str(source_path), False):
            try:
                if source_path.exists():
                    shutil.rmtree(source_path)
                    print(f"✅ Удалена старая папка: {source_path}")
                    cleaned_count += 1
            except Exception as e:
                print(f"⚠️ Не удалось удалить {source_path}: {e}")
    
    print(f"✅ Очищено {cleaned_count} старых папок")

def main():
    """Главная функция"""
    print("🚀 МИГРАЦИЯ МОДЕЛЕЙ НА ДИСК I:\\")
    print("=" * 50)
    
    # Проверяем доступность диска I:\
    if not Path("I:/").exists():
        print("❌ Диск I:\\ не найден! Убедитесь, что диск подключен.")
        return
    
    # 1. Находим папки кэша
    cache_dirs = find_huggingface_cache_dirs()
    if not cache_dirs:
        print("⚠️ Папки кэша Hugging Face не найдены")
        print("💡 Возможно, модели еще не загружались")
        return
    
    # 2. Находим модели
    model_dirs = find_model_directories(cache_dirs)
    if not model_dirs:
        print("⚠️ Модели не найдены в кэше")
        return
    
    print(f"\n📊 Найдено {len(model_dirs)} моделей для переноса")
    
    # 3. Создаем папки назначения
    if not create_destination_dirs():
        print("❌ Не удалось создать папки назначения")
        return
    
    # 4. Переносим модели
    results = migrate_models(model_dirs)
    
    # 5. Статистика
    successful = sum(1 for success in results.values() if success)
    print(f"\n📊 РЕЗУЛЬТАТЫ ПЕРЕНОСА:")
    print(f"✅ Успешно перенесено: {successful}/{len(model_dirs)}")
    print(f"❌ Ошибок: {len(model_dirs) - successful}")
    
    # 6. Обновляем переменные окружения
    update_environment_variables()
    
    # 7. Очищаем старые папки (опционально)
    if successful > 0:
        response = input("\n🧹 Удалить старые папки кэша? (y/N): ")
        if response.lower() in ['y', 'yes', 'да']:
            cleanup_old_cache(model_dirs, results)
    
    print("\n🎉 МИГРАЦИЯ ЗАВЕРШЕНА!")
    print("📝 Перезапустите терминал для применения переменных окружения")

if __name__ == "__main__":
    main()
