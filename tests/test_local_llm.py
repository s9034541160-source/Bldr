"""
🧪 Тестирование локального российского LLM процессора
"""

import os
import sys
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_local_llm_processor():
    """Тестирование локального LLM процессора"""
    
    try:
        # Импортируем локальный LLM процессор
        from local_russian_llm_processor import LocalRussianLLMProcessor, LocalLLMConfig
        
        logger.info("🔄 Инициализация локального российского LLM...")
        
        # Конфигурация для тестирования
        config = LocalLLMConfig(
            model_name="ai-forever/rugpt3large_based_on_gpt2",
            device="auto",
            max_length=2048,  # Уменьшаем для тестирования
            temperature=0.1,
            use_quantization=True,
            cache_dir="./models_cache"
        )
        
        # Создаем процессор
        processor = LocalRussianLLMProcessor(config)
        
        logger.info("✅ Локальный LLM процессор инициализирован")
        logger.info(f"📊 Информация о модели: {processor.get_model_info()}")
        
        # Тестовый контент
        test_content = """
        СНиП 2.01.07-85* "Нагрузки и воздействия"
        
        1. ОБЩИЕ ПОЛОЖЕНИЯ
        1.1. Настоящие нормы устанавливают нагрузки и воздействия для расчета строительных конструкций.
        
        2. КЛАССИФИКАЦИЯ НАГРУЗОК
        2.1. По характеру изменения во времени нагрузки подразделяются на:
        - постоянные;
        - временные длительные;
        - кратковременные;
        - особые.
        
        3. ПОСТОЯННЫЕ НАГРУЗКИ
        3.1. К постоянным нагрузкам относятся:
        - собственный вес конструкций;
        - вес стационарного оборудования;
        - давление грунта.
        """
        
        # Тестовые VLM метаданные
        vlm_metadata = {
            'tables': [
                {'title': 'Таблица нагрузок', 'data': 'Данные таблицы'}
            ],
            'sections': [
                {'title': 'Общие положения', 'level': 1},
                {'title': 'Классификация нагрузок', 'level': 1}
            ]
        }
        
        logger.info("🧪 Запуск тестового анализа...")
        
        # Анализируем документ
        result = processor.analyze_document_structure(test_content, vlm_metadata)
        
        if result.get('local_llm_available', False):
            logger.info("✅ Анализ завершен успешно!")
            logger.info(f"📄 Тип документа: {result.get('analysis', {}).get('document_type', 'unknown')}")
            logger.info(f"📊 Секции: {len(result.get('analysis', {}).get('sections', []))}")
            logger.info(f"📋 Таблицы: {len(result.get('analysis', {}).get('tables', []))}")
            logger.info(f"⚡ Время обработки: {result.get('analysis', {}).get('processing_time', 0):.2f} сек")
            
            # Выводим детали анализа
            analysis = result.get('analysis', {})
            if 'requirements' in analysis:
                logger.info(f"📝 Требования: {len(analysis['requirements'])}")
                for req in analysis['requirements'][:3]:  # Показываем первые 3
                    logger.info(f"   - {req}")
            
            if 'scope' in analysis:
                logger.info(f"🎯 Область применения: {analysis['scope']}")
                
        else:
            logger.error(f"❌ Анализ не удался: {result.get('error', 'unknown error')}")
            
    except ImportError as e:
        logger.error(f"❌ Не удалось импортировать локальный LLM процессор: {e}")
        logger.info("💡 Убедитесь, что установлены зависимости: pip install transformers torch")
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования: {e}")
        logger.info("💡 Проверьте доступность GPU и свободную память")

def test_model_loading():
    """Тестирование загрузки модели"""
    
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        logger.info("🔄 Тестирование загрузки модели...")
        
        model_name = "ai-forever/rugpt3large_based_on_gpt2"
        
        # Загружаем токенизатор
        logger.info("📝 Загрузка токенизатора...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        logger.info("✅ Токенизатор загружен")
        
        # Тестируем токенизацию
        test_text = "Это тестовый текст для проверки токенизации."
        tokens = tokenizer.encode(test_text)
        logger.info(f"📊 Токенов в тесте: {len(tokens)}")
        
        # Проверяем доступность GPU
        import torch
        if torch.cuda.is_available():
            logger.info(f"🎮 GPU доступен: {torch.cuda.get_device_name(0)}")
            logger.info(f"💾 Память GPU: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        else:
            logger.info("💻 Используется CPU")
            
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки модели: {e}")

if __name__ == "__main__":
    logger.info("🚀 Запуск тестирования локального российского LLM")
    
    # Тест 1: Загрузка модели
    test_model_loading()
    
    print("\n" + "="*50 + "\n")
    
    # Тест 2: Полный анализ
    test_local_llm_processor()
    
    logger.info("🏁 Тестирование завершено")
