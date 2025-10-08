#!/usr/bin/env python3
"""
Тест канонизации НТД - проверяем, что разные варианты одного НТД
приводят к одному каноническому ID
"""
import sys
sys.path.append('.')

from core.ntd_reference_extractor import NTDReferenceExtractor

def test_ntd_canonicalization():
    """Тестируем канонизацию НТД"""
    
    print("TESTING NTD CANONICALIZATION")
    print("=" * 60)
    
    extractor = NTDReferenceExtractor()
    
    # Тестовые случаи для канонизации
    test_cases = [
        # СП (Своды правил)
        ("СП 305.1325800.2017", "СП 305.1325800"),
        ("СП 305.1325800.20", "СП 305.1325800"),
        ("СП 305.1325800", "СП 305.1325800"),
        ("СП 305.1325800.2015", "СП 305.1325800"),
        ("изм.3 к СП 305.1325800.2017", "СП 305.1325800"),
        ("изменение 3 к СП 305.1325800.2017", "СП 305.1325800"),
        ("поправка 2 к СП 305.1325800.2017", "СП 305.1325800"),
        
        # СНиП
        ("СНиП 2.01.07-85", "СНиП 2.01.07"),
        ("СНиП 2.01.07", "СНиП 2.01.07"),
        ("изм.1 к СНиП 2.01.07-85", "СНиП 2.01.07"),
        
        # ГОСТ
        ("ГОСТ Р 54257-2010", "ГОСТ Р 54257"),
        ("ГОСТ 12.1.004-91", "ГОСТ 12.1.004"),
        ("ГОСТ 12.1.004", "ГОСТ 12.1.004"),
        
        # ГЭСН
        ("ГЭСНр-ОП-Разделы51-69", "ГЭСНР-ОП-РАЗДЕЛЫ51-69"),
        ("ГЭСН-ОП-51", "ГЭСН-ОП-51"),
        
        # Сложные случаи
        ("к СП 305.1325800.2017", "СП 305.1325800"),
        ("см. СП 305.1325800.2017", "СП 305.1325800"),
        ("согласно СП 305.1325800.2017", "СП 305.1325800"),
        ("Приложение А к СП 305.1325800.2017", "СП 305.1325800"),
    ]
    
    print("Testing individual canonicalization:")
    print("-" * 40)
    
    all_passed = True
    for input_id, expected in test_cases:
        result = extractor._canonicalize_ntd_id(input_id)
        status = "PASS" if result == expected else "FAIL"
        if result != expected:
            all_passed = False
        
        print(f"{status} '{input_id}' -> '{result}' (expected: '{expected}')")
    
    print("\n" + "=" * 60)
    
    # Тест полного извлечения с канонизацией
    print("Testing full extraction with canonicalization:")
    print("-" * 40)
    
    test_text = """
    СВОД ПРАВИЛ СП 305.1325800.2017 "СТАЛЬНЫЕ КОНСТРУКЦИИ"
    
    Настоящий свод правил разработан в соответствии с требованиями:
    - СНиП 2.01.07-85 "Нагрузки и воздействия"
    - ГОСТ 12.1.004-91 "Пожарная безопасность"
    - СП 20.13330.2016 "Нагрузки и воздействия"
    
    Дополнительные требования:
    - ГЭСНр-ОП-Разделы51-69 "Государственные элементные сметные нормы"
    - ФЕР 81-02-09-2001 "Федеральные единичные расценки"
    
    Изменения:
    - изм.3 к СП 305.1325800.2017
    - изменение 2 к СНиП 2.01.07-85
    
    В разделе "Библиография" указаны следующие источники:
    1. СП 20.13330.2016 "Нагрузки и воздействия"
    2. ГЭСНр-ОП-Разделы51-69 "Государственные элементные сметные нормы"
    3. ФЕР 81-02-09-2001 "Федеральные единичные расценки"
    """
    
    references = extractor.extract_ntd_references(test_text, "test_document")
    
    print(f"Found {len(references)} references:")
    print()
    
    # Группируем по каноническому ID
    canonical_groups = {}
    for ref in references:
        canonical_id = ref.canonical_id
        if canonical_id not in canonical_groups:
            canonical_groups[canonical_id] = []
        canonical_groups[canonical_id].append(ref)
    
    print("Canonical ID groups:")
    for canonical_id, refs in canonical_groups.items():
        print(f"  {canonical_id}:")
        for ref in refs:
            print(f"    - {ref.full_text} (confidence: {ref.confidence:.2f})")
        print()
    
    # Проверяем, что разные варианты одного НТД объединились
    print("Checking canonicalization results:")
    print("-" * 40)
    
    # Проверяем, что СП 305.1325800 объединился
    sp_305_refs = [ref for ref in references if 'СП 305.1325800' in ref.canonical_id]
    if len(sp_305_refs) > 0:
        print(f"PASS СП 305.1325800: {len(sp_305_refs)} references unified")
        for ref in sp_305_refs:
            print(f"   - {ref.full_text} -> {ref.canonical_id}")
    else:
        print("FAIL СП 305.1325800: No unified references found")
        all_passed = False
    
    # Проверяем, что СНиП 2.01.07 объединился
    snip_refs = [ref for ref in references if 'СНиП 2.01.07' in ref.canonical_id]
    if len(snip_refs) > 0:
        print(f"PASS СНиП 2.01.07: {len(snip_refs)} references unified")
        for ref in snip_refs:
            print(f"   - {ref.full_text} -> {ref.canonical_id}")
    else:
        print("FAIL СНиП 2.01.07: No unified references found")
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED! CANONICALIZATION WORKS PERFECTLY!")
        print("Different variants of the same NTD are unified into single canonical ID")
        print("Graph of Knowledge will have clean, deduplicated nodes")
        print("RAG system will correctly link all versions to one canonical document")
    else:
        print("SOME TESTS FAILED! Check canonicalization logic")
    
    return all_passed

if __name__ == "__main__":
    test_ntd_canonicalization()
