#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FORCE RAG RETRAIN - ПРИНУДИТЕЛЬНАЯ ПЕРЕОБРАБОТКА
==============================================

Принудительная переобработка всех файлов из указанной папки
с исключением системных папок.
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
        logging.FileHandler('force_retrain.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def clear_rag_cache():
    """Очистка кэша RAG для принудительной переобработки"""
    cache_dirs = [
        "I:/docs/downloaded/cache",
        "I:/docs/downloaded/embedding_cache", 
        "I:/docs/downloaded/qdrant_db",
        "I:/docs/downloaded/reports"
    ]
    
    logger.info("🧹 Очистка кэша RAG...")
    
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                if cache_dir.endswith("qdrant_db"):
                    # Для Qdrant DB - удаляем содержимое, но оставляем папку
                    for item in os.listdir(cache_dir):
                        item_path = os.path.join(cache_dir, item)
                        if os.path.isfile(item_path):
                            os.remove(item_path)
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                    logger.info(f"✅ Очищена папка: {cache_dir}")
                else:
                    # Для остальных - полная очистка
                    shutil.rmtree(cache_dir)
                    os.makedirs(cache_dir, exist_ok=True)
                    logger.info(f"✅ Очищена и пересоздана папка: {cache_dir}")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось очистить {cache_dir}: {e}")
        else:
            logger.info(f"ℹ️ Папка не существует: {cache_dir}")

def clear_processed_files():
    """Очистка списка обработанных файлов"""
    processed_files_path = "processed_files.json"
    
    if os.path.exists(processed_files_path):
        try:
            os.remove(processed_files_path)
            logger.info("✅ Удален файл processed_files.json")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось удалить processed_files.json: {e}")
    else:
        logger.info("ℹ️ Файл processed_files.json не найден")

def get_files_to_process():
    """Получение списка файлов для обработки"""
    base_dir = "I:/docs/downloaded"
    exclude_dirs = ["reports", "qdrant_db", "embedding_cache", "cache"]
    
    files_to_process = []
    
    logger.info(f"🔍 Сканирование папки: {base_dir}")
    logger.info(f"🚫 Исключаем папки: {exclude_dirs}")
    
    for root, dirs, files in os.walk(base_dir):
        # Исключаем системные папки
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.lower().endswith(('.pdf', '.docx', '.xlsx', '.xls', '.txt', '.doc')):
                file_path = os.path.join(root, file)
                files_to_process.append(file_path)
    
    logger.info(f"📁 Найдено файлов для обработки: {len(files_to_process)}")
    return files_to_process

def backup_existing_data():
    """Создание бэкапа существующих данных"""
    backup_dir = f"backup_rag_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        os.makedirs(backup_dir, exist_ok=True)
        
        # Бэкап processed_files.json
        if os.path.exists("processed_files.json"):
            shutil.copy2("processed_files.json", f"{backup_dir}/processed_files.json")
            logger.info(f"✅ Создан бэкап processed_files.json в {backup_dir}")
        
        # Бэкап кэша (если есть)
        cache_dirs = ["I:/docs/downloaded/cache", "I:/docs/downloaded/embedding_cache"]
        for cache_dir in cache_dirs:
            if os.path.exists(cache_dir):
                cache_backup = f"{backup_dir}/{os.path.basename(cache_dir)}"
                shutil.copytree(cache_dir, cache_backup)
                logger.info(f"✅ Создан бэкап {cache_dir} в {cache_backup}")
        
        logger.info(f"✅ Бэкап создан в папке: {backup_dir}")
        return backup_dir
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания бэкапа: {e}")
        return None

def run_rag_trainer():
    """Запуск RAG-тренера"""
    logger.info("🚀 Запуск RAG-тренера...")
    
    try:
        # Импортируем и запускаем тренер
        from enterprise_rag_trainer_full import main as rag_main
        
        # Запускаем с принудительной переобработкой
        rag_main()
        
        logger.info("✅ RAG-тренер завершен успешно")
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска RAG-тренера: {e}")
        logger.error(f"Трассировка: {traceback.format_exc()}")
        raise

def main():
    """Основная функция принудительной переобработки"""
    logger.info("🎯 НАЧАЛО ПРИНУДИТЕЛЬНОЙ ПЕРЕОБРАБОТКИ RAG")
    logger.info("=" * 60)
    
    try:
        # 1. Создаем бэкап
        logger.info("📦 Создание бэкапа...")
        backup_dir = backup_existing_data()
        
        # 2. Очищаем кэш
        logger.info("🧹 Очистка кэша...")
        clear_rag_cache()
        clear_processed_files()
        
        # 3. Получаем список файлов
        logger.info("📁 Получение списка файлов...")
        files_to_process = get_files_to_process()
        
        if not files_to_process:
            logger.warning("⚠️ Не найдено файлов для обработки!")
            return
        
        logger.info(f"📊 Будет обработано файлов: {len(files_to_process)}")
        
        # 4. Запускаем RAG-тренер
        logger.info("🚀 Запуск RAG-тренера...")
        run_rag_trainer()
        
        logger.info("✅ ПРИНУДИТЕЛЬНАЯ ПЕРЕОБРАБОТКА ЗАВЕРШЕНА УСПЕШНО!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        logger.error(f"Трассировка: {traceback.format_exc()}")
        raise

if __name__ == "__main__":
    main()
