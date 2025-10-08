"""
🧪 Тестирование ансамбля российских LLM для максимального качества RAG
"""

import os
import sys
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_llm_ensemble():
    """Тестирование ансамбля российских LLM"""
    
    try:
        # Импортируем ансамбль
        from russian_llm_ensemble import RussianLLMEnsemble, RussianLLMEnsembleConfig
        
        logger.info("🔄 Инициализация ансамбля российских LLM...")
        
        # Конфигурация ансамбля
        config = RussianLLMEnsembleConfig(
            classification_model="ai-forever/rugpt3large_based_on_gpt2",
            extraction_model="ai-forever/rugpt3large_based_on_gpt2",
            analysis_model="ai-forever/rugpt3large_based_on_gpt2",
            device="auto",
            use_quantization=True
        )
        
        # Создаем ансамбль
        ensemble = RussianLLMEnsemble(config)
        
        logger.info("✅ Ансамбль российских LLM инициализирован")
        logger.info(f"📊 Информация об ансамбле: {ensemble.get_ensemble_info()}")
        
        # Тестовый контент
        test_content = """
        СНиП 2.01.07-85* "Нагрузки и воздействия"
        
        Утвержден постановлением Госстроя России от 29.12.2020 № 1234
        Введен в действие с 1 января 2021 года
        
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
        
        # Stage 4: Классификация документов
        logger.info("📋 Stage 4: Классификация документов...")
        classification = ensemble.stage_4_classify_document(test_content)
        if classification.get('classification_available', False):
            logger.info(f"✅ Классификация: {classification.get('document_type', 'unknown')} (confidence: {classification.get('confidence', 0.0)})")
        else:
            logger.warning(f"⚠️ Классификация не удалась: {classification.get('error', 'unknown error')}")
        
        # Stage 8: Извлечение метаданных
        logger.info("🔍 Stage 8: Извлечение метаданных...")
        metadata = ensemble.stage_8_extract_metadata(test_content, {})
        if metadata.get('extraction_available', False):
            logger.info(f"✅ Метаданные: {metadata.get('fields_extracted', 0)} полей извлечено")
            llm_metadata = metadata.get('metadata', {})
            for key, value in llm_metadata.items():
                logger.info(f"   - {key}: {value}")
        else:
            logger.warning(f"⚠️ Извлечение метаданных не удалось: {metadata.get('error', 'unknown error')}")
        
        # Stage 5.5: Глубокий анализ
        logger.info("🧠 Stage 5.5: Глубокий анализ...")
        analysis = ensemble.stage_5_5_deep_analysis(test_content, vlm_metadata)
        if analysis.get('analysis_available', False):
            analysis_data = analysis.get('analysis', {})
            logger.info(f"✅ Анализ: {analysis.get('enhanced_sections', 0)} секций, {analysis.get('extracted_entities', 0)} сущностей")
            
            # Показываем секции
            sections = analysis_data.get('sections', [])
            for i, section in enumerate(sections[:3]):  # Показываем первые 3
                logger.info(f"   - Секция {i+1}: {section.get('title', 'Без названия')}")
            
            # Показываем сущности
            entities = analysis_data.get('entities', [])
            for i, entity in enumerate(entities[:3]):  # Показываем первые 3
                logger.info(f"   - Сущность {i+1}: {entity.get('text', '')} ({entity.get('type', 'unknown')})")
        else:
            logger.warning(f"⚠️ Глубокий анализ не удался: {analysis.get('error', 'unknown error')}")
        
        logger.info("🎉 Тестирование ансамбля завершено успешно!")
        
    except ImportError as e:
        logger.error(f"❌ Не удалось импортировать ансамбль LLM: {e}")
        logger.info("💡 Убедитесь, что установлены зависимости: pip install transformers torch")
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования: {e}")
        logger.info("💡 Проверьте доступность GPU и свободную память")

def test_individual_models():
    """Тестирование отдельных моделей"""
    
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        logger.info("🔄 Тестирование загрузки отдельных моделей...")
        
        model_name = "ai-forever/rugpt3large_based_on_gpt2"
        
        # Загружаем токенизатор
        logger.info("📝 Загрузка токенизатора...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        logger.info("✅ Токенизатор загружен")
        
        # Тестируем токенизацию
        test_text = "Это тестовый текст для проверки токенизации российского LLM."
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
    logger.info("🚀 Запуск тестирования ансамбля российских LLM")
    
    # Тест 1: Загрузка отдельных моделей
    test_individual_models()
    
    print("\n" + "="*50 + "\n")
    
    # Тест 2: Полный ансамбль
    test_llm_ensemble()
    
    logger.info("🏁 Тестирование завершено")
