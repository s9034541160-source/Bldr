#!/usr/bin/env python3
"""
Тестовый скрипт для проверки BldrRAGTrainer без LLM зависимостей
"""

from scripts.bldr_rag_trainer import BldrRAGTrainer
import os
import tempfile

def test_basic_pipeline():
    """Тестирует базовые стадии RAG trainer без LLM"""
    print("🧪 Тестирование BldrRAGTrainer без LLM зависимостей...")
    
    # Создаем тренер
    trainer = BldrRAGTrainer()
    print("✅ Trainer создан успешно")
    
    # Создаем тестовый файл
    test_content = """
    Тестовый документ для проверки работы системы.
    
    Раздел 1.1 Нормативные требования
    Данный документ содержит СП 31.13330.2012 требования.
    Работа по подготовке основания должна выполняться согласно нормам.
    
    Таблица 1: Материалы
    Бетон класса B25 - 100 м3
    Цемент М400 - 50 тонн
    
    Стоимость: 1500000 рублей
    Позиция 1: Земляные работы
    Позиция 2: Бетонные работы
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(test_content)
        test_file = f.name
    
    try:
        print(f"📄 Тестовый файл: {test_file}")
        
        # Stage 1: Валидация
        stage1_result = trainer._stage1_initial_validation(test_file)
        print(f"✅ Stage 1: {stage1_result['log']}")
        
        # Stage 2: Проверка дубликатов
        stage2_result = trainer._stage2_duplicate_checking(test_file)
        print(f"✅ Stage 2: {stage2_result['log']}")
        
        # Stage 3: Извлечение текста
        content = trainer._stage3_text_extraction(test_file)
        print(f"✅ Stage 3: Извлечено {len(content)} символов")
        
        # Stage 4: Определение типа документа
        doc_type_result = trainer._stage4_document_type_detection(content, test_file)
        print(f"✅ Stage 4: {doc_type_result['log']}")
        
        # Stage 5: Структурный анализ
        structural_result = trainer._stage5_structural_analysis(
            content, 
            doc_type_result['doc_type'], 
            doc_type_result['doc_subtype']
        )
        print(f"✅ Stage 5: {structural_result['log']}")
        
        # Stage 6: Извлечение работ (regex -> rubern)
        seed_works = trainer._stage6_regex_to_rubern(
            content, 
            doc_type_result['doc_type'], 
            structural_result['structural_data']
        )
        print(f"✅ Stage 6: Найдено {len(seed_works)} seed works")
        
        # Stage 7: Rubern разметка 
        rubern_data = trainer._stage7_rubern_markup(
            content,
            doc_type_result['doc_type'],
            doc_type_result['doc_subtype'],
            seed_works,
            structural_result['structural_data']
        )
        print(f"✅ Stage 7: Rubern разметка с {len(rubern_data.get('works', []))} работами")
        
        # Stage 8: Извлечение метаданных
        metadata = trainer._stage8_metadata_extraction(
            content,
            rubern_data,
            doc_type_result['doc_type']
        )
        print(f"✅ Stage 8: {len(metadata.get('materials', []))} материалов, {len(metadata.get('finances', []))} финансовых записей")
        
        # Stage 9: Контроль качества
        quality_score = trainer._stage9_quality_control(
            doc_type_result,
            structural_result['structural_data'],
            seed_works,
            rubern_data,
            metadata
        )
        print(f"✅ Stage 9: Оценка качества {quality_score:.2f}")
        
        # Stage 10: Типо-специфичная обработка (БЕЗ LLM!)
        type_specific_data = trainer._stage10_type_specific_processing(
            doc_type_result['doc_type'],
            doc_type_result['doc_subtype'],
            rubern_data
        )
        print(f"✅ Stage 10: Специфичная обработка, conf {type_specific_data.get('conf', 0.9)}")
        
        # Stage 11: Извлечение последовательности работ (БЕЗ tools_system!)
        work_sequences = trainer._stage11_work_sequence_extraction(rubern_data, metadata)
        print(f"✅ Stage 11: {len(work_sequences)} последовательностей работ")
        
        # Stage 12: Сохранение последовательности работ
        trainer._stage12_save_work_sequences(work_sequences)
        print(f"✅ Stage 12: Последовательности работ сохранены")
        
        # Stage 13: Умное разделение на чанки
        chunks = trainer._stage13_smart_chunking(rubern_data, metadata, doc_type_result)
        print(f"✅ Stage 13: Создано {len(chunks)} чанков")
        
        print("\n🎉 ВСЕ 13 СТАДИЙ РАБОТАЮТ БЕЗ LLM ЗАВИСИМОСТЕЙ!")
        print(f"📊 Итоговая статистика:")
        print(f"   - Тип документа: {doc_type_result['doc_type']}")
        print(f"   - Работы извлечены: {len(rubern_data.get('works', []))}")
        print(f"   - Последовательности работ: {len(work_sequences)}")
        print(f"   - Чанки созданы: {len(chunks)}")
        print(f"   - Оценка качества: {quality_score:.2f}")
        
    finally:
        # Удаляем тестовый файл
        try:
            os.unlink(test_file)
        except:
            pass

if __name__ == "__main__":
    test_basic_pipeline()