#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Прямой тест Qdrant без SBERT
"""

from qdrant_client import QdrantClient
from qdrant_client.http import models

try:
    # Подключаемся к Qdrant
    client = QdrantClient(host="localhost", port=6333)
    
    print('=== Тест Qdrant ===')
    
    # Получаем коллекции
    collections = client.get_collections()
    print(f'Коллекции: {[col.name for col in collections.collections]}')
    
    # Проверяем коллекцию enterprise_docs
    if 'enterprise_docs' in [col.name for col in collections.collections]:
        print('\n=== Проверка коллекции enterprise_docs ===')
        
        # Получаем информацию о коллекции
        collection_info = client.get_collection('enterprise_docs')
        print(f'Количество точек: {collection_info.points_count}')
        
        if collection_info.points_count > 0:
            print('\n=== Поиск без эмбеддингов ===')
            
            # Попробуем простой поиск по тексту
            try:
                # Получаем несколько случайных точек
                scroll_result = client.scroll(
                    collection_name='enterprise_docs',
                    limit=5
                )
                
                print(f'Найдено точек: {len(scroll_result[0])}')
                
                for i, point in enumerate(scroll_result[0]):
                    payload = point.payload if hasattr(point, 'payload') else {}
                    print(f'Точка {i+1}:')
                    print(f'  ID: {point.id}')
                    print(f'  Payload keys: {list(payload.keys())}')
                    if 'content' in payload:
                        content = payload['content']
                        if len(content) > 100:
                            content = content[:100] + '...'
                        print(f'  Content: {content}')
                    print()
                    
            except Exception as e:
                print(f'Ошибка поиска: {e}')
        else:
            print('Коллекция пуста')
    else:
        print('Коллекция enterprise_docs не найдена')
        
except Exception as e:
    print(f'Ошибка подключения к Qdrant: {e}')
    import traceback
    traceback.print_exc()

