#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ТЕСТ УЛУЧШЕНИЙ RAG PIPELINE
============================

Тестируемые улучшения:
1. ✅ Замена Rubern на SBERT для семантического извлечения работ  
2. ✅ Улучшенная категоризация документов с контекстом
3. ✅ Оптимизированный чанкинг с учетом структуры документа  
4. ✅ Обновление базы нормативных документов

🎯 Цель: Проверить работоспособность и эффективность улучшений
"""

import sys
import os
sys.path.append('.')

from scripts.bldr_rag_trainer import BldrRAGTrainer
from enhanced_rag_improvements import apply_improvements_to_trainer
import time
import json
from pathlib import Path

def test_improvements():
    """Тест улучшений RAG pipeline"""
    
    print("🧪 ТЕСТ УЛУЧШЕНИЙ RAG PIPELINE")
    print("="*50)
    
    # Инициализируем тренер
    print("🚀 Инициализация тренера...")
    trainer = BldrRAGTrainer()
    
    # Применяем улучшения
    print("⚡ Применяем улучшения...")
    improvements_result = apply_improvements_to_trainer(trainer)
    
    print("✅ Улучшения применены:")
    for component in improvements_result['components']:
        print(f"   - {component}")
    
    # Тестовые данные
    test_content = """
    1. ОБЩИЕ ПОЛОЖЕНИЯ
    
    1.1 Выполнение работ по устройству железобетонных конструкций должно осуществляться в соответствии с проектной документацией.
    
    1.2 Монтаж металлических конструкций выполняется специализированными организациями.
    
    2. ЗЕМЛЯНЫЕ РАБОТЫ
    
    2.1 Производство земляных работ включает:
    - разработку грунта экскаватором
    - устройство песчаного основания 
    - обратную засыпку с послойным уплотнением
    
    3. БЕТОННЫЕ РАБОТЫ
    
    3.1 Бетонирование фундаментов производится бетоном класса В25.
    3.2 Технология укладки бетонной смеси должна обеспечивать равномерное заполнение опалубки.
    """
    
    test_filename = "SP_test_document.pdf"
    doc_type = "norms"
    doc_subtype = "sp"
    
    print("\n📝 Тестируем на образце документа...")
    print(f"Файл: {test_filename}")
    print(f"Тип: {doc_type}/{doc_subtype}")
    
    # Тест 1: Извлечение работ с SBERT
    print("\n🔍 Тест 1: Извлечение работ с SBERT...")
    
    # Имитируем seed works
    seed_works = ["устройство фундаментов", "монтаж конструкций"]
    
    # Создаем структурные данные
    structural_data = {
        'sections': 3,
        'tables': 0,
        'completeness': 0.8
    }
    
    # Вызываем улучшенный метод
    try:
        rubern_data = trainer._stage7_rubern_markup_enhanced(
            test_content, doc_type, doc_subtype, seed_works, structural_data
        )
        
        extracted_works = rubern_data.get('works', [])
        print(f"✅ Извлечено работ: {len(extracted_works)}")
        
        print("📋 Извлеченные работы:")
        for i, work in enumerate(extracted_works[:5], 1):
            print(f"   {i}. {work}")
        
        if len(extracted_works) > 5:
            print(f"   ... и еще {len(extracted_works) - 5} работ")
            
    except Exception as e:
        print(f"❌ Ошибка при извлечении работ: {e}")
    
    # Тест 2: Улучшенная категоризация
    print("\n🏷️ Тест 2: Улучшенная категоризация...")
    
    try:
        category, confidence = trainer.enhanced_categorization(
            test_content, test_filename, doc_type
        )
        
        print(f"✅ Категория: {category}")
        print(f"✅ Уверенность: {confidence:.2f}")
        
    except Exception as e:
        print(f"❌ Ошибка при категоризации: {e}")
    
    # Тест 3: Оптимизированный чанкинг
    print("\n📄 Тест 3: Оптимизированный чанкинг...")
    
    try:
        chunks = trainer.enhanced_chunking(
            rubern_data,
            {'materials': [], 'finances': [], 'dates': []},
            {'doc_type': doc_type, 'doc_subtype': doc_subtype}
        )
        
        print(f"✅ Создано чанков: {len(chunks)}")
        
        # Анализ чанков
        total_length = sum(chunk['length'] for chunk in chunks)
        avg_length = total_length / len(chunks) if chunks else 0
        
        print(f"📊 Статистика чанков:")
        print(f"   - Общий размер: {total_length} символов")
        print(f"   - Средний размер: {avg_length:.0f} символов")
        
        # Показываем первые 2 чанка
        print("📋 Первые чанки:")
        for i, chunk in enumerate(chunks[:2], 1):
            chunk_preview = chunk['text'][:100] + "..." if len(chunk['text']) > 100 else chunk['text']
            print(f"   Чанк {i} ({chunk['length']} символов): {chunk_preview}")
            
    except Exception as e:
        print(f"❌ Ошибка при чанкинге: {e}")
    
    # Тест 4: Обновление базы нормативных документов
    print("\n🗃️ Тест 4: База нормативных документов...")
    
    if 'db_update' in improvements_result:
        db_result = improvements_result['db_update']
        print(f"✅ Статус обновления: {db_result['status']}")
        print(f"✅ Всего документов: {db_result['total_documents']}")
        print(f"✅ Категорий: {db_result['categories']}")
        print(f"✅ Новых документов: {db_result['new_documents']}")
    else:
        print("❌ Информация об обновлении БД недоступна")
    
    # Итоговая оценка
    print("\n🎯 ИТОГОВАЯ ОЦЕНКА")
    print("="*50)
    
    improvements_score = 0
    total_tests = 4
    
    # Проверяем каждый компонент
    if 'works' in locals() and extracted_works:
        improvements_score += 1
        print("✅ Извлечение работ с SBERT: РАБОТАЕТ")
    else:
        print("❌ Извлечение работ с SBERT: ОШИБКА")
    
    if 'category' in locals() and category:
        improvements_score += 1
        print("✅ Улучшенная категоризация: РАБОТАЕТ")
    else:
        print("❌ Улучшенная категоризация: ОШИБКА")
    
    if 'chunks' in locals() and chunks:
        improvements_score += 1
        print("✅ Оптимизированный чанкинг: РАБОТАЕТ")
    else:
        print("❌ Оптимизированный чанкинг: ОШИБКА")
    
    if improvements_result.get('db_update', {}).get('status') == 'success':
        improvements_score += 1
        print("✅ Обновление базы НТД: РАБОТАЕТ")
    else:
        print("❌ Обновление базы НТД: ОШИБКА")
    
    success_rate = (improvements_score / total_tests) * 100
    
    print(f"\n📈 РЕЗУЛЬТАТ: {improvements_score}/{total_tests} ({success_rate:.0f}%)")
    
    if success_rate >= 75:
        print("🎉 УЛУЧШЕНИЯ РАБОТАЮТ ОТЛИЧНО!")
        print("💡 Можно запускать полную обработку с улучшениями")
    elif success_rate >= 50:
        print("⚠️  УЛУЧШЕНИЯ РАБОТАЮТ ЧАСТИЧНО")
        print("💡 Требуется доработка некоторых компонентов")
    else:
        print("❌ УЛУЧШЕНИЯ НЕ РАБОТАЮТ")
        print("💡 Требуется серьезная отладка")
    
    return {
        'success_rate': success_rate,
        'working_components': improvements_score,
        'total_tests': total_tests,
        'improvements_result': improvements_result
    }


if __name__ == "__main__":
    try:
        result = test_improvements()
        
        # Сохраняем результат
        with open('test_improvements_result.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n💾 Результат сохранен в test_improvements_result.json")
        
    except Exception as e:
        print(f"💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()