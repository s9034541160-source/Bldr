#!/usr/bin/env python3
"""
Отладка конкретных регулярных выражений для строк типа "6.1"
"""
import re

def debug_specific_regex():
    """Отладка конкретных регулярных выражений"""
    test_lines = [
        "6. Общие требования",
        "6.1 Требования к материалам", 
        "6.1.1 Бетон должен соответствовать ГОСТ 26633",
        "6.1.2 Арматура должна соответствовать ГОСТ 10884",
        "6.2 Требования к конструкции",
        "6.2.1 Несущие конструкции должны быть рассчитаны на нагрузки",
        "6.2.2 Фундаменты должны обеспечивать устойчивость",
        "6.2.3 Соединения должны быть надежными",
        "7. Контроль качества",
        "7.1 Приемочный контроль",
        "7.1.1 Контроль должен проводиться в соответствии с требованиями"
    ]
    
    print("=== ОТЛАДКА КОНКРЕТНЫХ РЕГУЛЯРНЫХ ВЫРАЖЕНИЙ ===")
    
    # Тестируем разные паттерны для уровня 2
    level2_patterns = [
        r'^(\d+\.\d+)\.\s+([^\n]+)',
        r'^(\d+\.\d+)\.\s+(.+)',
        r'^(\d+\.\d+)\.\s+(.*)',
        r'^(\d+\.\d+)\.\s+([^\\n]+)',
        r'^(\d+\.\d+)\.\s+([^\\r\\n]+)',
        r'^(\d+\.\d+)\.\s+([^\\n\\r]+)',
    ]
    
    print("\n=== ТЕСТИРОВАНИЕ ПАТТЕРНОВ ДЛЯ УРОВНЯ 2 ===")
    for i, pattern in enumerate(level2_patterns):
        print(f"\nПаттерн {i+1}: {pattern}")
        for line in test_lines:
            match = re.match(pattern, line)
            if match:
                print(f"  ✓ '{line}' -> {match.group(1)} - {match.group(2)}")
    
    # Тестируем разные паттерны для уровня 3
    level3_patterns = [
        r'^(\d+\.\d+\.\d+)\.\s+([^\n]+)',
        r'^(\d+\.\d+\.\d+)\.\s+(.+)',
        r'^(\d+\.\d+\.\d+)\.\s+(.*)',
        r'^(\d+\.\d+\.\d+)\.\s+([^\\n]+)',
        r'^(\d+\.\d+\.\d+)\.\s+([^\\r\\n]+)',
        r'^(\d+\.\d+\.\d+)\.\s+([^\\n\\r]+)',
    ]
    
    print("\n=== ТЕСТИРОВАНИЕ ПАТТЕРНОВ ДЛЯ УРОВНЯ 3 ===")
    for i, pattern in enumerate(level3_patterns):
        print(f"\nПаттерн {i+1}: {pattern}")
        for line in test_lines:
            match = re.match(pattern, line)
            if match:
                print(f"  ✓ '{line}' -> {match.group(1)} - {match.group(2)}")
    
    # Тестируем с MULTILINE флагом
    print("\n=== ТЕСТИРОВАНИЕ С MULTILINE ФЛАГОМ ===")
    content = "\n".join(test_lines)
    
    level2_pattern = r'^(\d+\.\d+)\.\s+([^\n]+)'
    level3_pattern = r'^(\d+\.\d+\.\d+)\.\s+([^\n]+)'
    
    level2_matches = list(re.finditer(level2_pattern, content, re.MULTILINE))
    level3_matches = list(re.finditer(level3_pattern, content, re.MULTILINE))
    
    print(f"Уровень 2 (MULTILINE): {len(level2_matches)} совпадений")
    for match in level2_matches:
        print(f"  {match.group(1)} - {match.group(2)}")
    
    print(f"Уровень 3 (MULTILINE): {len(level3_matches)} совпадений")
    for match in level3_matches:
        print(f"  {match.group(1)} - {match.group(2)}")

if __name__ == "__main__":
    debug_specific_regex()
