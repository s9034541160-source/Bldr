#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLEAR RAG DATA - ОЧИСТКА ДАННЫХ RAG
==================================

Полная очистка всех данных RAG для принудительной переобработки.
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('clear_rag_data.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def clear_neo4j_data():
    """ПРОПУСК ОЧИСТКИ Neo4j - БАЗА ДАННЫХ НЕ ОЧИЩАЕТСЯ"""
    logger.info("ℹ️ ПРОПУСК: Neo4j база данных НЕ очищается")
    logger.info("ℹ️ Существующие данные в Neo4j сохраняются")

def clear_qdrant_data():
    """ПРОПУСК ОЧИСТКИ Qdrant - БАЗА ДАННЫХ НЕ ОЧИЩАЕТСЯ"""
    logger.info("ℹ️ ПРОПУСК: Qdrant база данных НЕ очищается")
    logger.info("ℹ️ Существующие данные в Qdrant сохраняются")

def clear_file_cache():
    """Очистка только файлового кэша (БЕЗ БАЗ ДАННЫХ)"""
    logger.info("🗑️ Очистка файлового кэша...")
    
    # Очищаем только кэш, НЕ базы данных
    cache_dirs = [
        "I:/docs/downloaded/cache",
        "I:/docs/downloaded/embedding_cache", 
        "I:/docs/downloaded/reports",
        "cache",
        "embedding_cache",
        "reports"
    ]
    
    # НЕ очищаем qdrant_db - это база данных!
    logger.info("ℹ️ ПРОПУСК: qdrant_db НЕ очищается (это база данных)")
    
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                os.makedirs(cache_dir, exist_ok=True)
                logger.info(f"Очищена папка: {cache_dir}")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось очистить {cache_dir}: {e}")
        else:
            logger.info(f"ℹ️ Папка не существует: {cache_dir}")

def clear_processed_files():
    """Очистка списка обработанных файлов"""
    logger.info("🗑️ Очистка списка обработанных файлов...")
    
    processed_files = [
        "processed_files.json",
        "duplication_master_list.csv",
        "duplication_master_list_updated.csv"
    ]
    
    for file_path in processed_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Удален файл: {file_path}")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось удалить {file_path}: {e}")
        else:
            logger.info(f"ℹ️ Файл не существует: {file_path}")

def clear_logs():
    """Очистка логов"""
    logger.info("🗑️ Очистка логов...")
    
    log_files = [
        "rag_training.log",
        "force_retrain.log",
        "clear_rag_data.log",
        "gui_debug.log"
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            try:
                os.remove(log_file)
                logger.info(f"Удален лог: {log_file}")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось удалить {log_file}: {e}")

def create_backup():
    """Создание бэкапа перед очисткой"""
    logger.info("📦 Создание бэкапа...")
    
    backup_dir = f"backup_rag_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        os.makedirs(backup_dir, exist_ok=True)
        
        # Бэкап важных файлов
        important_files = [
            "processed_files.json",
            "duplication_master_list.csv",
            "duplication_master_list_updated.csv"
        ]
        
        for file_path in important_files:
            if os.path.exists(file_path):
                shutil.copy2(file_path, f"{backup_dir}/{file_path}")
                logger.info(f"Создан бэкап: {file_path}")
        
        # Бэкап кэша (БЕЗ БАЗ ДАННЫХ)
        cache_dirs = ["cache", "embedding_cache", "reports"]  # НЕ включаем qdrant_db!
        for cache_dir in cache_dirs:
            if os.path.exists(cache_dir):
                shutil.copytree(cache_dir, f"{backup_dir}/{cache_dir}")
                logger.info(f"Создан бэкап папки: {cache_dir}")
        
        logger.info("ℹ️ ПРОПУСК: qdrant_db НЕ включен в бэкап (это база данных)")
        
        logger.info(f"Бэкап создан в папке: {backup_dir}")
        return backup_dir
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания бэкапа: {e}")
        return None

def main():
    """Основная функция очистки"""
    logger.info("НАЧАЛО ОЧИСТКИ ДАННЫХ RAG")
    logger.info("=" * 50)
    
    try:
        # 1. Создаем бэкап
        backup_dir = create_backup()
        
        # 2. ПРОПУСК: Neo4j база данных НЕ очищается
        clear_neo4j_data()
        
        # 3. ПРОПУСК: Qdrant база данных НЕ очищается  
        clear_qdrant_data()
        
        # 4. Очищаем только файловый кэш (БЕЗ БАЗ ДАННЫХ)
        clear_file_cache()
        
        # 5. Очищаем список обработанных файлов
        clear_processed_files()
        
        # 6. Очищаем логи
        clear_logs()
        
        logger.info("ОЧИСТКА ДАННЫХ RAG ЗАВЕРШЕНА УСПЕШНО!")
        logger.info("=" * 50)
        logger.info("Теперь можно запускать RAG-тренер заново!")
        
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        raise

if __name__ == "__main__":
    main()
