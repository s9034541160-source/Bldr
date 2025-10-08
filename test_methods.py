#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест методов RAG trainer
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_methods_exist():
    """Тест наличия методов этапов 12-14"""
    try:
        from enterprise_rag_trainer_full import EnterpriseRAGTrainer
        
        trainer = EnterpriseRAGTrainer()
        
        # Проверяем наличие методов
        methods = [
            '_stage12_save_work_sequences',
            '_stage13_smart_chunking', 
            '_stage14_save_to_qdrant'
        ]
        
        for method_name in methods:
            if hasattr(trainer, method_name):
                method = getattr(trainer, method_name)
                print(f"OK Метод {method_name} существует: {type(method)}")
            else:
                print(f"ERROR Метод {method_name} отсутствует")
                return False
                
        return True
        
    except Exception as e:
        print(f"ERROR Ошибка проверки методов: {e}")
        return False

def test_method_calls():
    """Тест вызова методов"""
    try:
        from enterprise_rag_trainer_full import EnterpriseRAGTrainer, WorkSequence, DocumentChunk
        
        trainer = EnterpriseRAGTrainer()
        
        # Тест _stage12_save_work_sequences
        work_sequences = [WorkSequence(name="test", deps=[], doc_type="sp")]
        result = trainer._stage12_save_work_sequences(work_sequences, "test.pdf", {})
        print(f"OK _stage12_save_work_sequences вызван успешно: {result}")
        
        # Тест _stage13_smart_chunking
        chunks = trainer._stage13_smart_chunking("test content", {}, {}, {'doc_type': 'sp'})
        print(f"OK _stage13_smart_chunking вызван успешно: {len(chunks)} chunks")
        
        # Тест _stage14_save_to_qdrant
        document_chunks = [DocumentChunk(content="test", metadata={})]
        result = trainer._stage14_save_to_qdrant(document_chunks, "test.pdf", "hash", {})
        print(f"OK _stage14_save_to_qdrant вызван успешно: {result}")
        
        return True
        
    except Exception as e:
        print(f"ERROR Ошибка вызова методов: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Тестирование методов RAG trainer...")
    print("=" * 50)
    
    tests = [
        test_methods_exist,
        test_method_calls
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print(f"\nЗапуск {test.__name__}...")
        if test():
            passed += 1
        print("-" * 30)
    
    print(f"\nРезультат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("Все методы работают корректно!")
    else:
        print("Некоторые методы требуют доработки")
