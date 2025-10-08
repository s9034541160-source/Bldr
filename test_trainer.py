#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест Enterprise RAG Trainer
"""

import os
import sys

# Устанавливаем переменные окружения
os.environ['BASE_DIR'] = 'I:/docs'

try:
    from enterprise_rag_trainer_full import EnterpriseRAGTrainer
    
    print('=== Запуск Enterprise RAG Trainer ===')
    trainer = EnterpriseRAGTrainer(base_dir='I:/docs')
    print('✅ Trainer инициализирован успешно')
    
    # Проверим статус
    print(f'Base dir: {trainer.base_dir}')
    print(f'Qdrant available: {trainer.qdrant is not None}')
    print(f'Neo4j available: {trainer.neo4j is not None}')
    print(f'SBERT available: {trainer.sbert_model is not None}')
    
    # Проверим коллекции Qdrant
    if trainer.qdrant:
        try:
            collections = trainer.qdrant.get_collections()
            print(f'Qdrant collections: {[col.name for col in collections.collections]}')
        except Exception as e:
            print(f'Qdrant collections error: {e}')
    
    # Попробуем простой поиск
    print('\n=== Тест поиска ===')
    result = trainer.query('СП металлоконструкции', k=3)
    print('Результат поиска:', result)
    
except Exception as e:
    print(f'❌ Ошибка: {e}')
    import traceback
    traceback.print_exc()

