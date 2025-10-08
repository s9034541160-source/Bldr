#!/usr/bin/env python3
"""
Простая отладка регулярных выражений
"""
import re

def debug_simple_regex():
    """Простая отладка регулярных выражений"""
    test_strings = [
        "6.1 Требования к материалам",
        "6.1.1 Бетон должен соответствовать ГОСТ 26633",
        "6.2.1 Несущие конструкции должны быть рассчитаны на нагрузки"
    ]
    
    print("=== ПРОСТАЯ ОТЛАДКА РЕГУЛЯРНЫХ ВЫРАЖЕНИЙ ===")
    
    for test_string in test_strings:
        print(f"\nТестируем строку: '{test_string}'")
        
        # Тестируем разные паттерны
        patterns = [
            (r'^(\d+\.\d+)\.\s+(.+)', "Уровень 2"),
            (r'^(\d+\.\d+\.\d+)\.\s+(.+)', "Уровень 3"),
            (r'^(\d+\.\d+)\.\s+([^\n]+)', "Уровень 2 (без \\n)"),
            (r'^(\d+\.\d+\.\d+)\.\s+([^\n]+)', "Уровень 3 (без \\n)"),
        ]
        
        for pattern, description in patterns:
            match = re.match(pattern, test_string)
            if match:
                print(f"  ✓ {description}: {match.group(1)} - {match.group(2)}")
            else:
                print(f"  ✗ {description}: НЕ СОВПАЛ")
    
    # Тестируем с MULTILINE
    print(f"\n=== ТЕСТИРОВАНИЕ С MULTILINE ===")
    content = "\n".join(test_strings)
    print(f"Контент:\n{content}")
    
    level2_pattern = r'^(\d+\.\d+)\.\s+(.+)'
    level3_pattern = r'^(\d+\.\d+\.\d+)\.\s+(.+)'
    
    level2_matches = list(re.finditer(level2_pattern, content, re.MULTILINE))
    level3_matches = list(re.finditer(level3_pattern, content, re.MULTILINE))
    
    print(f"Уровень 2: {len(level2_matches)} совпадений")
    for match in level2_matches:
        print(f"  {match.group(1)} - {match.group(2)}")
    
    print(f"Уровень 3: {len(level3_matches)} совпадений")
    for match in level3_matches:
        print(f"  {match.group(1)} - {match.group(2)}")

if __name__ == "__main__":
    debug_simple_regex()
