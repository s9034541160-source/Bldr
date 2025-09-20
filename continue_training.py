#!/usr/bin/env python3
"""
Скрипт для продолжения RAG обучения после исправления ошибки uuid
"""

from scripts.bldr_rag_trainer import BldrRAGTrainer
import os
import time
import hashlib
from pathlib import Path

def continue_rag_training():
    print('🚀 ПРОДОЛЖАЕМ RAG ОБУЧЕНИЕ С ИСПРАВЛЕННОЙ ОШИБКОЙ UUID!')
    print('=' * 60)

    # Создаем тренер
    trainer = BldrRAGTrainer(
        base_dir='I:/docs/downloaded',
        reports_dir='I:/docs/reports'
    )

    # Получаем список всех файлов для обработки
    source_dir = 'I:/docs/downloaded'
    all_files = []
    for file in os.listdir(source_dir):
        file_path = os.path.join(source_dir, file)
        if os.path.isfile(file_path):
            all_files.append(file_path)

    print(f'📦 Всего файлов для обработки: {len(all_files)}')

    # Определяем уже обработанные файлы
    processed_hashes = set(trainer.processed_files.keys())
    print(f'✅ Уже обработано: {len(processed_hashes)} файлов')

    # Обрабатываем файлы партиями
    processed_count = 0
    start_time = time.time()

    def progress_callback(stage, message, progress):
        timestamp = time.strftime('%H:%M:%S')
        print(f'  [{timestamp}] {stage} | {progress:3d}% | {message}')

    print('📋 Начинаем обработку по одному файлу...')
    print()

    # Обработаем первые 20 файлов для теста
    files_to_process = all_files[:20]
    
    for i, file_path in enumerate(files_to_process):
        filename = Path(file_path).name
        
        # Проверяем, не обработан ли уже файл
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
                file_hash = hashlib.sha256(file_content).hexdigest()
            
            if file_hash in processed_hashes:
                print(f'⏭️  [{i+1}/{len(files_to_process)}] Пропускаем (уже обработан): {filename}')
                continue
                
            print(f'🔄 [{i+1}/{len(files_to_process)}] Обрабатываем: {filename}')
            
            success = trainer.process_document(file_path, progress_callback)
            
            if success:
                processed_count += 1
                print(f'✅ [{i+1}/{len(files_to_process)}] Завершен: {filename}')
            else:
                print(f'❌ [{i+1}/{len(files_to_process)}] Ошибка: {filename}')
                
        except Exception as e:
            print(f'❌ [{i+1}/{len(files_to_process)}] Критическая ошибка при обработке {filename}: {e}')
        
        print()

    elapsed_time = time.time() - start_time
    print('=' * 60)
    print(f'📊 РЕЗУЛЬТАТЫ ПАКЕТНОЙ ОБРАБОТКИ:')
    print(f'⏱️  Время выполнения: {elapsed_time/60:.1f} минут')
    print(f'✅ Обработано успешно: {processed_count} файлов')
    if elapsed_time > 0:
        print(f'📈 Скорость: {processed_count/(elapsed_time/60):.1f} файлов/мин')
    print()
    
    # Проверяем статус Qdrant после обработки
    try:
        if trainer.qdrant_client:
            collection_info = trainer.qdrant_client.get_collection('universal_docs')
            point_count = getattr(collection_info, 'points_count', 'unknown')
            print(f'🗄️  Qdrant коллекция теперь содержит: {point_count} векторов')
    except Exception as e:
        print(f'⚠️  Ошибка проверки Qdrant: {e}')
    
    print('🎯 Обучение продолжается успешно!')

if __name__ == "__main__":
    continue_rag_training()