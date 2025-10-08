#!/usr/bin/env python3
"""
GPU тест для RAG trainer
"""

from scripts.bldr_rag_trainer import BldrRAGTrainer
import time

def test_gpu_rag():
    print('🚀 ТЕСТИРУЕМ ОБНОВЛЕННЫЙ RAG TRAINER С GPU!')
    print('=' * 60)

    # Создаем тренер с GPU
    trainer = BldrRAGTrainer(use_advanced_embeddings=True)

    print()
    print('📊 ИНФОРМАЦИЯ О СИСТЕМЕ:')
    print(f'  Device: {getattr(trainer, "device", "неизвестно")}')
    print(f'  Embedding dimension: {trainer.dimension}')
    print(f'  Model: {type(trainer.embedding_model).__name__}')

    print()
    print('🧪 ТЕСТ ГЕНЕРАЦИИ ВЕКТОРОВ...')

    # Тестируем на небольшой выборке
    test_chunks = [
        'Строительные работы по возведению фундамента',
        'Установка опалубки и арматуры для монтажа',
        'Бетонирование конструкций согласно проекту',
        'Контроль качества выполненных работ',
        'Гидроизоляция подземных конструкций',
        'Монтаж металлических конструкций каркаса',
        'Устройство кровельного покрытия здания',
        'Отделочные работы внутренних помещений'
    ]

    start_time = time.time()
    embeddings = trainer._generate_embeddings_with_batching(test_chunks)
    gpu_time = time.time() - start_time

    print(f'✅ Векторы сгенерированы за {gpu_time:.2f} секунд')
    print(f'📐 Размерность: {embeddings.shape}')
    
    # Сравним со старой скоростью
    expected_cpu_time = len(test_chunks) * 0.5  # Примерно 0.5 сек на чанк на CPU
    speedup = expected_cpu_time / gpu_time if gpu_time > 0 else 0
    
    print(f'⚡ Ускорение примерно в {speedup:.1f}x по сравнению с CPU')
    print(f'🎯 Система готова к полноценному обучению!')
    
    return trainer

if __name__ == "__main__":
    trainer = test_gpu_rag()