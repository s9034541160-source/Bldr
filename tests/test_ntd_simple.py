#!/usr/bin/env python3
"""
Простой тест NTDReferenceExtractor
"""
import sys
sys.path.append('.')

from core.ntd_reference_extractor import NTDReferenceExtractor

def test_ntd_simple():
    """Простой тест NTDReferenceExtractor"""
    
    print("TESTING NTD REFERENCE EXTRACTOR")
    print("=" * 50)
    
    # Создаем экстрактор
    extractor = NTDReferenceExtractor()
    
    # Тестовый текст
    test_text = """
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
    
    # Тест 1: Извлечение ссылок
    print("\n1. Testing NTD Reference Extraction:")
    references = extractor.extract_ntd_references(test_text, "test_document")
    print(f"   Found {len(references)} NTD references")
    
    for i, ref in enumerate(references[:5]):  # Показываем первые 5
        print(f"   {i+1}. {ref.canonical_id} ({ref.document_type}) - confidence: {ref.confidence:.2f}")
    
    # Тест 2: Статистика
    print("\n2. Testing Statistics:")
    stats = extractor.get_reference_statistics(references)
    print(f"   Total references: {stats['total_references']}")
    print(f"   High confidence (>=0.7): {stats['high_confidence']}")
    print(f"   Average confidence: {stats['average_confidence']:.2f}")
    print(f"   By type: {stats['by_type']}")
    
    # Тест 3: Библиография
    print("\n3. Testing Bibliography Extraction:")
    bib_references = extractor.extract_bibliography_references(test_text)
    print(f"   Found {len(bib_references)} references in bibliography")
    
    for i, ref in enumerate(bib_references[:3]):  # Показываем первые 3
        print(f"   {i+1}. {ref.canonical_id} ({ref.document_type}) - confidence: {ref.confidence:.2f}")
    
    # Тест 4: Контекст
    print("\n4. Testing Context Extraction:")
    for ref in references[:3]:  # Показываем первые 3
        context = ref.context[:80] + "..." if len(ref.context) > 80 else ref.context
        print(f"   {ref.canonical_id}: {context}")
    
    print("\n" + "=" * 50)
    print("NTD REFERENCE EXTRACTOR TEST COMPLETED!")

if __name__ == "__main__":
    test_ntd_simple()
