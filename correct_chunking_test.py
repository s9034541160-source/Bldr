#!/usr/bin/env python3
"""
Правильный тест рекурсивного ГОСТ-чанкинга с исправленными паттернами
"""
import re
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class DocumentChunk:
    """Чанк документа"""
    content: str
    chunk_id: str
    metadata: Dict[str, Any]
    section_id: str = ""
    chunk_type: str = "content"

def recursive_gost_chunking(content: str, metadata: Dict) -> List[DocumentChunk]:
    """Recursive ГОСТ-чанкинг с 3-уровневой иерархией (6→6.2→6.2.3) и сохранением метаданных иерархии."""
    chunks = []
    
    try:
        # ИСПРАВЛЕННЫЕ паттерны для разных уровней
        # Убираем лишние точки из паттернов
        level1_pattern = r'^(\d+)\.\s+([^\n]+)'
        level2_pattern = r'^(\d+\.\d+)\s+([^\n]+)'
        level3_pattern = r'^(\d+\.\d+\.\d+)\s+([^\n]+)'
        
        # Извлекаем разделы всех уровней
        level1_matches = list(re.finditer(level1_pattern, content, re.MULTILINE))
        level2_matches = list(re.finditer(level2_pattern, content, re.MULTILINE))
        level3_matches = list(re.finditer(level3_pattern, content, re.MULTILINE))
        
        print(f"Найдено совпадений:")
        print(f"  Уровень 1: {len(level1_matches)}")
        print(f"  Уровень 2: {len(level2_matches)}")
        print(f"  Уровень 3: {len(level3_matches)}")
        
        # Показываем найденные совпадения
        for i, match in enumerate(level1_matches):
            print(f"  L1[{i}]: {match.group(1)} - {match.group(2)}")
        for i, match in enumerate(level2_matches):
            print(f"  L2[{i}]: {match.group(1)} - {match.group(2)}")
        for i, match in enumerate(level3_matches):
            print(f"  L3[{i}]: {match.group(1)} - {match.group(2)}")
        
        # Создаем чанки для разделов 1 уровня
        for i, match in enumerate(level1_matches):
            section_number = match.group(1)
            section_title = match.group(2).strip()
            
            # Определяем конец текущего раздела
            section_end = match.end()
            if i + 1 < len(level1_matches):
                section_end = level1_matches[i + 1].start()
            else:
                section_end = len(content)
            
            section_text = content[match.start():section_end].strip()
            
            if len(section_text) > 50:  # Минимальный размер чанка
                chunk = DocumentChunk(
                    content=section_text,
                    chunk_id=f"gost_section_{section_number}",
                    metadata={
                        **metadata,
                        "path": [section_number],
                        "title": section_title,
                        "hierarchy_level": 1
                    },
                    section_id=section_number,
                    chunk_type="gost_section"
                )
                chunks.append(chunk)
                print(f"[RECURSIVE_GOST] Создан чанк раздела 1 уровня: {section_number}")
        
        # Создаем чанки для разделов 2 уровня
        for i, match in enumerate(level2_matches):
            section_number = match.group(1)
            section_title = match.group(2).strip()
            
            # Разбираем путь
            path_parts = section_number.split('.')
            level1_part = path_parts[0] if len(path_parts) > 0 else ""
            level2_part = section_number
            
            # Определяем конец текущего раздела
            section_end = match.end()
            # Ищем следующий раздел того же или более высокого уровня
            next_section_found = False
            for j in range(i + 1, len(level2_matches)):
                if level2_matches[j].group(1).startswith(level1_part + "."):
                    section_end = level2_matches[j].start()
                    next_section_found = True
                    break
            
            if not next_section_found:
                # Ищем следующий раздел 1 уровня
                level1_part_num = int(level1_part)
                for j, l1_match in enumerate(level1_matches):
                    l1_num = int(l1_match.group(1))
                    if l1_num > level1_part_num:
                        section_end = l1_match.start()
                        next_section_found = True
                        break
            
            if not next_section_found:
                section_end = len(content)
            
            section_text = content[match.start():section_end].strip()
            
            if len(section_text) > 50:  # Минимальный размер чанка
                chunk = DocumentChunk(
                    content=section_text,
                    chunk_id=f"gost_section_{section_number}",
                    metadata={
                        **metadata,
                        "path": [level1_part, level2_part],
                        "title": section_title,
                        "hierarchy_level": 2
                    },
                    section_id=section_number,
                    chunk_type="gost_section"
                )
                chunks.append(chunk)
                print(f"[RECURSIVE_GOST] Создан чанк раздела 2 уровня: {section_number}")
        
        # Создаем чанки для разделов 3 уровня
        for i, match in enumerate(level3_matches):
            section_number = match.group(1)
            section_title = match.group(2).strip()
            
            # Разбираем путь
            path_parts = section_number.split('.')
            level1_part = path_parts[0] if len(path_parts) > 0 else ""
            level2_part = f"{path_parts[0]}.{path_parts[1]}" if len(path_parts) > 1 else ""
            level3_part = section_number
            
            # Определяем конец текущего раздела
            section_end = match.end()
            # Ищем следующий раздел того же уровня
            next_section_found = False
            for j in range(i + 1, len(level3_matches)):
                if level3_matches[j].group(1).startswith(f"{level1_part}.{level2_part}."):
                    section_end = level3_matches[j].start()
                    next_section_found = True
                    break
            
            if not next_section_found:
                # Ищем следующий раздел 2 уровня в той же секции 1 уровня
                for j, l2_match in enumerate(level2_matches):
                    l2_num = l2_match.group(1)
                    if l2_num.startswith(f"{level1_part}.") and l2_num > level2_part:
                        section_end = l2_match.start()
                        next_section_found = True
                        break
            
            if not next_section_found:
                # Ищем следующий раздел 1 уровня
                level1_part_num = int(level1_part)
                for j, l1_match in enumerate(level1_matches):
                    l1_num = int(l1_match.group(1))
                    if l1_num > level1_part_num:
                        section_end = l1_match.start()
                        next_section_found = True
                        break
            
            if not next_section_found:
                section_end = len(content)
            
            section_text = content[match.start():section_end].strip()
            
            if len(section_text) > 50:  # Минимальный размер чанка
                chunk = DocumentChunk(
                    content=section_text,
                    chunk_id=f"gost_section_{section_number}",
                    metadata={
                        **metadata,
                        "path": [level1_part, level2_part, level3_part],
                        "title": section_title,
                        "hierarchy_level": 3
                    },
                    section_id=section_number,
                    chunk_type="gost_section"
                )
                chunks.append(chunk)
                print(f"[RECURSIVE_GOST] Создан чанк раздела 3 уровня: {section_number}")
        
        print(f"[RECURSIVE_GOST] Создано {len(chunks)} чанков с иерархией")
        return chunks
        
    except Exception as e:
        print(f"[RECURSIVE_GOST] Ошибка рекурсивного чанкинга: {e}")
        return []

def test_correct_chunking():
    """Правильный тест чанкинга"""
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
    
    print("=== ПРАВИЛЬНЫЙ ТЕСТ РЕКУРСИВНОГО ГОСТ-ЧАНКИНГА ===")
    print(f"Тестовый контент:\n{test_content}")
    print("\n" + "="*50)
    
    # Вызываем рекурсивный чанкинг
    chunks = recursive_gost_chunking(test_content, metadata)
    
    print(f"\nСоздано чанков: {len(chunks)}")
    
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
    test_correct_chunking()
