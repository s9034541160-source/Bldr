#!/usr/bin/env python3
"""
Тест различных размеров промптов для DeepSeek-Coder
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

def test_deepseek_sizes():
    """Тест различных размеров промптов"""
    
    logger.info("=== ТЕСТ РАЗМЕРОВ ПРОМПТОВ DEEPSEEK-CODER ===")
    
    try:
        from hybrid_llm_ensemble import HybridLLMEnsemble, HybridLLMConfig
        
        config = HybridLLMConfig.from_env()
        ensemble = HybridLLMEnsemble(config)
        
        if not ensemble.qwen_model:
            logger.error("❌ DeepSeek-Coder не загружен!")
            return False
        
        # Тестовые размеры промптов
        test_sizes = [500, 1000, 2000, 3000, 4096]
        
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
                # Устанавливаем таймаут 30 секунд
                import signal
                
                def timeout_handler(signum, frame):
                    raise TimeoutError(f"DeepSeek-Coder завис на {size} символов!")
                
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(30)
                
                response = ensemble.qwen_model(
                    prompt,
                    max_tokens=min(size, 1000),  # Ограничиваем max_tokens
                    temperature=0.1,
                    stop=["ТЕКСТ:", "ЗАДАЧА:"]
                )
                
                signal.alarm(0)  # Отключаем таймаут
                elapsed = time.time() - start_time
                result = response['choices'][0]['text'].strip()
                
                logger.info(f"✅ Размер {size}: {elapsed:.2f}s - {len(result)} символов")
                
                # Если промпт обрабатывается дольше 10 секунд, считаем его проблемным
                if elapsed > 10:
                    logger.warning(f"⚠️ Размер {size} медленный: {elapsed:.2f}s")
                
            except TimeoutError as e:
                signal.alarm(0)
                logger.error(f"❌ ТАЙМАУТ на {size} символов: {e}")
                logger.info(f"🎯 МАКСИМАЛЬНЫЙ РАЗМЕР: {size-500} символов")
                return size-500
            except Exception as e:
                signal.alarm(0)
                logger.error(f"❌ Размер {size} ОШИБКА: {e}")
                return size-500
        
        logger.info("🎉 ВСЕ РАЗМЕРЫ ПРОШЛИ! DeepSeek-Coder работает до 4096 символов")
        return 4096
        
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        return 1000

def test_optimal_prompt_size():
    """Поиск оптимального размера промпта"""
    
    logger.info("=== ПОИСК ОПТИМАЛЬНОГО РАЗМЕРА ПРОМПТА ===")
    
    try:
        from hybrid_llm_ensemble import HybridLLMEnsemble, HybridLLMConfig
        
        config = HybridLLMConfig.from_env()
        ensemble = HybridLLMEnsemble(config)
        
        if not ensemble.qwen_model:
            logger.error("❌ DeepSeek-Coder не загружен!")
            return 1000
        
        # Тестируем размеры от 100 до 3000 с шагом 200
        optimal_size = 1000  # По умолчанию
        best_time = float('inf')
        
        for size in range(100, 3001, 200):
            logger.info(f"🔍 Тестируем оптимальный размер {size}...")
            
            test_text = "СП 158.13330.2014 " * (size // 20)
            test_text = test_text[:size]
            
            prompt = f"""ЗАДАЧА: Исправь только очевидные ошибки.

ТЕКСТ: {test_text}

ИСПРАВЛЕННЫЙ:"""
            
            start_time = time.time()
            try:
                import signal
                
                def timeout_handler(signum, frame):
                    raise TimeoutError(f"Таймаут на {size} символов!")
                
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(15)  # Короткий таймаут для быстрого тестирования
                
                response = ensemble.qwen_model(
                    prompt,
                    max_tokens=min(size, 500),
                    temperature=0.1,
                    stop=["ТЕКСТ:", "ЗАДАЧА:"]
                )
                
                signal.alarm(0)
                elapsed = time.time() - start_time
                
                if elapsed < best_time and elapsed < 5:  # Быстрее 5 секунд
                    best_time = elapsed
                    optimal_size = size
                
                logger.info(f"✅ Размер {size}: {elapsed:.2f}s")
                
            except TimeoutError:
                signal.alarm(0)
                logger.warning(f"⚠️ Таймаут на {size} символов")
                break
            except Exception as e:
                signal.alarm(0)
                logger.error(f"❌ Размер {size} ОШИБКА: {e}")
                break
        
        logger.info(f"🎯 ОПТИМАЛЬНЫЙ РАЗМЕР ПРОМПТА: {optimal_size} символов ({best_time:.2f}s)")
        return optimal_size
        
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        return 1000

if __name__ == "__main__":
    logger.info("🚀 ЗАПУСК ТЕСТОВ РАЗМЕРОВ ПРОМПТОВ")
    
    # Тест 1: Различные размеры
    max_size = test_deepseek_sizes()
    
    if max_size < 4096:
        # Тест 2: Поиск оптимального размера
        optimal_size = test_optimal_prompt_size()
        logger.info(f"🎯 РЕКОМЕНДУЕМЫЙ РАЗМЕР ПРОМПТА: {optimal_size}")
        logger.info(f"🎯 МАКСИМАЛЬНЫЙ РАЗМЕР: {max_size}")
    else:
        logger.info("🎉 DeepSeek-Coder работает со всеми размерами!")
    
    logger.info("🏁 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
