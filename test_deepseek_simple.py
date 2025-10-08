#!/usr/bin/env python3
"""
Простой тест размеров промптов для DeepSeek-Coder (без таймаутов)
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

def test_deepseek_simple():
    """Простой тест размеров промптов"""
    
    logger.info("=== ПРОСТОЙ ТЕСТ РАЗМЕРОВ DEEPSEEK-CODER ===")
    
    try:
        from hybrid_llm_ensemble import HybridLLMEnsemble, HybridLLMConfig
        
        config = HybridLLMConfig.from_env()
        ensemble = HybridLLMEnsemble(config)
        
        if not ensemble.qwen_model:
            logger.error("❌ DeepSeek-Coder не загружен!")
            return False
        
        # Тестовые размеры промптов
        test_sizes = [500, 1000, 2000]
        
        for size in test_sizes:
            logger.info(f"🔍 Тестируем промпт размером {size} символов...")
            
            # Создаем тестовый текст нужного размера
            test_text = "СП 158.13330.2014 " * (size // 20)  # Примерно нужный размер
            test_text = test_text[:size]  # Обрезаем до точного размера
            
            prompt = f"""ЗАДАЧА: Исправь только очевидные ошибки.

ТЕКСТ: {test_text}

ИСПРАВЛЕННЫЙ:"""
            
            start_time = time.time()
            try:
                response = ensemble.qwen_model(
                    prompt,
                    max_tokens=min(size, 500),  # Ограничиваем max_tokens
                    temperature=0.1,
                    stop=["ТЕКСТ:", "ЗАДАЧА:"]
                )
                
                elapsed = time.time() - start_time
                result = response['choices'][0]['text'].strip()
                
                logger.info(f"✅ Размер {size}: {elapsed:.2f}s - {len(result)} символов")
                
                # Если промпт обрабатывается дольше 15 секунд, считаем его проблемным
                if elapsed > 15:
                    logger.warning(f"⚠️ Размер {size} медленный: {elapsed:.2f}s")
                    logger.info(f"🎯 РЕКОМЕНДУЕМЫЙ МАКСИМАЛЬНЫЙ РАЗМЕР: {size-200} символов")
                    return size-200
                
            except Exception as e:
                logger.error(f"❌ Размер {size} ОШИБКА: {e}")
                logger.info(f"🎯 РЕКОМЕНДУЕМЫЙ МАКСИМАЛЬНЫЙ РАЗМЕР: {size-200} символов")
                return size-200
        
        logger.info("🎉 ВСЕ РАЗМЕРЫ ПРОШЛИ! DeepSeek-Coder работает до 2000 символов")
        return 2000
        
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        return 1000

def test_optimal_size():
    """Поиск оптимального размера"""
    
    logger.info("=== ПОИСК ОПТИМАЛЬНОГО РАЗМЕРА ===")
    
    try:
        from hybrid_llm_ensemble import HybridLLMEnsemble, HybridLLMConfig
        
        config = HybridLLMConfig.from_env()
        ensemble = HybridLLMEnsemble(config)
        
        if not ensemble.qwen_model:
            logger.error("❌ DeepSeek-Coder не загружен!")
            return 1000
        
        # Тестируем размеры от 200 до 1500 с шагом 200
        optimal_size = 1000
        best_time = float('inf')
        
        for size in range(200, 1501, 200):
            logger.info(f"🔍 Тестируем размер {size}...")
            
            test_text = "СП 158.13330.2014 " * (size // 20)
            test_text = test_text[:size]
            
            prompt = f"""ЗАДАЧА: Исправь только очевидные ошибки.

ТЕКСТ: {test_text}

ИСПРАВЛЕННЫЙ:"""
            
            start_time = time.time()
            try:
                response = ensemble.qwen_model(
                    prompt,
                    max_tokens=min(size, 300),
                    temperature=0.1,
                    stop=["ТЕКСТ:", "ЗАДАЧА:"]
                )
                
                elapsed = time.time() - start_time
                
                if elapsed < best_time and elapsed < 8:  # Быстрее 8 секунд
                    best_time = elapsed
                    optimal_size = size
                
                logger.info(f"✅ Размер {size}: {elapsed:.2f}s")
                
                # Если размер обрабатывается дольше 10 секунд, останавливаемся
                if elapsed > 10:
                    logger.warning(f"⚠️ Размер {size} слишком медленный: {elapsed:.2f}s")
                    break
                
            except Exception as e:
                logger.error(f"❌ Размер {size} ОШИБКА: {e}")
                break
        
        logger.info(f"🎯 ОПТИМАЛЬНЫЙ РАЗМЕР: {optimal_size} символов ({best_time:.2f}s)")
        return optimal_size
        
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        return 1000

if __name__ == "__main__":
    logger.info("🚀 ЗАПУСК ПРОСТОГО ТЕСТА РАЗМЕРОВ")
    
    # Тест 1: Простые размеры
    max_size = test_deepseek_simple()
    
    if max_size < 2000:
        # Тест 2: Поиск оптимального размера
        optimal_size = test_optimal_size()
        logger.info(f"🎯 РЕКОМЕНДУЕМЫЙ РАЗМЕР: {optimal_size}")
        logger.info(f"🎯 МАКСИМАЛЬНЫЙ РАЗМЕР: {max_size}")
    else:
        logger.info("🎉 DeepSeek-Coder работает со всеми размерами!")
    
    logger.info("🏁 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
