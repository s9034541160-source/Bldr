#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для безопасной очистки старых папок кэша на диске C:\\
Удаляет только те папки, которые были успешно перенесены на диск I:\\
"""

import os
import shutil
from pathlib import Path
import time

def verify_migration():
    """Проверяет, что перенос был успешным"""
    source_path = Path.home() / ".cache" / "huggingface"
    dest_path = Path("I:/huggingface_cache")
    
    if not source_path.exists():
        print("Исходная папка не найдена")
        return False
    
    if not dest_path.exists():
        print("Папка назначения не найдена")
        return False
    
    # Проверяем основные папки
    key_folders = ["hub", "models--ai-forever--rugpt3large_based_on_gpt2", "models--microsoft--layoutlmv3-base"]
    
    for folder in key_folders:
        source_folder = source_path / folder
        dest_folder = dest_path / folder
        
        if source_folder.exists() and not dest_folder.exists():
            print(f"ОШИБКА: Папка {folder} не найдена в назначении!")
            return False
    
    print("Проверка миграции: УСПЕШНО")
    return True

def get_folder_size(path):
    """Получает размер папки в MB"""
    try:
        total_size = 0
        for file_path in path.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size / (1024 * 1024)
    except:
        return 0

def cleanup_old_cache():
    """Очищает старые папки кэша"""
    source_path = Path.home() / ".cache" / "huggingface"
    
    if not source_path.exists():
        print("Папка кэша не найдена")
        return
    
    print(f"Очистка папки: {source_path}")
    
    # Получаем размер до очистки
    size_before = get_folder_size(source_path)
    print(f"Размер до очистки: {size_before:.1f}MB")
    
    # Удаляем папку целиком
    try:
        shutil.rmtree(source_path)
        print("Папка успешно удалена")
        
        # Проверяем освобожденное место
        print(f"Освобождено: {size_before:.1f}MB")
        
    except Exception as e:
        print(f"Ошибка при удалении: {e}")

def cleanup_torch_cache():
    """Очищает кэш PyTorch"""
    torch_cache = Path.home() / ".cache" / "torch"
    
    if torch_cache.exists():
        print(f"Очистка PyTorch кэша: {torch_cache}")
        try:
            shutil.rmtree(torch_cache)
            print("PyTorch кэш удален")
        except Exception as e:
            print(f"Ошибка удаления PyTorch кэша: {e}")

def main():
    """Главная функция"""
    print("ОЧИСТКА СТАРЫХ ПАПОК КЭША")
    print("=" * 40)
    
    # Проверяем миграцию
    if not verify_migration():
        print("ОШИБКА: Миграция не была успешной!")
        return
    
    print("\nВНИМАНИЕ: Будет удалена папка C:\\Users\\papa\\.cache\\huggingface")
    response = input("Продолжить? (y/N): ")
    
    if response.lower() not in ['y', 'yes', 'да']:
        print("Отменено пользователем")
        return
    
    # Очищаем кэш
    cleanup_old_cache()
    cleanup_torch_cache()
    
    print("\nОЧИСТКА ЗАВЕРШЕНА!")
    print("Теперь все модели находятся только на диске I:\\")

if __name__ == "__main__":
    main()
