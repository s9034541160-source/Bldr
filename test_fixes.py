#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест исправлений RAG trainer
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_worksequence_creation():
    """Тест создания WorkSequence"""
    try:
        from enterprise_rag_trainer_full import WorkSequence
        
        # Тест с правильными параметрами
        sequence = WorkSequence(
            name="Тестовая работа",
            deps=["dep1", "dep2"],
            duration=1.5,
            priority=1,
            quality_score=0.8,
            doc_type="sp",
            section="1.1"
        )
        
        print("OK WorkSequence создается корректно")
        print(f"   name: {sequence.name}")
        print(f"   deps: {sequence.deps}")
        print(f"   doc_type: {sequence.doc_type}")
        return True
        
    except Exception as e:
        print(f"ERROR Ошибка создания WorkSequence: {e}")
        return False

def test_processed_files_loading():
    """Тест загрузки processed_files"""
    try:
        from enterprise_rag_trainer_full import EnterpriseRAGTrainer
        
        # Создаем экземпляр тренера
        trainer = EnterpriseRAGTrainer()
        
        # Тестируем загрузку processed_files
        trainer._load_processed_files()
        
        print("OK _load_processed_files работает корректно")
        print(f"   Загружено файлов: {len(trainer.processed_files)}")
        return True
        
    except Exception as e:
        print(f"ERROR Ошибка загрузки processed_files: {e}")
        return False

def test_stage_methods_exist():
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
                print(f"OK Метод {method_name} существует")
            else:
                print(f"ERROR Метод {method_name} отсутствует")
                return False
                
        return True
        
    except Exception as e:
        print(f"ERROR Ошибка проверки методов: {e}")
        return False

if __name__ == "__main__":
    print("Тестирование исправлений RAG trainer...")
    print("=" * 50)
    
    tests = [
        test_worksequence_creation,
        test_processed_files_loading,
        test_stage_methods_exist
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
        print("Все исправления работают корректно!")
    else:
        print("Некоторые исправления требуют доработки")
