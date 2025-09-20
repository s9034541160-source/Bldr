#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Тестовый скрипт для проверки всех исправлений на небольшом наборе документов
"""

import os
import glob
from pathlib import Path
from scripts.bldr_rag_trainer import BldrRAGTrainer

def test_improvements():
    """Тестируем исправления на 5 документах"""
    
    print("🧪 ТЕСТ ИСПРАВЛЕНИЙ RAG PIPELINE")
    print("=" * 50)
    
    # Инициализируем trainer
    trainer = BldrRAGTrainer()
    
    # Получаем первые 5 файлов из папки
    source_folder = "I:/docs/downloaded"
    all_files = glob.glob(os.path.join(source_folder, "*.*"))
    test_files = all_files[:5]  # Первые 5 файлов
    
    print(f"📁 Тестируем {len(test_files)} документов:")
    for i, file_path in enumerate(test_files, 1):
        print(f"  {i}. {Path(file_path).name}")
    
    print("\n🚀 НАЧИНАЕМ ОБРАБОТКУ...")
    print("=" * 50)
    
    results = {
        'processed': 0,
        'errors': 0,
        'moved_files': [],
        'quality_scores': [],
        'work_counts': []
    }
    
    def progress_callback(stage, description, progress):
        print(f"  [{stage}] {description}")
    
    # Обрабатываем каждый файл
    for i, file_path in enumerate(test_files, 1):
        file_name = Path(file_path).name
        print(f"\n🔄 [{i}/{len(test_files)}] Обрабатываем: {file_name}")
        
        try:
            success = trainer.process_document(file_path, progress_callback)
            if success:
                results['processed'] += 1
                print(f"✅ [{i}/{len(test_files)}] Завершен: {file_name}")
                
                # Проверяем, переместился ли файл
                if not os.path.exists(file_path):
                    results['moved_files'].append(file_name)
                    print(f"📁 Файл успешно перемещен в категорию!")
                
            else:
                results['errors'] += 1
                print(f"❌ [{i}/{len(test_files)}] Ошибка: {file_name}")
                
        except Exception as e:
            results['errors'] += 1
            print(f"💥 [{i}/{len(test_files)}] Исключение для {file_name}: {e}")
    
    # Итоговый отчет
    print("\n📊 ИТОГОВЫЙ ОТЧЕТ:")
    print("=" * 30)
    print(f"✅ Обработано успешно: {results['processed']}")
    print(f"❌ Ошибок: {results['errors']}")
    print(f"📁 Перемещено файлов: {len(results['moved_files'])}")
    
    if results['moved_files']:
        print("📁 Перемещенные файлы:")
        for moved_file in results['moved_files']:
            print(f"  • {moved_file}")
    
    # Проверим, что файлы действительно перемещены в категории
    base_dir = "I:/docs/БАЗА"
    if os.path.exists(base_dir):
        print(f"\n📂 Категории в {base_dir}:")
        categories = os.listdir(base_dir)
        for category in categories:
            category_path = os.path.join(base_dir, category)
            if os.path.isdir(category_path):
                files_count = len(os.listdir(category_path))
                print(f"  📁 {category}: {files_count} файлов")
    
    success_rate = (results['processed'] / len(test_files)) * 100 if test_files else 0
    
    print(f"\n🎯 УСПЕШНОСТЬ: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 ТЕСТ ПРОЙДЕН! Система работает отлично!")
    elif success_rate >= 60:
        print("⚠️ ТЕСТ ЧАСТИЧНО ПРОЙДЕН. Нужны доработки.")
    else:
        print("❌ ТЕСТ ПРОВАЛЕН. Требуется исправление.")
    
    return success_rate >= 80

if __name__ == "__main__":
    test_improvements()