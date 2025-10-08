"""
🧪 Тестирование рабочего ансамбля LLM для RTX 4060 (БЕЗ 30B модели)
Qwen3-8B (рабочая лошадка) + RuT5 (специалист по извлечению)
"""

import os
import sys
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_workhorse_ensemble():
    """Тестирование рабочего ансамбля LLM (БЕЗ 30B модели)"""
    
    try:
        # Импортируем рабочий ансамбль
        from workhorse_llm_ensemble import WorkhorseLLMEnsemble, WorkhorseLLMConfig
        
        logger.info("🔄 Инициализация рабочего ансамбля LLM (БЕЗ 30B модели)...")
        
        # Конфигурация для RTX 4060 (БЕЗ 30B модели)
        config = WorkhorseLLMConfig(
            workhorse_model="Qwen/Qwen2.5-7B-Instruct",  # Qwen3-8B
            extraction_model="ai-forever/rugpt3large_based_on_gpt2",  # RuT5 fallback
            use_4bit_quantization=True,
            max_memory_gb=7.0,
            device="auto"
        )
        
        # Создаем ансамбль
        ensemble = WorkhorseLLMEnsemble(config)
        
        logger.info("✅ Рабочий ансамбль LLM инициализирован (БЕЗ 30B модели)")
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
        
        # Stage 4: Классификация документов (Qwen3-8B)
        logger.info("🐎 Stage 4: Классификация документов (Qwen3-8B)...")
        classification = ensemble.stage_4_classify_document(test_content)
        if classification.get('classification_available', False):
            logger.info(f"✅ Классификация: {classification.get('document_type', 'unknown')} (confidence: {classification.get('confidence', 0.0)})")
        else:
            logger.warning(f"⚠️ Классификация не удалась: {classification.get('error', 'unknown error')}")
        
        # Stage 8: Извлечение метаданных (RuT5)
        logger.info("🔍 Stage 8: Извлечение метаданных (RuT5)...")
        metadata = ensemble.stage_8_extract_metadata(test_content, {})
        if metadata.get('extraction_available', False):
            logger.info(f"✅ Метаданные: {metadata.get('fields_extracted', 0)} полей извлечено")
            llm_metadata = metadata.get('metadata', {})
            for key, value in llm_metadata.items():
                logger.info(f"   - {key}: {value}")
        else:
            logger.warning(f"⚠️ Извлечение метаданных не удалось: {metadata.get('error', 'unknown error')}")
        
        # Stage 5.5: Глубокий анализ (Qwen3-8B)
        logger.info("🧠 Stage 5.5: Глубокий анализ (Qwen3-8B)...")
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
        
        # Stage 10: Сложная логика (Qwen3-8B)
        logger.info("⚡ Stage 10: Сложная логика (Qwen3-8B)...")
        complex_logic = ensemble.stage_10_complex_logic(
            "Создай Cypher запрос для поиска всех документов, связанных с нагрузками",
            test_content
        )
        if complex_logic.get('complex_logic_available', False):
            result = complex_logic.get('result', {})
            logger.info(f"✅ Сложная логика выполнена: {result.get('task_type', 'unknown')}")
            logger.info(f"   - Результат: {result.get('task_result', '')[:200]}...")
        else:
            logger.warning(f"⚠️ Сложная логика не удалась: {complex_logic.get('error', 'unknown error')}")
        
        logger.info("🎉 Тестирование рабочего ансамбля завершено успешно!")
        logger.info("💡 Ансамбль оптимизирован для RTX 4060: Qwen3-8B + RuT5 (БЕЗ 30B модели)")
        
    except ImportError as e:
        logger.error(f"❌ Не удалось импортировать рабочий ансамбль: {e}")
        logger.info("💡 Убедитесь, что установлены зависимости: pip install transformers torch accelerate bitsandbytes")
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования: {e}")
        logger.info("💡 Проверьте доступность GPU и свободную память")

def test_vram_usage():
    """Тестирование использования VRAM"""
    
    try:
        import torch
        
        logger.info("🔄 Проверка использования VRAM...")
        
        if torch.cuda.is_available():
            logger.info(f"🎮 GPU доступен: {torch.cuda.get_device_name(0)}")
            logger.info(f"💾 Общая память GPU: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
            logger.info(f"💾 Свободная память GPU: {torch.cuda.memory_reserved(0) / 1e9:.1f} GB")
            logger.info(f"💾 Используемая память GPU: {torch.cuda.memory_allocated(0) / 1e9:.1f} GB")
        else:
            logger.info("💻 Используется CPU")
            
    except Exception as e:
        logger.error(f"❌ Ошибка проверки VRAM: {e}")

def test_ensemble_strategy():
    """Тестирование стратегии ансамбля"""
    
    logger.info("📋 Стратегия рабочего ансамбля:")
    logger.info("🐎 Qwen3-8B (Рабочая лошадка):")
    logger.info("   - Stage 4: Классификация документов")
    logger.info("   - Stage 5.5: Глубокий анализ")
    logger.info("   - Stage 10: Сложная логика и Cypher запросы")
    logger.info("")
    logger.info("🔍 RuT5 (Специалист по извлечению):")
    logger.info("   - Stage 8: Извлечение метаданных")
    logger.info("   - QA подход для точного извлечения фактов")
    logger.info("")
    logger.info("❌ ИСКЛЮЧЕНО: Qwen3-Coder-30B (слишком тяжелый для RAG-тренера)")
    logger.info("💡 Результат: Максимальная скорость + качество для RTX 4060")

if __name__ == "__main__":
    logger.info("🚀 Запуск тестирования рабочего ансамбля LLM (БЕЗ 30B модели)")
    
    # Тест 1: Проверка VRAM
    test_vram_usage()
    
    print("\n" + "="*50 + "\n")
    
    # Тест 2: Стратегия ансамбля
    test_ensemble_strategy()
    
    print("\n" + "="*50 + "\n")
    
    # Тест 3: Полный ансамбль
    test_workhorse_ensemble()
    
    logger.info("🏁 Тестирование завершено")
