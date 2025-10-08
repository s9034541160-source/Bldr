#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для анализа оставшихся папок кэша на диске C:\\
"""

import os
from pathlib import Path

def get_folder_size_mb(path):
    """Получает размер папки в MB"""
    try:
        total_size = 0
        for file_path in path.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size / (1024 * 1024)
    except:
        return 0

def analyze_cache_folders():
    """Анализирует все папки кэша"""
    cache_path = Path.home() / ".cache"
    
    if not cache_path.exists():
        print("Папка .cache не найдена")
        return
    
    print("АНАЛИЗ ПАПОК КЭША НА ДИСКЕ C:\\")
    print("=" * 50)
    
    total_size = 0
    folders = []
    
    for item in cache_path.iterdir():
        if item.is_dir():
            size_mb = get_folder_size_mb(item)
            size_gb = size_mb / 1024
            total_size += size_mb
            
            folders.append({
                'name': item.name,
                'size_mb': size_mb,
                'size_gb': size_gb,
                'path': str(item)
            })
    
    # Сортируем по размеру
    folders.sort(key=lambda x: x['size_mb'], reverse=True)
    
    print(f"{'Папка':<25} {'Размер (MB)':<15} {'Размер (GB)':<15}")
    print("-" * 60)
    
    for folder in folders:
        print(f"{folder['name']:<25} {folder['size_mb']:<15.1f} {folder['size_gb']:<15.2f}")
    
    print("-" * 60)
    print(f"{'ИТОГО':<25} {total_size:<15.1f} {total_size/1024:<15.2f}")
    
    return folders

def suggest_cleanup(folders):
    """Предлагает что можно очистить"""
    print("\nРЕКОМЕНДАЦИИ ПО ОЧИСТКЕ:")
    print("=" * 50)
    
    for folder in folders:
        if folder['size_mb'] > 100:  # Больше 100MB
            print(f"\\nПапка: {folder['name']} ({folder['size_gb']:.2f}GB)")
            
            if folder['name'] == 'whisper':
                print("  Рекомендация: МОЖНО УДАЛИТЬ")
                print("  Описание: Кэш модели Whisper для распознавания речи")
                print("  Действие: Модель перезагрузится при следующем использовании")
                
            elif folder['name'] == 'puppeteer':
                print("  Рекомендация: МОЖНО УДАЛИТЬ")
                print("  Описание: Кэш браузера для автоматизации")
                print("  Действие: Браузер перезагрузится при следующем использовании")
                
            elif folder['name'] == 'ezdxf':
                print("  Рекомендация: МОЖНО УДАЛИТЬ")
                print("  Описание: Кэш для работы с CAD файлами")
                print("  Действие: Кэш пересоздастся при следующем использовании")
                
            else:
                print("  Рекомендация: ПРОВЕРИТЬ ВРУЧНУЮ")
                print("  Описание: Неизвестная папка кэша")

def create_cleanup_script(folders):
    """Создает скрипт для очистки"""
    script_content = '''#!/usr/bin/env python3
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
'''
    
    with open("cleanup_remaining_cache.py", "w", encoding="utf-8") as f:
        f.write(script_content)
    
    print(f"\nСоздан скрипт очистки: cleanup_remaining_cache.py")

def main():
    """Главная функция"""
    folders = analyze_cache_folders()
    
    if folders:
        suggest_cleanup(folders)
        create_cleanup_script(folders)
        
        print(f"\nОБЩИЙ РАЗМЕР ОСТАВШИХСЯ ПАПОК: {sum(f['size_mb'] for f in folders)/1024:.2f}GB")
        print("Для очистки запустите: python cleanup_remaining_cache.py")

if __name__ == "__main__":
    main()
