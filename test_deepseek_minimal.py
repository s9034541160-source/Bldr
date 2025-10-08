#!/usr/bin/env python3
"""
Минимальный тест DeepSeek-Coder БЕЗ SBERT и RuT5
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

def test_deepseek_only():
    """Тест ТОЛЬКО DeepSeek-Coder без других моделей"""
    
    logger.info("=== МИНИМАЛЬНЫЙ ТЕСТ DEEPSEEK-CODER ===")
    
    try:
        from llama_cpp import Llama
        
        logger.info("1. Прямая загрузка DeepSeek-Coder...")
        
        # Прямая загрузка без ансамбля
        model_path = "I:/models_cache/TheBloke/deepseek-coder-6.7B-instruct-GGUF/deepseek-coder-6.7b-instruct.Q5_K_M.gguf"
        
        if not os.path.exists(model_path):
            logger.error(f"❌ Файл модели не найден: {model_path}")
            return False
        
        logger.info(f"2. Загрузка модели из {model_path}")
        
        # Минимальные параметры для экономии памяти
        llm = Llama(
            model_path=model_path,
            n_ctx=4096,  # Уменьшаем контекст
            n_gpu_layers=20,  # Меньше слоев на GPU
            n_threads=4,  # Меньше потоков
            verbose=False
        )
        
        logger.info("✅ DeepSeek-Coder загружен успешно!")
        
        # ТЕСТ 1: Простейший промпт
        logger.info("3. ТЕСТ 1: Простейший промпт...")
        start_time = time.time()
        
        try:
            response = llm(
                "Привет! Как дела?",
                max_tokens=50,
                temperature=0.1,
                stop=["\n"]
            )
            elapsed = time.time() - start_time
            result = response['choices'][0]['text'].strip()
            logger.info(f"✅ ТЕСТ 1 УСПЕХ: {elapsed:.2f}s - '{result}'")
        except Exception as e:
            logger.error(f"❌ ТЕСТ 1 ОШИБКА: {e}")
            return False
        
        # ТЕСТ 2: Промпт нормализации (короткий)
        logger.info("4. ТЕСТ 2: Короткий промпт нормализации...")
        start_time = time.time()
        
        try:
            prompt = """ЗАДАЧА: Исправь только очевидные ошибки.

ТЕКСТ: Это тест ов ый текст с пробелами.

ИСПРАВЛЕННЫЙ:"""
            
            response = llm(
                prompt,
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
        
        # ТЕСТ 3: Средний промпт
        logger.info("5. ТЕСТ 3: Средний промпт...")
        start_time = time.time()
        
        try:
            medium_text = "СП 158.13330.2014 " * 50  # ~1000 символов
            prompt = f"""ЗАДАЧА: Исправь только очевидные ошибки.

ТЕКСТ: {medium_text}

ИСПРАВЛЕННЫЙ:"""
            
            response = llm(
                prompt,
                max_tokens=200,
                temperature=0.1,
                stop=["ТЕКСТ:", "ЗАДАЧА:"]
            )
            elapsed = time.time() - start_time
            result = response['choices'][0]['text'].strip()
            logger.info(f"✅ ТЕСТ 3 УСПЕХ: {elapsed:.2f}s - {len(result)} символов")
        except Exception as e:
            logger.error(f"❌ ТЕСТ 3 ОШИБКА: {e}")
            return False
        
        # ТЕСТ 4: Большой промпт (как в реальном коде)
        logger.info("6. ТЕСТ 4: Большой промпт...")
        start_time = time.time()
        
        try:
            large_text = "СП 158.13330.2014 " * 200  # ~4000 символов
            prompt = f"""ЗАДАЧА: Исправь только очевидные ошибки.

ТЕКСТ: {large_text}

ИСПРАВЛЕННЫЙ:"""
            
            response = llm(
                prompt,
                max_tokens=1000,  # Уменьшаем max_tokens
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

if __name__ == "__main__":
    logger.info("🚀 ЗАПУСК МИНИМАЛЬНОГО ТЕСТА DEEPSEEK-CODER")
    
    success = test_deepseek_only()
    
    if success:
        logger.info("🎉 DeepSeek-Coder работает! Проблема в ансамбле.")
    else:
        logger.error("❌ DeepSeek-Coder не работает даже в минимальном режиме!")
    
    logger.info("🏁 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
