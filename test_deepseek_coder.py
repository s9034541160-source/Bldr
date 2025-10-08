#!/usr/bin/env python3
"""
Тест DeepSeek-Coder для диагностики зависания
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

def test_deepseek_coder_simple():
    """Простой тест DeepSeek-Coder с минимальным промптом"""
    
    logger.info("=== ТЕСТ DEEPSEEK-CODER ===")
    
    try:
        from hybrid_llm_ensemble import HybridLLMEnsemble, HybridLLMConfig
        
        logger.info("1. Загрузка конфигурации...")
        config = HybridLLMConfig.from_env()
        
        logger.info("2. Инициализация HybridLLMEnsemble...")
        ensemble = HybridLLMEnsemble(config)
        
        logger.info("3. Проверка доступности DeepSeek-Coder...")
        if not ensemble.qwen_model:
            logger.error("❌ DeepSeek-Coder не загружен!")
            return False
            
        logger.info("✅ DeepSeek-Coder загружен успешно")
        
        # ТЕСТ 1: Минимальный промпт
        logger.info("4. ТЕСТ 1: Минимальный промпт...")
        simple_prompt = "Привет! Как дела?"
        
        start_time = time.time()
        try:
            response = ensemble.qwen_model(
                simple_prompt,
                max_tokens=50,
                temperature=0.1,
                stop=["\n", "Привет"]
            )
            elapsed = time.time() - start_time
            logger.info(f"✅ ТЕСТ 1 УСПЕХ: {elapsed:.2f}s - {response['choices'][0]['text'][:100]}")
        except Exception as e:
            logger.error(f"❌ ТЕСТ 1 ОШИБКА: {e}")
            return False
        
        # ТЕСТ 2: Промпт нормализации (короткий)
        logger.info("5. ТЕСТ 2: Короткий промпт нормализации...")
        short_text = "Это тест ов ый текст с пробелами."
        normalization_prompt = f"""ЗАДАЧА: Исправь только очевидные ошибки.

ТЕКСТ: {short_text}

ИСПРАВЛЕННЫЙ:"""
        
        start_time = time.time()
        try:
            response = ensemble.qwen_model(
                normalization_prompt,
                max_tokens=100,
                temperature=0.1,
                stop=["ТЕКСТ:", "ЗАДАЧА:"]
            )
            elapsed = time.time() - start_time
            result = response['choices'][0]['text'].strip()
            logger.info(f"✅ ТЕСТ 2 УСПЕХ: {elapsed:.2f}s - '{result}'")
        except Exception as e:
            logger.error(f"❌ ТЕСТ 2 ОШИБКА: {e}")
            return False
        
        # ТЕСТ 3: Промпт нормализации (средний)
        logger.info("6. ТЕСТ 3: Средний промпт нормализации...")
        medium_text = "Это тест ов ый текст с пробелами и переносами.\n\nМного пробелов    здесь."
        medium_prompt = f"""ЗАДАЧА: Исправь только очевидные ошибки.

ТЕКСТ: {medium_text}

ИСПРАВЛЕННЫЙ:"""
        
        start_time = time.time()
        try:
            response = ensemble.qwen_model(
                medium_prompt,
                max_tokens=200,
                temperature=0.1,
                stop=["ТЕКСТ:", "ЗАДАЧА:"]
            )
            elapsed = time.time() - start_time
            result = response['choices'][0]['text'].strip()
            logger.info(f"✅ ТЕСТ 3 УСПЕХ: {elapsed:.2f}s - '{result[:100]}...'")
        except Exception as e:
            logger.error(f"❌ ТЕСТ 3 ОШИБКА: {e}")
            return False
        
        # ТЕСТ 4: Большой чанк (как в реальном коде)
        logger.info("7. ТЕСТ 4: Большой чанк (4096 символов)...")
        large_text = "СП 158.13330.2014 " * 200  # ~4000 символов
        large_prompt = f"""ЗАДАЧА: Исправь только очевидные ошибки.

ТЕКСТ: {large_text}

ИСПРАВЛЕННЫЙ:"""
        
        start_time = time.time()
        try:
            response = ensemble.qwen_model(
                large_prompt,
                max_tokens=4096,
                temperature=0.1,
                stop=["ТЕКСТ:", "ЗАДАЧА:"]
            )
            elapsed = time.time() - start_time
            result = response['choices'][0]['text'].strip()
            logger.info(f"✅ ТЕСТ 4 УСПЕХ: {elapsed:.2f}s - {len(result)} символов")
        except Exception as e:
            logger.error(f"❌ ТЕСТ 4 ОШИБКА: {e}")
            return False
        
        logger.info("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        return True
        
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        return False

def test_deepseek_coder_timeout():
    """Тест с таймаутом для выявления зависания"""
    
    logger.info("=== ТЕСТ С ТАЙМАУТОМ ===")
    
    try:
        from hybrid_llm_ensemble import HybridLLMEnsemble, HybridLLMConfig
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("DeepSeek-Coder завис!")
        
        # Устанавливаем таймаут 30 секунд
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)
        
        try:
            config = HybridLLMConfig.from_env()
            ensemble = HybridLLMEnsemble(config)
            
            if not ensemble.qwen_model:
                logger.error("❌ DeepSeek-Coder не загружен!")
                return False
            
            # Тест с большим промптом
            large_text = "СП 158.13330.2014 " * 300  # ~6000 символов
            prompt = f"""ЗАДАЧА: Исправь только очевидные ошибки.

ТЕКСТ: {large_text}

ИСПРАВЛЕННЫЙ:"""
            
            logger.info("Отправка большого промпта...")
            start_time = time.time()
            
            response = ensemble.qwen_model(
                prompt,
                max_tokens=4096,
                temperature=0.1,
                stop=["ТЕКСТ:", "ЗАДАЧА:"]
            )
            
            elapsed = time.time() - start_time
            result = response['choices'][0]['text'].strip()
            
            signal.alarm(0)  # Отключаем таймаут
            logger.info(f"✅ ТЕСТ С ТАЙМАУТОМ УСПЕХ: {elapsed:.2f}s - {len(result)} символов")
            return True
            
        except TimeoutError:
            signal.alarm(0)
            logger.error("❌ ТАЙМАУТ! DeepSeek-Coder завис на 30 секунд!")
            return False
        except Exception as e:
            signal.alarm(0)
            logger.error(f"❌ ОШИБКА: {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 ЗАПУСК ТЕСТОВ DEEPSEEK-CODER")
    
    # Тест 1: Простые тесты
    success1 = test_deepseek_coder_simple()
    
    if success1:
        # Тест 2: Тест с таймаутом
        success2 = test_deepseek_coder_timeout()
        
        if success2:
            logger.info("🎉 ВСЕ ТЕСТЫ ПРОШЛИ! DeepSeek-Coder работает нормально.")
        else:
            logger.error("❌ DeepSeek-Coder зависает на больших промптах!")
    else:
        logger.error("❌ DeepSeek-Coder не работает даже на простых промптах!")
    
    logger.info("🏁 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
