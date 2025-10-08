#!/usr/bin/env python3
"""
Тест сценарной метадата-идентификации
"""
import sys
sys.path.append('.')

from core.metadata_dispatcher import MetadataDispatcher

def test_scenario_metadata():
    """Тестируем различные сценарии извлечения метаданных"""
    
    print("TESTING SCENARIO-BASED METADATA EXTRACTION")
    print("=" * 60)
    
    dispatcher = MetadataDispatcher()
    
    # Тест 1: НТД (СП)
    print("\n1. Testing NTD (SP) extraction:")
    ntd_content = "СП 88.13330.2014 Защитные сооружения гражданской обороны"
    ntd_doc_type = {'doc_type': 'norms', 'subtype': 'sp'}
    ntd_metadata = dispatcher.extract_metadata(ntd_content, ntd_doc_type)
    print(f"   Canonical ID: {ntd_metadata.canonical_id}")
    print(f"   Title: {ntd_metadata.title}")
    print(f"   Method: {ntd_metadata.extraction_method}")
    print(f"   Confidence: {ntd_metadata.confidence:.2f}")
    
    # Тест 2: ГЭСН
    print("\n2. Testing GESN extraction:")
    gesn_content = "ГОСУДАРСТВЕННЫЕ СМЕТНЫЕ НОРМАТИВЫ ГЭСНр-ОП-Разделы51-69"
    gesn_doc_type = {'doc_type': 'smeta', 'subtype': 'gesn'}
    gesn_metadata = dispatcher.extract_metadata(gesn_content, gesn_doc_type)
    print(f"   Canonical ID: {gesn_metadata.canonical_id}")
    print(f"   Title: {gesn_metadata.title}")
    print(f"   Method: {gesn_metadata.extraction_method}")
    print(f"   Confidence: {gesn_metadata.confidence:.2f}")
    
    # Тест 3: ГЭСН с fallback на имя файла
    print("\n3. Testing GESN with filename fallback:")
    gesn_content = "ГОСУДАРСТВЕННЫЕ СМЕТНЫЕ НОРМАТИВЫ ГОСУДАРСТВЕННЫЕ СМЕТНЫЕ НОРМАТИВЫ"
    gesn_doc_type = {'doc_type': 'smeta', 'subtype': 'gesn'}
    gesn_file_path = "aeed3ad29f9e00f0_ГЭСНр-ОП-Разделы51-69 Государственные элементные сметные нормы.pdf"
    gesn_metadata = dispatcher.extract_metadata(gesn_content, gesn_doc_type, gesn_file_path)
    print(f"   Canonical ID: {gesn_metadata.canonical_id}")
    print(f"   Title: {gesn_metadata.title}")
    print(f"   Method: {gesn_metadata.extraction_method}")
    print(f"   Confidence: {gesn_metadata.confidence:.2f}")
    
    # Тест 4: Правовые документы
    print("\n4. Testing Legal documents:")
    legal_content = "Постановление Правительства РФ от 12.02.2018 N 130"
    legal_doc_type = {'doc_type': 'legal', 'subtype': 'pp'}
    legal_metadata = dispatcher.extract_metadata(legal_content, legal_doc_type)
    print(f"   Canonical ID: {legal_metadata.canonical_id}")
    print(f"   Title: {legal_metadata.title}")
    print(f"   Method: {legal_metadata.extraction_method}")
    print(f"   Confidence: {legal_metadata.confidence:.2f}")
    
    # Тест 5: Проектные документы
    print("\n5. Testing Project documents:")
    project_content = "Номер проекта: ППР-УЧАСТОК-12-2025"
    project_doc_type = {'doc_type': 'project', 'subtype': 'ppr'}
    project_metadata = dispatcher.extract_metadata(project_content, project_doc_type)
    print(f"   Canonical ID: {project_metadata.canonical_id}")
    print(f"   Title: {project_metadata.title}")
    print(f"   Method: {project_metadata.extraction_method}")
    print(f"   Confidence: {project_metadata.confidence:.2f}")
    
    # Тест 6: Книги/курсы
    print("\n6. Testing Books/Courses:")
    book_content = """
    Основы Строительной Физики
    Автор: Иванов П.С.
    Год издания: 2023
    """
    book_doc_type = {'doc_type': 'book', 'subtype': 'textbook'}
    book_metadata = dispatcher.extract_metadata(book_content, book_doc_type)
    print(f"   Canonical ID: {book_metadata.canonical_id}")
    print(f"   Title: {book_metadata.title}")
    print(f"   Authors: {book_metadata.authors}")
    print(f"   Method: {book_metadata.extraction_method}")
    print(f"   Confidence: {book_metadata.confidence:.2f}")
    
    # Тест 7: Агрессивный fallback
    print("\n7. Testing Aggressive fallback:")
    unknown_content = "Какой-то непонятный документ без четкой структуры"
    unknown_doc_type = {'doc_type': 'unknown', 'subtype': 'other'}
    unknown_metadata = dispatcher.extract_metadata(unknown_content, unknown_doc_type)
    print(f"   Canonical ID: {unknown_metadata.canonical_id}")
    print(f"   Title: {unknown_metadata.title}")
    print(f"   Method: {unknown_metadata.extraction_method}")
    print(f"   Confidence: {unknown_metadata.confidence:.2f}")
    
    print("\n" + "=" * 60)
    print("SCENARIO-BASED METADATA EXTRACTION TEST COMPLETED!")

if __name__ == "__main__":
    test_scenario_metadata()
