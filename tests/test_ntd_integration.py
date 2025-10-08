#!/usr/bin/env python3
"""
Тест интеграции NTDReferenceExtractor в Stage 12
"""
import sys
sys.path.append('.')

from enterprise_rag_trainer_full import EnterpriseRAGTrainer
from pathlib import Path
import tempfile
import os

def test_ntd_integration():
    """Тестируем интеграцию NTDReferenceExtractor в Stage 12"""
    
    print("TESTING NTD REFERENCE EXTRACTOR INTEGRATION")
    print("=" * 60)
    
    # Создаем экземпляр тренера
    trainer = EnterpriseRAGTrainer()
    
    # Создаем временный файл с тестовым содержимым
    test_content = """
    Согласно СП 16.13330.2017 "Стальные конструкции" и СНиП 2.01.07-85 "Нагрузки и воздействия",
    конструкции должны быть рассчитаны в соответствии с ГОСТ 12.1.004-91.
    
    В разделе "Библиография" указаны следующие источники:
    1. СП 20.13330.2016 "Нагрузки и воздействия"
    2. ГЭСНр-ОП-Разделы51-69 "Государственные элементные сметные нормы"
    3. ФЕР 81-02-09-2001 "Федеральные единичные расценки"
    4. ТЕР 81-02-09-2001 "Территориальные единичные расценки"
    
    Дополнительные требования:
    - Постановление Правительства РФ от 12.02.2018 N 130
    - Приказ от 15.03.2019 N 45
    - Федеральный закон от 01.01.2020 N 1
    """
    
    # Создаем временный файл
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(test_content)
        temp_file_path = f.name
    
    try:
        # Тест 1: Извлечение ссылок на НТД
        print("\n1. Testing NTD Reference Extraction:")
        metadata = {'doc_type': 'norms', 'canonical_id': 'СП 16.13330.2017'}
        
        references = trainer._extract_ntd_references_from_document(temp_file_path, metadata)
        print(f"   Found {len(references)} NTD references")
        
        for i, ref in enumerate(references[:5]):  # Показываем первые 5
            print(f"   {i+1}. {ref['canonical_id']} ({ref['document_type']}) - уверенность: {ref['confidence']:.2f}")
        
        # Тест 2: Статистика по ссылкам
        print("\n2. Testing NTD Reference Statistics:")
        stats = trainer._get_ntd_reference_statistics(references)
        print(f"   Total references: {stats['total_references']}")
        print(f"   High confidence (≥0.7): {stats['high_confidence']}")
        print(f"   Average confidence: {stats['average_confidence']:.2f}")
        print(f"   By type: {stats['by_type']}")
        
        # Тест 3: Проверка типов документов
        print("\n3. Testing Document Types:")
        doc_types = set(ref['document_type'] for ref in references)
        print(f"   Found document types: {sorted(doc_types)}")
        
        # Тест 4: Проверка уверенности
        print("\n4. Testing Confidence Levels:")
        high_conf = [ref for ref in references if ref['confidence'] >= 0.7]
        medium_conf = [ref for ref in references if 0.5 <= ref['confidence'] < 0.7]
        low_conf = [ref for ref in references if ref['confidence'] < 0.5]
        
        print(f"   High confidence (≥0.7): {len(high_conf)}")
        print(f"   Medium confidence (0.5-0.7): {len(medium_conf)}")
        print(f"   Low confidence (<0.5): {len(low_conf)}")
        
        # Тест 5: Проверка контекста
        print("\n5. Testing Context Extraction:")
        for ref in references[:3]:  # Показываем первые 3
            context = ref['context'][:100] + "..." if len(ref['context']) > 100 else ref['context']
            print(f"   {ref['canonical_id']}: {context}")
        
        print("\n" + "=" * 60)
        print("NTD REFERENCE EXTRACTOR INTEGRATION TEST COMPLETED!")
        
    finally:
        # Удаляем временный файл
        os.unlink(temp_file_path)

if __name__ == "__main__":
    test_ntd_integration()
