#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
СКРИПТ ДЛЯ ИСПРАВЛЕНИЯ ИМЕН УЖЕ ОБРАБОТАННЫХ ФАЙЛОВ
==================================================

Этот скрипт исправляет имена файлов в папке processed/, которые были 
неправильно переименованы из-за бага в Stage 15.

Проблема: Файлы переименовывались в устаревшие СНиП вместо актуальных СП
Решение: Используем кеш метаданных для правильного переименования
"""

import os
import json
import shutil
import re
from pathlib import Path
from typing import Dict, List, Optional

def load_processed_files_cache() -> Dict:
    """Загружаем кеш обработанных файлов"""
    cache_path = Path("I:/docs/downloaded/processed_files.json")
    if cache_path.exists():
        with open(cache_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def extract_correct_document_name(metadata: Dict) -> str:
    """Извлекаем правильное название документа с ПРАВИЛЬНОЙ логикой приоритетов"""
    
    # Получаем номера документов из метаданных
    doc_numbers = metadata.get('doc_numbers', [])
    if not doc_numbers:
        return "Документ"
    
    # Создаем список с приоритетами для сортировки
    prioritized_docs = []
    
    for doc in doc_numbers:
        priority = 0
        
        # Приоритет 1 (Высший): СП с полным годом (например, СП 541.1325800.2024)
        if doc.startswith('СП ') and ('.20' in doc or '.19' in doc):
            priority = 1000 + len(doc)  # Длина для сортировки по полноте
        
        # Приоритет 2: СП с полным номером без года (например, СП 88.13330)
        elif doc.startswith('СП ') and '.' in doc and '.20' not in doc and '.19' not in doc:
            priority = 800 + len(doc)
        
        # Приоритет 3: СП короткий (например, СП 88)
        elif doc.startswith('СП ') and '.' not in doc:
            priority = 600 + len(doc)
        
        # Приоритет 4: СНиП с полным годом (например, СНиП 23-03-2003)
        elif doc.startswith('СНиП ') and ('.20' in doc or '.19' in doc or '-' in doc):
            priority = 400 + len(doc)
        
        # Приоритет 5: СНиП короткий (например, СНиП 2)
        elif doc.startswith('СНиП ') and '.' not in doc and '-' not in doc:
            priority = 200 + len(doc)
        
        # Приоритет 6: Любой другой документ
        else:
            priority = 100 + len(doc)
        
        prioritized_docs.append((priority, doc))
    
    # Сортируем по убыванию приоритета
    prioritized_docs.sort(key=lambda x: x[0], reverse=True)
    
    if prioritized_docs:
        return prioritized_docs[0][1]
    
    return "Документ"

def create_safe_filename(title: str) -> str:
    """Создаем безопасное имя файла"""
    if not title or title == 'Документ':
        return 'Документ'
    
    # Очищаем от недопустимых символов
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
    safe_title = re.sub(r'\s+', '_', safe_title)
    safe_title = re.sub(r'_+', '_', safe_title)
    
    # Ограничиваем длину
    if len(safe_title) > 80:
        safe_title = safe_title[:80]
        last_underscore = safe_title.rfind('_')
        if last_underscore > 50:
            safe_title = safe_title[:last_underscore]
    
    safe_title = safe_title.strip('_')
    return safe_title if safe_title else "Документ"

def is_incorrectly_named_file(filename: str) -> bool:
    """Проверяем, является ли файл неправильно переименованным"""
    
    # Ищем файлы с устаревшими СНиП
    if re.search(r'СНиП_\d+\.\d+\.\d+', filename):
        return True
    
    # Ищем файлы с неправильными СП (например, СП_60 вместо СП_490)
    if re.search(r'СП_\d+\.\d+\.\d+', filename):
        # Проверяем, не является ли это известным неправильным СП
        wrong_sps = ['СП_60', 'СП_71', 'СП_158']  # Добавьте известные неправильные
        for wrong_sp in wrong_sps:
            if wrong_sp in filename:
                return True
    
    return False

def fix_processed_filenames():
    """Основная функция исправления имен файлов"""
    
    print("🔧 ЗАПУСК ИСПРАВЛЕНИЯ ИМЕН ОБРАБОТАННЫХ ФАЙЛОВ")
    print("=" * 60)
    
    # Загружаем кеш обработанных файлов
    processed_cache = load_processed_files_cache()
    print(f"📁 Загружен кеш: {len(processed_cache)} файлов")
    
    # Папка с обработанными файлами
    processed_dir = Path("I:/docs/processed/norms")
    if not processed_dir.exists():
        print(f"❌ Папка {processed_dir} не найдена!")
        return
    
    # Счетчики
    fixed_count = 0
    skipped_count = 0
    error_count = 0
    
    print(f"🔍 Сканируем папку: {processed_dir}")
    
    # Проходим по всем файлам в папке processed
    for file_path in processed_dir.glob("*.pdf"):
        filename = file_path.name
        
        # Проверяем, нужно ли исправлять имя файла
        if not is_incorrectly_named_file(filename):
            skipped_count += 1
            continue
        
        print(f"\n🔧 Исправляем: {filename}")
        
        # Ищем файл в кеше по оригинальному пути
        original_path = None
        file_metadata = None
        
        for cache_path, cache_data in processed_cache.items():
            if cache_data.get('original_path') == str(file_path):
                original_path = cache_path
                file_metadata = cache_data
                break
        
        if not file_metadata:
            print(f"   ⚠️ Метаданные не найдены для {filename}")
            error_count += 1
            continue
        
        # Извлекаем правильное название документа
        correct_name = extract_correct_document_name(file_metadata)
        print(f"   📋 Правильное название: {correct_name}")
        
        # Создаем новое имя файла
        safe_name = create_safe_filename(correct_name)
        new_filename = f"{safe_name}.pdf"
        new_path = file_path.parent / new_filename
        
        # Проверяем, не существует ли уже файл с таким именем
        if new_path.exists() and new_path != file_path:
            print(f"   ⚠️ Файл {new_filename} уже существует, пропускаем")
            error_count += 1
            continue
        
        try:
            # Переименовываем файл
            shutil.move(str(file_path), str(new_path))
            print(f"   ✅ Переименован: {filename} -> {new_filename}")
            fixed_count += 1
            
        except Exception as e:
            print(f"   ❌ Ошибка переименования: {e}")
            error_count += 1
    
    # Итоговая статистика
    print("\n" + "=" * 60)
    print("📊 ИТОГОВАЯ СТАТИСТИКА:")
    print(f"   ✅ Исправлено файлов: {fixed_count}")
    print(f"   ⏭️ Пропущено файлов: {skipped_count}")
    print(f"   ❌ Ошибок: {error_count}")
    print("=" * 60)

if __name__ == "__main__":
    fix_processed_filenames()

