#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для очистки оставшихся папок кэша
"""

import shutil
from pathlib import Path

def cleanup_cache():
    """Очищает папки кэша"""
    cache_path = Path.home() / ".cache"
    
    # Папки для очистки
    folders_to_clean = [
        "whisper",
        "puppeteer", 
        "ezdxf"
    ]
    
    print("ОЧИСТКА ПАПОК КЭША")
    print("=" * 30)
    
    for folder_name in folders_to_clean:
        folder_path = cache_path / folder_name
        if folder_path.exists():
            try:
                shutil.rmtree(folder_path)
                print(f"Удалена папка: {folder_name}")
            except Exception as e:
                print(f"Ошибка удаления {folder_name}: {e}")
        else:
            print(f"Папка не найдена: {folder_name}")
    
    print("Очистка завершена!")

if __name__ == "__main__":
    cleanup_cache()
