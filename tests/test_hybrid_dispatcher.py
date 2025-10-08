#!/usr/bin/env python3
"""
Тест гибридного трехступенчатого диспетчера метаданных
"""
import sys
sys.path.append('.')

from enterprise_rag_trainer_full import EnterpriseRAGTrainer
from pathlib import Path

def test_hybrid_dispatcher():
    """Тестируем гибридный диспетчер с тремя стратегиями"""
    
    print("TESTING HYBRID THREE-TIERED METADATA DISPATCHER")
    print("=" * 60)
    
    # Создаем экземпляр тренера
    trainer = EnterpriseRAGTrainer()
    
    # Тест 1: НТД (СП) - Стратегия 1
    print("\n1. Testing NTD (SP) - Strategy 1 (Strict Technical):")
    ntd_content = "СП 88.13330.2014 Защитные сооружения гражданской обороны"
    ntd_structural_data = {
        'header': ntd_content,
        'sections': [],
        'tables': []
    }
    ntd_doc_type = {'doc_type': 'norms', 'subtype': 'sp'}
    
    metadata = trainer._extract_strict_technical_metadata(ntd_content, ntd_doc_type, ntd_structural_data)
    print(f"   Canonical ID: {metadata.canonical_id}")
    print(f"   Title: {metadata.title}")
    print(f"   Doc Numbers: {metadata.doc_numbers}")
    print(f"   Doc Type: {metadata.doc_type}")
    
    # Тест 2: ГЭСН - Стратегия 1
    print("\n2. Testing GESN - Strategy 1 (Strict Technical):")
    gesn_content = "ГОСУДАРСТВЕННЫЕ СМЕТНЫЕ НОРМАТИВЫ ГЭСНр-ОП-Разделы51-69"
    gesn_structural_data = {
        'header': gesn_content,
        'sections': [],
        'tables': []
    }
    gesn_doc_type = {'doc_type': 'smeta', 'subtype': 'gesn'}
    
    metadata = trainer._extract_strict_technical_metadata(gesn_content, gesn_doc_type, gesn_structural_data)
    print(f"   Canonical ID: {metadata.canonical_id}")
    print(f"   Title: {metadata.title}")
    print(f"   Doc Numbers: {metadata.doc_numbers}")
    
    # Тест 3: ГЭСН с fallback на имя файла
    print("\n3. Testing GESN with filename fallback:")
    trainer._current_file_path = "aeed3ad29f9e00f0_ГЭСНр-ОП-Разделы51-69 Государственные элементные сметные нормы.pdf"
    gesn_content_fallback = "ГОСУДАРСТВЕННЫЕ СМЕТНЫЕ НОРМАТИВЫ ГОСУДАРСТВЕННЫЕ СМЕТНЫЕ НОРМАТИВЫ"
    
    metadata = trainer._extract_strict_technical_metadata(gesn_content_fallback, gesn_doc_type, gesn_structural_data)
    print(f"   Canonical ID: {metadata.canonical_id}")
    print(f"   Title: {metadata.title}")
    print(f"   Doc Numbers: {metadata.doc_numbers}")
    
    # Тест 4: Книга - Стратегия 2
    print("\n4. Testing Book - Strategy 2 (Semantic):")
    book_content = """
    Основы Строительной Физики
    Автор: Иванов П.С.
    Год издания: 2023
    
    Введение
    Данная книга посвящена основам строительной физики...
    """
    book_structural_data = {
        'header': book_content,
        'sections': [],
        'tables': []
    }
    book_doc_type = {'doc_type': 'book', 'subtype': 'textbook'}
    
    metadata = trainer._extract_semantic_title(book_content, book_doc_type, book_structural_data)
    print(f"   Canonical ID: {metadata.canonical_id}")
    print(f"   Title: {metadata.title}")
    print(f"   Authors: {metadata.authors}")
    
    # Тест 5: Неизвестный документ - Стратегия 3
    print("\n5. Testing Unknown Document - Strategy 3 (Heuristic Fallback):")
    unknown_content = "Какой-то непонятный документ без четкой структуры"
    unknown_structural_data = {
        'header': unknown_content,
        'sections': [],
        'tables': []
    }
    unknown_doc_type = {'doc_type': 'internal', 'subtype': 'misc'}
    trainer._current_file_path = "some_random_document.pdf"
    
    metadata = trainer._extract_heuristic_fallback(unknown_content, unknown_doc_type, unknown_structural_data)
    print(f"   Canonical ID: {metadata.canonical_id}")
    print(f"   Title: {metadata.title}")
    
    # Тест 6: Полный диспетчер
    print("\n6. Testing Full Dispatcher Integration:")
    trainer._current_file_path = "test_file.pdf"
    
    # НТД через полный диспетчер
    full_metadata = trainer._stage8_metadata_extraction(ntd_content, ntd_structural_data, ntd_doc_type)
    print(f"   Full Dispatcher - NTD:")
    print(f"   Canonical ID: {full_metadata.canonical_id}")
    print(f"   Method: {full_metadata.extraction_method}")
    print(f"   Confidence: {full_metadata.confidence:.2f}")
    
    # ГЭСН через полный диспетчер
    trainer._current_file_path = "aeed3ad29f9e00f0_ГЭСНр-ОП-Разделы51-69.pdf"
    full_metadata = trainer._stage8_metadata_extraction(gesn_content, gesn_structural_data, gesn_doc_type)
    print(f"   Full Dispatcher - GESN:")
    print(f"   Canonical ID: {full_metadata.canonical_id}")
    print(f"   Method: {full_metadata.extraction_method}")
    print(f"   Confidence: {full_metadata.confidence:.2f}")
    
    print("\n" + "=" * 60)
    print("HYBRID THREE-TIERED METADATA DISPATCHER TEST COMPLETED!")

if __name__ == "__main__":
    test_hybrid_dispatcher()
