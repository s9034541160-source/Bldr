#!/usr/bin/env python3
"""
Отладка рекурсивного ГОСТ-чанкинга
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from enterprise_rag_trainer_full import EnterpriseRAGTrainer

def test_debug_chunking():
    """Отладочный тест чанкинга"""
    trainer = EnterpriseRAGTrainer()
    
    # Простой тестовый контент
    test_content = """
6. Общие требования
6.1 Требования к материалам
6.1.1 Бетон должен соответствовать ГОСТ 26633
6.1.2 Арматура должна соответствовать ГОСТ 10884
6.2 Требования к конструкции
6.2.1 Несущие конструкции должны быть рассчитаны на нагрузки
6.2.2 Фундаменты должны обеспечивать устойчивость
6.2.3 Соединения должны быть надежными
7. Контроль качества
7.1 Приемочный контроль
7.1.1 Контроль должен проводиться в соответствии с требованиями
    """.strip()
    
    metadata = {
        "title": "Тестовый ГОСТ",
        "doc_type": "gost",
        "file_path": "test_gost.pdf"
    }
    
    print("=== ОТЛАДКА РЕКУРСИВНОГО ГОСТ-ЧАНКИНГА ===")
    print(f"Тестовый контент:\n{test_content}")
    print("\n" + "="*50)
    
    # Вызываем рекурсивный чанкинг
    chunks = trainer._recursive_gost_chunking(test_content, metadata)
    
    print(f"Создано чанков: {len(chunks)}")
    
    for i, chunk in enumerate(chunks):
        print(f"\nЧанк {i+1}:")
        print(f"  ID: {chunk.chunk_id}")
        print(f"  Path: {chunk.metadata.get('path', [])}")
        print(f"  Title: {chunk.metadata.get('title', 'N/A')}")
        print(f"  Hierarchy Level: {chunk.metadata.get('hierarchy_level', 'N/A')}")
        print(f"  Content (первые 100 символов): {chunk.content[:100]}...")
    
    # Проверяем чанки с path длиной >= 2
    chunks_with_path = [chunk for chunk in chunks if len(chunk.metadata.get("path", [])) >= 2]
    print(f"\nЧанков с path длиной >= 2: {len(chunks_with_path)}")
    
    if chunks_with_path:
        print("✅ УСПЕХ: Найдены чанки с path длиной >= 2")
        for chunk in chunks_with_path:
            print(f"  - {chunk.chunk_id}: path={chunk.metadata['path']}")
    else:
        print("❌ ПРОБЛЕМА: Нет чанков с path длиной >= 2")
        print("Все чанки:")
        for chunk in chunks:
            print(f"  - {chunk.chunk_id}: path={chunk.metadata.get('path', [])}")

if __name__ == "__main__":
    test_debug_chunking()
