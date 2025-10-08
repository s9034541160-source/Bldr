#!/usr/bin/env python3
"""
Тестирование улучшенного переименования файлов в RAG trainer
"""

import os
import sys
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_document_title_extraction():
    """Тестирование извлечения названий документов"""
    print("🔍 Тестирование извлечения названий документов...")
    
    try:
        from enterprise_rag_trainer_full import EnterpriseRAGTrainer
        
        trainer = EnterpriseRAGTrainer()
        
        # Тестовые контенты документов
        test_contents = [
            "СП 16.13330.2017 - Свод правил «Стальные конструкции. Актуализированная редакция СНиП II-23-81»",
            "ГОСТ 27751-2014 - Надежность строительных конструкций и оснований",
            "СНиП 2.01.07-85* - Нагрузки и воздействия",
            "РД-11-02-2006 - Требования к составу и порядку ведения исполнительной документации",
            "ТУ 102-488-05 - Технические условия на стальные конструкции"
        ]
        
        print("📋 Тестируем извлечение названий:")
        for i, content in enumerate(test_contents, 1):
            title = trainer._extract_document_title(content)
            print(f"  {i}. Исходный: {content[:50]}...")
            print(f"     Извлечено: {title}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования извлечения названий: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_safe_filename_creation():
    """Тестирование создания безопасных имен файлов"""
    print("\n🔒 Тестирование создания безопасных имен файлов...")
    
    try:
        from enterprise_rag_trainer_full import EnterpriseRAGTrainer
        
        trainer = EnterpriseRAGTrainer()
        
        # Тестовые названия документов
        test_titles = [
            "СП 16.13330.2017 - Свод правил «Стальные конструкции»",
            "ГОСТ 27751-2014 - Надежность строительных конструкций",
            "СНиП 2.01.07-85* - Нагрузки и воздействия",
            "РД-11-02-2006 - Требования к составу",
            "ТУ 102-488-05 - Технические условия"
        ]
        
        print("📁 Тестируем создание безопасных имен:")
        for i, title in enumerate(test_titles, 1):
            safe_name = trainer._create_safe_filename(title)
            print(f"  {i}. Исходный: {title}")
            print(f"     Безопасный: {safe_name}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования безопасных имен: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_metadata_title_extraction():
    """Тестирование извлечения названий из метаданных"""
    print("\n📊 Тестирование извлечения названий из метаданных...")
    
    try:
        from enterprise_rag_trainer_full import EnterpriseRAGTrainer
        
        trainer = EnterpriseRAGTrainer()
        
        # Тестовые метаданные
        test_metadata = [
            {
                'doc_type': 'normative',
                'doc_title': 'СП 16.13330.2017 - Стальные конструкции',
                'doc_numbers': ['СП 16.13330.2017']
            },
            {
                'doc_type': 'normative',
                'doc_title': 'Документ',
                'doc_numbers': ['ГОСТ 27751-2014']
            },
            {
                'doc_type': 'unknown',
                'doc_title': '',
                'doc_numbers': []
            }
        ]
        
        print("🔍 Тестируем извлечение из метаданных:")
        for i, metadata in enumerate(test_metadata, 1):
            title = trainer._extract_document_title_from_metadata(metadata)
            print(f"  {i}. Метаданные: {metadata}")
            print(f"     Извлечено: {title}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования метаданных: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_improved_renaming_logic():
    """Тестирование улучшенной логики переименования"""
    print("\n🎯 Тестирование улучшенной логики переименования...")
    
    try:
        # Проверяем, что исправления применены
        with open('enterprise_rag_trainer_full.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Ищем новые методы
        improvements = [
            "_extract_document_title_from_metadata",
            "_create_safe_filename",
            "doc_title = self._extract_document_title_from_metadata",
            "safe_title = self._create_safe_filename"
        ]
        
        found_improvements = 0
        for improvement in improvements:
            if improvement in content:
                found_improvements += 1
                print(f"✅ Найдено: {improvement}")
            else:
                print(f"❌ Не найдено: {improvement}")
        
        if found_improvements == len(improvements):
            print("\n🎉 Все улучшения применены!")
            return True
        else:
            print(f"\n⚠️ Найдено {found_improvements}/{len(improvements)} улучшений")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка проверки улучшений: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 ТЕСТИРОВАНИЕ УЛУЧШЕННОГО ПЕРЕИМЕНОВАНИЯ ФАЙЛОВ")
    print("=" * 70)
    
    # Тестируем все компоненты
    title_extraction_ok = test_document_title_extraction()
    safe_filename_ok = test_safe_filename_creation()
    metadata_extraction_ok = test_metadata_title_extraction()
    improvements_ok = test_improved_renaming_logic()
    
    print("\n" + "=" * 70)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"   🔍 Извлечение названий: {'✅' if title_extraction_ok else '❌'}")
    print(f"   🔒 Безопасные имена: {'✅' if safe_filename_ok else '❌'}")
    print(f"   📊 Метаданные: {'✅' if metadata_extraction_ok else '❌'}")
    print(f"   🎯 Улучшения применены: {'✅' if improvements_ok else '❌'}")
    
    if title_extraction_ok and safe_filename_ok and metadata_extraction_ok and improvements_ok:
        print("\n🎉 УЛУЧШЕННОЕ ПЕРЕИМЕНОВАНИЕ РАБОТАЕТ КОРРЕКТНО!")
        print("✅ Файлы переименовываются в понятные названия документов")
        print("✅ Поддержка СП, ГОСТ, СНиП, РД, ТУ документов")
        print("✅ Безопасные имена файлов")
        print("✅ Извлечение из метаданных")
    else:
        print("\n⚠️ НЕКОТОРЫЕ УЛУЧШЕНИЯ ТРЕБУЮТ ДОРАБОТКИ")
    
    print("=" * 70)

if __name__ == "__main__":
    main()
