#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ПОЛНАЯ ОЧИСТКА ВСЕХ БАЗ ДАННЫХ И КЕША
=====================================
Скрипт для удаления всех следов предыдущих обработок
"""

import os
import shutil
from pathlib import Path

def clear_all_databases():
    """Полная очистка всех баз данных и кеша"""
    
    print("=== CLEARING ALL DATABASES & CACHE ===")
    
    # Возможные локации баз данных
    locations_to_clear = [
        # Bldr directory
        "C:/Bldr/qdrant_db",
        "C:/Bldr/data/qdrant_db", 
        "C:/Bldr/cache",
        "C:/Bldr/reports",
        "C:/Bldr/processed_files.json",
        
        # Downloaded docs directory
        "I:/docs/downloaded/qdrant_db",
        "I:/docs/downloaded/cache", 
        "I:/docs/downloaded/reports",
        "I:/docs/downloaded/processed_files.json",
        
        # Any other possible locations
        "C:/temp/qdrant_db",
        "C:/Users/papa/Documents/qdrant_db",
    ]
    
    cleared_count = 0
    
    for location in locations_to_clear:
        path = Path(location)
        try:
            if path.exists():
                if path.is_file():
                    path.unlink()
                    print(f"✓ Removed file: {location}")
                    cleared_count += 1
                elif path.is_dir():
                    shutil.rmtree(path)
                    print(f"✓ Removed directory: {location}")
                    cleared_count += 1
        except Exception as e:
            print(f"✗ Failed to remove {location}: {e}")
    
    # Очистка логов
    logs_dir = Path("C:/Bldr/logs")
    if logs_dir.exists():
        try:
            for log_file in logs_dir.glob("*.log"):
                log_file.unlink()
            print(f"✓ Cleared log files")
            cleared_count += 1
        except Exception as e:
            print(f"✗ Failed to clear logs: {e}")
    
    # Очистка embedding cache
    embed_cache_dir = Path("C:/Bldr/embedding_cache")
    if embed_cache_dir.exists():
        try:
            shutil.rmtree(embed_cache_dir)
            print(f"✓ Cleared embedding cache")
            cleared_count += 1
        except Exception as e:
            print(f"✗ Failed to clear embedding cache: {e}")
    
    print(f"\n=== CLEARING COMPLETE ===")
    print(f"Cleared {cleared_count} locations")
    print("All databases and cache are now clean!")
    print("Ready for fresh training run 🚀")

if __name__ == "__main__":
    clear_all_databases()