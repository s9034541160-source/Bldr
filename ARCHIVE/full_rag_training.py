#!/usr/bin/env python3
"""
🚀 ПОЛНЫЙ РЕАЛЬНЫЙ ПРОЦЕСС ОБУЧЕНИЯ RAG НА ВСЕХ 1168 ДОКУМЕНТАХ
Symbiotic 15-stage pipeline with GPU acceleration and automatic sorting
"""

from scripts.bldr_rag_trainer import BldrRAGTrainer
import os
import time
import hashlib
from pathlib import Path
import json

def full_rag_training():
    print("🚀 ЗАПУСКАЕМ ФУЛЛ РЕАЛЬНЫЙ RAG ПРОЦЕСС!")
    print("=" * 80)
    print("📊 КОНФИГУРАЦИЯ:")
    print("• 🗂️  Источник: I:/docs/downloaded (1168+ файлов)")
    print("• 📁 Автосортировка в: I:/docs/БАЗА/{категория}/")
    print("• 🧠 Модель: ai-forever/sbert_large_nlu_ru (GPU)")
    print("• 🔄 Pipeline: 15 стадий (Stage 0 + Stages 1-14)")
    print("• 💾 Хранение: Neo4j + Qdrant + FAISS")
    print("=" * 80)
    print()
    
    # Создаем мощный тренер с GPU
    trainer = BldrRAGTrainer(
        base_dir='I:/docs/downloaded',     # Источник документов
        reports_dir='I:/docs/reports',     # Отчеты
        use_advanced_embeddings=True       # Максимальное качество
    )
    
    # Получаем все файлы для обработки
    source_dir = 'I:/docs/downloaded'
    all_files = []
    
    print("📦 СКАНИРОВАНИЕ ФАЙЛОВ...")
    for file in os.listdir(source_dir):
        file_path = os.path.join(source_dir, file)
        if os.path.isfile(file_path):
            all_files.append(file_path)
    
    print(f"✅ Найдено файлов: {len(all_files)}")
    
    # Проверяем уже обработанные
    processed_hashes = set(trainer.processed_files.keys())
    completed_count = sum(1 for v in trainer.processed_files.values() if v.get('status') == 'completed')
    
    print(f"🏁 Уже обработано: {completed_count} файлов")
    print(f"🎯 К обработке: {len(all_files) - completed_count} файлов")
    print()
    
    # Обратный вызов для отслеживания прогресса
    def progress_callback(stage, message, progress):
        timestamp = time.strftime('%H:%M:%S')
        print(f'  [{timestamp}] {stage} | {progress:3d}% | {message[:60]}...')

    # Главный цикл обработки
    start_time = time.time()
    processed_count = 0
    error_count = 0
    skipped_count = 0
    
    print("🔥 НАЧИНАЕМ МАССОВУЮ ОБРАБОТКУ...")
    print("=" * 80)
    
    for i, file_path in enumerate(all_files):
        filename = Path(file_path).name
        
        try:
            # Проверяем дубликат
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            
            if file_hash in processed_hashes:
                skipped_count += 1
                if i % 50 == 0:  # Каждые 50 файлов показываем прогресс
                    progress_percent = (i / len(all_files)) * 100
                    print(f"⏭️  [{i+1:4d}/{len(all_files)}] {progress_percent:5.1f}% | Пропущен дубликат: {filename[:40]}...")
                continue
            
            print(f"🔄 [{i+1:4d}/{len(all_files)}] Обрабатываем: {filename}")
            
            # Запускаем полный 15-стадийный процесс
            success = trainer.process_document(file_path, progress_callback)
            
            if success:
                processed_count += 1
                print(f"✅ [{i+1:4d}/{len(all_files)}] Завершен: {filename}")
                
                # Каждые 10 обработанных файлов показываем статистику
                if processed_count % 10 == 0:
                    elapsed = time.time() - start_time
                    speed = processed_count / (elapsed / 60) if elapsed > 0 else 0
                    remaining = (len(all_files) - i - 1) / speed if speed > 0 else 0
                    print()
                    print(f"📈 ПРОМЕЖУТОЧНАЯ СТАТИСТИКА:")
                    print(f"   ✅ Обработано: {processed_count}")
                    print(f"   ⏭️  Пропущено: {skipped_count}")
                    print(f"   ❌ Ошибок: {error_count}")
                    print(f"   ⚡ Скорость: {speed:.1f} файлов/мин")
                    print(f"   ⏱️  Осталось: {remaining:.0f} минут")
                    print()
            else:
                error_count += 1
                print(f"❌ [{i+1:4d}/{len(all_files)}] Ошибка: {filename}")
            
        except Exception as e:
            error_count += 1
            print(f"💥 [{i+1:4d}/{len(all_files)}] Критическая ошибка в {filename}: {e}")
        
        print()  # Пустая строка для читаемости

    # Финальная статистика
    total_time = time.time() - start_time
    print("=" * 80)
    print("🎊 ПОЛНОЕ RAG ОБУЧЕНИЕ ЗАВЕРШЕНО!")
    print("=" * 80)
    print(f"⏱️  Общее время: {total_time/3600:.1f} часов ({total_time/60:.1f} минут)")
    print(f"✅ Успешно обработано: {processed_count} файлов")
    print(f"⏭️  Пропущено дубликатов: {skipped_count} файлов")
    print(f"❌ Ошибок: {error_count} файлов")
    print(f"📊 Общая скорость: {processed_count/(total_time/60):.1f} файлов/мин")
    
    # Проверяем финальное состояние системы
    print()
    print("📈 ФИНАЛЬНОЕ СОСТОЯНИЕ СИСТЕМЫ:")
    
    try:
        # Qdrant статистика
        if trainer.qdrant_client:
            collection_info = trainer.qdrant_client.get_collection('universal_docs')
            point_count = getattr(collection_info, 'points_count', 'unknown')
            print(f"🗄️  Qdrant векторов: {point_count}")
        
        # Проверяем папки БАЗА
        base_folder = Path('I:/docs/БАЗА')
        if base_folder.exists():
            subfolders = [f for f in base_folder.iterdir() if f.is_dir()]
            total_sorted_files = sum(len(list(folder.rglob('*.*'))) for folder in subfolders)
            print(f"📁 Файлов в БАЗА структуре: {total_sorted_files}")
            print(f"📂 Категорий создано: {len(subfolders)}")
        
        # Обработанные файлы
        reports_file = Path('I:/docs/reports/processed_files.json')
        if reports_file.exists():
            with open(reports_file, 'r') as f:
                processed_data = json.load(f)
            completed_total = sum(1 for v in processed_data.values() if v.get('status') == 'completed')
            print(f"📋 Записей в processed_files.json: {len(processed_data)}")
            print(f"🏁 Статус 'completed': {completed_total}")
        
    except Exception as e:
        print(f"⚠️  Ошибка при проверке финального состояния: {e}")
    
    print()
    print("🎯 СИСТЕМА ПОЛНОСТЬЮ ОБУЧЕНА И ГОТОВА К РАБОТЕ!")
    print("🚀 Можно запускать поиск и анализ документов!")
    
    return trainer

if __name__ == "__main__":
    trainer = full_rag_training()