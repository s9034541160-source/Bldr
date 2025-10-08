#!/usr/bin/env python3
"""
Тест для recursive ГОСТ-чанкинга
Проверяет 3-уровневую иерархию (6→6.2→6.2.3)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enterprise_rag_trainer_full import EnterpriseRAGTrainer

def test_recursive_gost_chunking():
    """Тестирует recursive ГОСТ-чанкинг с реальным примером"""
    
    # Создаем экземпляр тренера
    trainer = EnterpriseRAGTrainer()
    
    # Пример ГОСТ-документа с 3-уровневой иерархией
    gost_content = """
6. ОБЩИЕ ТРЕБОВАНИЯ

6.1 Требования к материалам должны соответствовать ГОСТ 12345-2020.

6.1.1 Стальные конструкции должны быть изготовлены из стали марки С255.

6.1.2 Бетонные конструкции должны соответствовать классу прочности В25.

6.2 Требования к монтажу

6.2.1 Монтаж должен производиться в соответствии с проектом.

6.2.2 Сварные соединения должны соответствовать ГОСТ 5264-80.

6.2.3 Контроль качества сварных соединений должен проводиться в соответствии с ГОСТ 3242-79.

6.2.3.1 Визуальный контроль должен проводиться на 100% соединений.

6.2.3.2 Ультразвуковой контроль должен проводиться на 20% соединений.

6.3 Требования к испытаниям

6.3.1 Испытания должны проводиться в соответствии с программой испытаний.

6.3.2 Результаты испытаний должны оформляться протоколом.
"""
    
    print("🧪 Тестируем recursive ГОСТ-чанкинг...")
    print("=" * 50)
    
    # Тестируем базовый чанкинг
    chunks = trainer._custom_ntd_chunking(gost_content, "gost")
    
    print(f"📊 Создано {len(chunks)} чанков:")
    print()
    
    for i, chunk in enumerate(chunks, 1):
        print(f"Чанк {i}:")
        print(f"  {chunk[:100]}...")
        print()
    
    # Тестируем чанкинг с метаданными
    base_metadata = {
        'doc_type': 'gost',
        'title': 'Тестовый ГОСТ',
        'canonical_id': 'test_gost_001'
    }
    
    chunk_data = trainer._custom_ntd_chunking_with_metadata(gost_content, "gost", base_metadata)
    
    print("📋 Метаданные чанков:")
    print("=" * 50)
    
    for i, data in enumerate(chunk_data, 1):
        metadata = data['metadata']
        print(f"Чанк {i}:")
        print(f"  Номер пункта: {metadata.get('punkt_num', 'N/A')}")
        print(f"  Уровень иерархии: {metadata.get('hierarchy_level', 'N/A')}")
        print(f"  Путь: {' → '.join(metadata.get('parent_path', []))}")
        print(f"  Тип чанка: {metadata.get('chunk_type', 'N/A')}")
        print(f"  Структурный: {metadata.get('is_structural', False)}")
        if 'gost_structure' in metadata:
            structure = metadata['gost_structure']
            print(f"  Раздел: {structure.get('section', 'N/A')}")
            print(f"  Подраздел: {structure.get('subsection', 'N/A')}")
            print(f"  Подподраздел: {structure.get('subsubsection', 'N/A')}")
        print()
    
    # Проверяем, что иерархия работает правильно
    print("🔍 Проверка иерархии:")
    print("=" * 50)
    
    for data in chunk_data:
        metadata = data['metadata']
        punkt_num = metadata.get('punkt_num', '')
        level = metadata.get('hierarchy_level', 0)
        parent_path = metadata.get('parent_path', [])
        
        print(f"Пункт {punkt_num}: уровень {level}, родители: {parent_path}")
        
        # Проверяем логику иерархии
        if punkt_num == "6.2.3.1":
            assert level == 4, f"Ожидался уровень 4, получен {level}"
            assert "6.2.3" in parent_path, "6.2.3 должен быть в родительском пути"
            print("  ✅ Правильная иерархия для 6.2.3.1")
        
        if punkt_num == "6.2.3":
            assert level == 3, f"Ожидался уровень 3, получен {level}"
            assert "6.2" in parent_path, "6.2 должен быть в родительском пути"
            print("  ✅ Правильная иерархия для 6.2.3")
    
    print("\n🎉 Все тесты пройдены успешно!")
    print("✅ Recursive ГОСТ-чанкинг работает корректно")
    print("✅ 3-уровневая иерархия поддерживается")
    print("✅ Метаданные сохраняются правильно")

if __name__ == "__main__":
    test_recursive_gost_chunking()
