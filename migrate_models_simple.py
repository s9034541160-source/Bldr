#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для переноса моделей с диска C:\\ на диск I:\\
"""

import os
import shutil
import sys
from pathlib import Path
import time

def find_huggingface_cache():
    """Находит папки кэша Hugging Face"""
    cache_dirs = []
    
    # Стандартные пути
    possible_paths = [
        Path.home() / ".cache" / "huggingface",
        Path.home() / ".cache" / "transformers", 
        Path.home() / ".cache" / "torch",
    ]
    
    print("Поиск папок кэша Hugging Face...")
    
    for path in possible_paths:
        if path.exists() and path.is_dir():
            cache_dirs.append(path)
            print(f"Найдена папка: {path}")
    
    return cache_dirs

def get_directory_size_mb(path):
    """Получает размер папки в MB"""
    try:
        total_size = 0
        for file_path in path.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size / (1024 * 1024)
    except:
        return 0

def find_models(cache_dirs):
    """Находит модели в кэше"""
    model_dirs = []
    
    print("Поиск папок с моделями...")
    
    for cache_dir in cache_dirs:
        try:
            for item in cache_dir.rglob("*"):
                if item.is_dir():
                    size_mb = get_directory_size_mb(item)
                    if size_mb > 100:  # Больше 100MB
                        model_dirs.append((item, f"{size_mb:.1f}MB"))
                        print(f"Найдена модель: {item} ({size_mb:.1f}MB)")
        except Exception as e:
            print(f"Ошибка при сканировании {cache_dir}: {e}")
    
    return model_dirs

def create_dest_dirs():
    """Создает папки назначения"""
    dest_dirs = [
        Path("I:/huggingface_cache"),
        Path("I:/models_cache"),
    ]
    
    print("Создание папок назначения на диске I:\\...")
    
    for dest_dir in dest_dirs:
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
            print(f"Создана папка: {dest_dir}")
        except Exception as e:
            print(f"Ошибка создания папки {dest_dir}: {e}")
            return False
    
    return True

def migrate_models(model_dirs):
    """Переносит модели"""
    results = {}
    
    print(f"Начинаем перенос {len(model_dirs)} моделей...")
    
    for i, (source_path, size_info) in enumerate(model_dirs, 1):
        print(f"[{i}/{len(model_dirs)}] Перенос: {source_path.name} ({size_info})")
        
        try:
            dest_path = Path("I:/huggingface_cache") / source_path.name
            
            if dest_path.exists():
                print(f"Папка уже существует: {dest_path}")
                results[str(source_path)] = True
                continue
            
            print(f"Источник: {source_path}")
            print(f"Назначение: {dest_path}")
            
            start_time = time.time()
            shutil.copytree(source_path, dest_path)
            elapsed = time.time() - start_time
            
            print(f"Успешно перенесено за {elapsed:.1f}с")
            results[str(source_path)] = True
            
        except Exception as e:
            print(f"Ошибка переноса {source_path}: {e}")
            results[str(source_path)] = False
    
    return results

def main():
    """Главная функция"""
    print("МИГРАЦИЯ МОДЕЛЕЙ НА ДИСК I:\\")
    print("=" * 50)
    
    # Проверяем диск I:\
    if not Path("I:/").exists():
        print("Диск I:\\ не найден! Убедитесь, что диск подключен.")
        return
    
    # Находим кэш
    cache_dirs = find_huggingface_cache()
    if not cache_dirs:
        print("Папки кэша Hugging Face не найдены")
        return
    
    # Находим модели
    model_dirs = find_models(cache_dirs)
    if not model_dirs:
        print("Модели не найдены в кэше")
        return
    
    print(f"Найдено {len(model_dirs)} моделей для переноса")
    
    # Создаем папки
    if not create_dest_dirs():
        print("Не удалось создать папки назначения")
        return
    
    # Переносим
    results = migrate_models(model_dirs)
    
    # Статистика
    successful = sum(1 for success in results.values() if success)
    print(f"РЕЗУЛЬТАТЫ ПЕРЕНОСА:")
    print(f"Успешно перенесено: {successful}/{len(model_dirs)}")
    print(f"Ошибок: {len(model_dirs) - successful}")
    
    print("МИГРАЦИЯ ЗАВЕРШЕНА!")

if __name__ == "__main__":
    main()
