#!/usr/bin/env python3
"""
Тест различных размеров чанков для DeepSeek-Coder
"""

import os
import sys
import time
import logging

# Отключаем кэш Python
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
os.environ['PYTHONUNBUFFERED'] = '1'

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_chunk_sizes():
    """Тест различных размеров чанков"""
    
    logger.info("=== ТЕСТ РАЗМЕРОВ ЧАНКОВ ===")
    
    try:
        from hybrid_llm_ensemble import HybridLLMEnsemble, HybridLLMConfig
        
        config = HybridLLMConfig.from_env()
        ensemble = HybridLLMEnsemble(config)
        
        if not ensemble.qwen_model:
            logger.error("❌ DeepSeek-Coder не загружен!")
            return False
        
        # Тестовые размеры чанков
        chunk_sizes = [512, 1024, 2048, 4096, 8192]
        
        for chunk_size in chunk_sizes:
            logger.info(f"🔍 Тестируем чанк размером {chunk_size} символов...")
            
            # Создаем тестовый текст нужного размера
            test_text = "СП 158.13330.2014 " * (chunk_size // 20)  # Примерно нужный размер
            test_text = test_text[:chunk_size]  # Обрезаем до точного размера
            
            prompt = f"""ЗАДАЧА: Исправь только очевидные ошибки.

ТЕКСТ: {test_text}

ИСПРАВЛЕННЫЙ:"""
            
            start_time = time.time()
            try:
                response = ensemble.qwen_model(
                    prompt,
                    max_tokens=chunk_size,
                    temperature=0.1,
                    stop=["ТЕКСТ:", "ЗАДАЧА:"]
                )
                
                elapsed = time.time() - start_time
                result = response['choices'][0]['text'].strip()
                
                logger.info(f"✅ Чанк {chunk_size}: {elapsed:.2f}s - {len(result)} символов")
                
                # Если чанк обрабатывается дольше 10 секунд, считаем его проблемным
                if elapsed > 10:
                    logger.warning(f"⚠️ Чанк {chunk_size} медленный: {elapsed:.2f}s")
                
            except Exception as e:
                logger.error(f"❌ Чанк {chunk_size} ОШИБКА: {e}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        return False

def test_optimal_chunk_size():
    """Поиск оптимального размера чанка"""
    
    logger.info("=== ПОИСК ОПТИМАЛЬНОГО РАЗМЕРА ЧАНКА ===")
    
    try:
        from hybrid_llm_ensemble import HybridLLMEnsemble, HybridLLMConfig
        
        config = HybridLLMConfig.from_env()
        ensemble = HybridLLMEnsemble(config)
        
        if not ensemble.qwen_model:
            logger.error("❌ DeepSeek-Coder не загружен!")
            return False
        
        # Тестируем размеры от 256 до 2048 с шагом 256
        optimal_size = 1024  # По умолчанию
        best_time = float('inf')
        
        for chunk_size in range(256, 2049, 256):
            logger.info(f"🔍 Тестируем оптимальный размер {chunk_size}...")
            
            test_text = "СП 158.13330.2014 " * (chunk_size // 20)
            test_text = test_text[:chunk_size]
            
            prompt = f"""ЗАДАЧА: Исправь только очевидные ошибки.

ТЕКСТ: {test_text}

ИСПРАВЛЕННЫЙ:"""
            
            start_time = time.time()
            try:
                response = ensemble.qwen_model(
                    prompt,
                    max_tokens=chunk_size,
                    temperature=0.1,
                    stop=["ТЕКСТ:", "ЗАДАЧА:"]
                )
                
                elapsed = time.time() - start_time
                
                if elapsed < best_time and elapsed < 5:  # Быстрее 5 секунд
                    best_time = elapsed
                    optimal_size = chunk_size
                
                logger.info(f"✅ Размер {chunk_size}: {elapsed:.2f}s")
                
            except Exception as e:
                logger.error(f"❌ Размер {chunk_size} ОШИБКА: {e}")
                continue
        
        logger.info(f"🎯 ОПТИМАЛЬНЫЙ РАЗМЕР ЧАНКА: {optimal_size} символов ({best_time:.2f}s)")
        return optimal_size
        
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        return 1024

if __name__ == "__main__":
    logger.info("🚀 ЗАПУСК ТЕСТОВ РАЗМЕРОВ ЧАНКОВ")
    
    # Тест 1: Различные размеры
    success1 = test_chunk_sizes()
    
    if success1:
        # Тест 2: Поиск оптимального размера
        optimal_size = test_optimal_chunk_size()
        logger.info(f"🎯 РЕКОМЕНДУЕМЫЙ РАЗМЕР ЧАНКА: {optimal_size}")
    else:
        logger.error("❌ Тесты размеров чанков не прошли!")
    
    logger.info("🏁 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
