#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Запуск обучения Enterprise RAG Trainer
"""

import os
import sys

# Устанавливаем переменные окружения
os.environ['BASE_DIR'] = 'I:/docs'

try:
    from enterprise_rag_trainer_full import EnterpriseRAGTrainer
    
    print('=== Запуск обучения Enterprise RAG Trainer ===')
    trainer = EnterpriseRAGTrainer(base_dir='I:/docs')
    print('✅ Trainer инициализирован успешно')
    
    # Запускаем обучение на ограниченном количестве файлов
    print('\n=== Начинаем обучение ===')
    trainer.train(max_files=5)  # Обрабатываем только 5 файлов для теста
    
    print('\n=== Обучение завершено ===')
    
    # Проверяем результат
    print('\n=== Проверка результата ===')
    result = trainer.query('СП металлоконструкции', k=3)
    print('Результат поиска:', result)
    
except Exception as e:
    print(f'❌ Ошибка: {e}')
    import traceback
    traceback.print_exc()

