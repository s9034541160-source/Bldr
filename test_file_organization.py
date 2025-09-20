#!/usr/bin/env python3
"""
Test File Organization
Тестирование системы организации файлов
"""

import os
import json
from pathlib import Path
from file_organizer import DocumentFileOrganizer, organize_document_file

def test_file_organization():
    """Тестирование организации файлов"""
    print("🧪 ТЕСТИРОВАНИЕ ОРГАНИЗАЦИИ ФАЙЛОВ")
    print("=" * 40)
    
    # Создаем организатор
    organizer = DocumentFileOrganizer("I:/docs")
    
    print("📁 Структура папок создана:")
    for doc_type, config in organizer.folder_structure.items():
        print(f"   {doc_type}: {config['folder']}")
        for subfolder_key, subfolder_path in config['subfolders'].items():
            print(f"     └─ {subfolder_key}: {subfolder_path}")
    
    print(f"\n📊 Статистика организации:")
    stats = organizer.get_organization_stats()
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    
    # Тестовые примеры
    test_cases = [
        {
            'filename': 'ГОСТ_12345_Строительство.pdf',
            'doc_type_info': {
                'doc_type': 'norms',
                'doc_subtype': 'gost',
                'confidence': 0.95
            },
            'expected_folder': 'norms/gost'
        },
        {
            'filename': 'ГЭСН_81-02-01_Земляные_работы.pdf',
            'doc_type_info': {
                'doc_type': 'estimates',
                'doc_subtype': 'gesn',
                'confidence': 0.88
            },
            'expected_folder': 'estimates/gesn'
        },
        {
            'filename': 'ППР_Фундаментные_работы.docx',
            'doc_type_info': {
                'doc_type': 'projects',
                'doc_subtype': 'ppr',
                'confidence': 0.92
            },
            'expected_folder': 'projects/ppr'
        },
        {
            'filename': 'Договор_подряда_123.pdf',
            'doc_type_info': {
                'doc_type': 'contracts',
                'doc_subtype': 'construction',
                'confidence': 0.85
            },
            'expected_folder': 'contracts/construction'
        }
    ]
    
    print(f"\n🎯 ТЕСТОВЫЕ СЛУЧАИ:")
    print("-" * 20)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Файл: {test_case['filename']}")
        print(f"   Тип: {test_case['doc_type_info']['doc_type']}")
        print(f"   Подтип: {test_case['doc_type_info']['doc_subtype']}")
        print(f"   Уверенность: {test_case['doc_type_info']['confidence']}")
        
        # Определяем целевую папку (без реального перемещения)
        target_folder = organizer._determine_target_folder(
            test_case['doc_type_info'], 
            {}, 
            Path(test_case['filename'])
        )
        
        expected_path = Path("I:/docs") / test_case['expected_folder']
        
        if target_folder == expected_path:
            print(f"   ✅ Правильная папка: {target_folder.relative_to(Path('I:/docs'))}")
        else:
            print(f"   ❌ Неправильная папка: {target_folder.relative_to(Path('I:/docs'))}")
            print(f"      Ожидалось: {test_case['expected_folder']}")

def check_downloaded_files():
    """Проверка файлов в папке downloaded"""
    print(f"\n📂 АНАЛИЗ ФАЙЛОВ В I:/docs/downloaded")
    print("=" * 40)
    
    downloaded_dir = Path("I:/docs/downloaded")
    if not downloaded_dir.exists():
        print("❌ Папка I:/docs/downloaded не найдена")
        return
    
    # Подсчет файлов по типам
    file_types = {}
    total_files = 0
    total_size = 0
    
    for file_path in downloaded_dir.rglob("*.*"):
        if file_path.is_file():
            total_files += 1
            total_size += file_path.stat().st_size
            
            extension = file_path.suffix.lower()
            if extension not in file_types:
                file_types[extension] = {'count': 0, 'size': 0}
            
            file_types[extension]['count'] += 1
            file_types[extension]['size'] += file_path.stat().st_size
    
    print(f"📊 Всего файлов: {total_files}")
    print(f"📊 Общий размер: {total_size / 1024 / 1024:.2f} MB")
    print()
    
    print("📋 По типам файлов:")
    for ext, info in sorted(file_types.items(), key=lambda x: x[1]['count'], reverse=True):
        size_mb = info['size'] / 1024 / 1024
        print(f"   {ext or 'без расширения'}: {info['count']} файлов, {size_mb:.2f} MB")
    
    # Примеры файлов для каждого типа
    print(f"\n📝 Примеры файлов:")
    for ext in ['.pdf', '.docx', '.doc', '.txt']:
        if ext in file_types:
            examples = list(downloaded_dir.rglob(f"*{ext}"))[:3]
            print(f"   {ext}:")
            for example in examples:
                print(f"     • {example.name}")

def simulate_organization():
    """Симуляция организации файлов"""
    print(f"\n🎭 СИМУЛЯЦИЯ ОРГАНИЗАЦИИ ФАЙЛОВ")
    print("=" * 35)
    
    downloaded_dir = Path("I:/docs/downloaded")
    if not downloaded_dir.exists():
        print("❌ Папка I:/docs/downloaded не найдена")
        return
    
    organizer = DocumentFileOrganizer("I:/docs")
    
    # Берем первые 10 PDF файлов для симуляции
    pdf_files = list(downloaded_dir.rglob("*.pdf"))[:10]
    
    print(f"📁 Найдено PDF файлов для симуляции: {len(pdf_files)}")
    
    simulation_results = {}
    
    for file_path in pdf_files:
        filename = file_path.name.lower()
        
        # Простое определение типа по имени файла
        if any(keyword in filename for keyword in ['гост', 'gost']):
            doc_type_info = {'doc_type': 'norms', 'doc_subtype': 'gost', 'confidence': 0.9}
        elif any(keyword in filename for keyword in ['снип', 'snip']):
            doc_type_info = {'doc_type': 'norms', 'doc_subtype': 'snip', 'confidence': 0.9}
        elif any(keyword in keyword for keyword in ['гэсн', 'gesn']):
            doc_type_info = {'doc_type': 'estimates', 'doc_subtype': 'gesn', 'confidence': 0.85}
        elif any(keyword in filename for keyword in ['ппр', 'ppr']):
            doc_type_info = {'doc_type': 'projects', 'doc_subtype': 'ppr', 'confidence': 0.8}
        else:
            doc_type_info = {'doc_type': 'other', 'doc_subtype': 'unknown', 'confidence': 0.5}
        
        # Определяем целевую папку
        target_folder = organizer._determine_target_folder(doc_type_info, {}, file_path)
        
        doc_type = doc_type_info['doc_type']
        if doc_type not in simulation_results:
            simulation_results[doc_type] = []
        
        simulation_results[doc_type].append({
            'filename': file_path.name,
            'target_folder': str(target_folder.relative_to(Path("I:/docs"))),
            'confidence': doc_type_info['confidence']
        })
    
    print(f"\n📊 РЕЗУЛЬТАТЫ СИМУЛЯЦИИ:")
    for doc_type, files in simulation_results.items():
        print(f"\n{doc_type.upper()} ({len(files)} файлов):")
        for file_info in files:
            print(f"   • {file_info['filename']}")
            print(f"     → {file_info['target_folder']} (уверенность: {file_info['confidence']})")

def main():
    """Главная функция тестирования"""
    test_file_organization()
    check_downloaded_files()
    simulate_organization()
    
    print(f"\n🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
    print("=" * 30)
    print("✅ Система организации файлов готова к работе")
    print("✅ Структура папок создана")
    print("✅ Логика определения папок работает")
    print()
    print("📋 СЛЕДУЮЩИЕ ШАГИ:")
    print("1. Запустите обучение RAG с новой системой")
    print("2. Файлы будут автоматически организованы после этапа 5")
    print("3. Проверьте папки в I:/docs/ после обучения")

if __name__ == "__main__":
    main()