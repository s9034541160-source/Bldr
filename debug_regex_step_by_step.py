#!/usr/bin/env python3
"""
Пошаговая отладка регулярных выражений
"""
import re

def debug_regex_step_by_step():
    """Пошаговая отладка регулярных выражений"""
    test_string = "6.1 Требования к материалам"
    
    print(f"=== ПОШАГОВАЯ ОТЛАДКА РЕГУЛЯРНЫХ ВЫРАЖЕНИЙ ===")
    print(f"Тестовая строка: '{test_string}'")
    
    # Тестируем простые паттерны
    simple_patterns = [
        r'^(\d+)',
        r'^(\d+\.)',
        r'^(\d+\.\d+)',
        r'^(\d+\.\d+\.)',
        r'^(\d+\.\d+\.\d+)',
    ]
    
    print(f"\n=== ПРОСТЫЕ ПАТТЕРНЫ ===")
    for i, pattern in enumerate(simple_patterns):
        match = re.match(pattern, test_string)
        if match:
            print(f"  {i+1}. {pattern} -> {match.group(1)}")
        else:
            print(f"  {i+1}. {pattern} -> НЕ СОВПАЛ")
    
    # Тестируем паттерны с пробелами
    space_patterns = [
        r'^(\d+\.\d+)\s',
        r'^(\d+\.\d+)\s+',
        r'^(\d+\.\d+)\.\s',
        r'^(\d+\.\d+)\.\s+',
    ]
    
    print(f"\n=== ПАТТЕРНЫ С ПРОБЕЛАМИ ===")
    for i, pattern in enumerate(space_patterns):
        match = re.match(pattern, test_string)
        if match:
            print(f"  {i+1}. {pattern} -> {match.group(1)}")
        else:
            print(f"  {i+1}. {pattern} -> НЕ СОВПАЛ")
    
    # Тестируем полные паттерны
    full_patterns = [
        r'^(\d+\.\d+)\.\s+(.+)',
        r'^(\d+\.\d+)\.\s+([^\n]+)',
        r'^(\d+\.\d+)\.\s+([^\\n]+)',
        r'^(\d+\.\d+)\.\s+([^\\r\\n]+)',
    ]
    
    print(f"\n=== ПОЛНЫЕ ПАТТЕРНЫ ===")
    for i, pattern in enumerate(full_patterns):
        match = re.match(pattern, test_string)
        if match:
            print(f"  {i+1}. {pattern} -> {match.group(1)} - {match.group(2)}")
        else:
            print(f"  {i+1}. {pattern} -> НЕ СОВПАЛ")
    
    # Тестируем с разными флагами
    print(f"\n=== ТЕСТИРОВАНИЕ С ФЛАГАМИ ===")
    pattern = r'^(\d+\.\d+)\.\s+(.+)'
    
    flags = [
        (re.MULTILINE, "MULTILINE"),
        (re.DOTALL, "DOTALL"),
        (re.MULTILINE | re.DOTALL, "MULTILINE | DOTALL"),
    ]
    
    for flag, name in flags:
        match = re.match(pattern, test_string, flag)
        if match:
            print(f"  {name}: {match.group(1)} - {match.group(2)}")
        else:
            print(f"  {name}: НЕ СОВПАЛ")

if __name__ == "__main__":
    debug_regex_step_by_step()
