#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RUN RAG RETRAIN - ЗАПУСК ПЕРЕОБРАБОТКИ RAG
========================================

Запуск RAG-тренера с принудительной переобработкой всех файлов.
"""

import os
import sys
import subprocess
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('run_rag_retrain.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_requirements():
    """Проверка требований для запуска"""
    logger.info("🔍 Проверка требований...")
    
    # Проверяем наличие основных файлов
    required_files = [
        "enterprise_rag_trainer_full.py",
        "clear_rag_data.py"
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            logger.error(f"❌ Не найден файл: {file_path}")
            return False
    
    # Проверяем папку с документами
    docs_dir = "I:/docs/downloaded"
    if not os.path.exists(docs_dir):
        logger.error(f"❌ Не найдена папка с документами: {docs_dir}")
        return False
    
    logger.info("✅ Все требования выполнены")
    return True

def clear_rag_data():
    """Очистка данных RAG"""
    logger.info("🧹 Очистка данных RAG...")
    
    try:
        # Запускаем скрипт очистки
        result = subprocess.run([sys.executable, "clear_rag_data.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ Данные RAG очищены успешно")
            return True
        else:
            logger.error(f"❌ Ошибка очистки данных: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка запуска очистки: {e}")
        return False

def run_rag_trainer():
    """Запуск RAG-тренера"""
    logger.info("🚀 Запуск RAG-тренера...")
    
    try:
        # Запускаем RAG-тренер
        result = subprocess.run([sys.executable, "enterprise_rag_trainer_full.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ RAG-тренер завершен успешно")
            return True
        else:
            logger.error(f"❌ Ошибка RAG-тренера: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка запуска RAG-тренера: {e}")
        return False

def main():
    """Основная функция"""
    logger.info("🎯 НАЧАЛО ПЕРЕОБРАБОТКИ RAG")
    logger.info("=" * 50)
    
    try:
        # 1. Проверяем требования
        if not check_requirements():
            logger.error("❌ Требования не выполнены!")
            return False
        
        # 2. Очищаем данные RAG
        if not clear_rag_data():
            logger.error("❌ Не удалось очистить данные RAG!")
            return False
        
        # 3. Запускаем RAG-тренер
        if not run_rag_trainer():
            logger.error("❌ Не удалось запустить RAG-тренер!")
            return False
        
        logger.info("✅ ПЕРЕОБРАБОТКА RAG ЗАВЕРШЕНА УСПЕШНО!")
        logger.info("=" * 50)
        return True
        
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
