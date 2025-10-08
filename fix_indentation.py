#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для исправления ошибок отступов в enterprise_rag_trainer_full.py
"""

import re

def fix_indentation_errors():
    """Исправляет ошибки отступов в файле"""
    file_path = "enterprise_rag_trainer_full.py"
    
    print("Исправление ошибок отступов...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    in_try_block = False
    in_except_block = False
    
    for i, line in enumerate(lines, 1):
        original_line = line
        
        # Исправляем распространенные ошибки отступов
        if line.strip().startswith('except Exception as e:'):
            # except должен быть на том же уровне, что и try
            line = '        ' + line.lstrip()
            in_except_block = True
            in_try_block = False
            
        elif line.strip().startswith('return ') and in_except_block:
            # return в except блоке
            line = '            ' + line.lstrip()
            
        elif line.strip().startswith('logger.error') and in_except_block:
            # logger.error в except блоке
            line = '            ' + line.lstrip()
            
        elif line.strip().startswith('else:') and not line.startswith('        '):
            # else должен быть на правильном уровне
            line = '        ' + line.lstrip()
            
        elif line.strip().startswith('if ') and not line.startswith('        '):
            # if должен быть на правильном уровне
            line = '        ' + line.lstrip()
            
        elif line.strip().startswith('metadata.') and not line.startswith('                    '):
            # metadata assignments должны быть правильно отступлены
            line = '                    ' + line.lstrip()
            
        elif line.strip().startswith('logger.') and not line.startswith('                    '):
            # logger calls должны быть правильно отступлены
            line = '                    ' + line.lstrip()
        
        # Сбрасываем флаги
        if line.strip().startswith('def ') or line.strip().startswith('class '):
            in_try_block = False
            in_except_block = False
        
        fixed_lines.append(line)
    
    # Записываем исправленный файл
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print("Исправления применены!")

if __name__ == "__main__":
    fix_indentation_errors()
