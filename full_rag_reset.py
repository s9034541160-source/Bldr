#!/usr/bin/env python3
"""
ПОЛНЫЙ СБРОС RAG ОБУЧЕНИЯ
Очищает все базы данных, кэши и обработанные файлы
"""

import os
import shutil
import time
import subprocess
from pathlib import Path

def main():
    print('🔥 ПОЛНЫЙ СБРОС RAG ОБУЧЕНИЯ!')
    print('=' * 50)
    
    # 1. Очищаем Qdrant
    print('1️⃣ Очистка Qdrant...')
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host='localhost', port=6333)
        
        # Удаляем коллекцию
        try:
            client.delete_collection('enterprise_docs')
            print('✅ Коллекция enterprise_docs удалена')
        except Exception as e:
            print(f'⚠️ Ошибка удаления коллекции: {e}')
        
        # Создаем новую пустую коллекцию
        try:
            from qdrant_client.http.models import VectorParams, Distance
            client.create_collection(
                collection_name='enterprise_docs',
                vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
            )
            print('✅ Новая коллекция enterprise_docs создана')
        except Exception as e:
            print(f'⚠️ Ошибка создания коллекции: {e}')
            
    except Exception as e:
        print(f'❌ Ошибка очистки Qdrant: {e}')
    
    # 2. Очищаем Neo4j
    print('\n2️⃣ Очистка Neo4j...')
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver('bolt://localhost:7687')
        
        with driver.session() as session:
            # Удаляем все узлы и связи
            session.run('MATCH (n) DETACH DELETE n')
            print('✅ Все узлы и связи Neo4j удалены')
            
        driver.close()
    except Exception as e:
        print(f'❌ Ошибка очистки Neo4j: {e}')
    
    # 3. Очищаем Redis
    print('\n3️⃣ Очистка Redis...')
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.flushdb()
        print('✅ Redis очищен')
    except Exception as e:
        print(f'❌ Ошибка очистки Redis: {e}')
    
    # 4. Удаляем processed_files.json
    print('\n4️⃣ Удаление processed_files.json...')
    try:
        if os.path.exists('processed_files.json'):
            os.remove('processed_files.json')
            print('✅ processed_files.json удален')
        else:
            print('⚠️ processed_files.json не найден')
    except Exception as e:
        print(f'❌ Ошибка удаления processed_files.json: {e}')
    
    # 5. Очищаем кэш
    print('\n5️⃣ Очистка кэша...')
    try:
        if os.path.exists('temp'):
            shutil.rmtree('temp')
            print('✅ Папка temp удалена')
        if os.path.exists('__pycache__'):
            shutil.rmtree('__pycache__')
            print('✅ Папка __pycache__ удалена')
        if os.path.exists('logs'):
            shutil.rmtree('logs')
            print('✅ Папка logs удалена')
    except Exception as e:
        print(f'❌ Ошибка очистки кэша: {e}')
    
    # 6. Очищаем processed и failed папки
    print('\n6️⃣ Очистка processed и failed папок...')
    try:
        if os.path.exists('processed'):
            shutil.rmtree('processed')
            print('✅ Папка processed удалена')
        if os.path.exists('failed'):
            shutil.rmtree('failed')
            print('✅ Папка failed удалена')
    except Exception as e:
        print(f'❌ Ошибка очистки папок: {e}')
    
    # 7. Очищаем все .pyc файлы
    print('\n7️⃣ Очистка .pyc файлов...')
    try:
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.pyc'):
                    os.remove(os.path.join(root, file))
        print('✅ Все .pyc файлы удалены')
    except Exception as e:
        print(f'❌ Ошибка очистки .pyc файлов: {e}')
    
    # 8. Финальная проверка
    print('\n8️⃣ Финальная проверка...')
    
    # Проверяем Qdrant
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host='localhost', port=6333)
        collections = client.get_collections()
        print(f'📊 Коллекций в Qdrant: {len(collections.collections)}')
        
        if len(collections.collections) > 0:
            for col in collections.collections:
                print(f'  - {col.name}')
        
    except Exception as e:
        print(f'❌ Ошибка проверки Qdrant: {e}')
    
    # Проверяем Redis
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        keys = r.keys('*')
        print(f'📊 Ключей в Redis: {len(keys)}')
        
    except Exception as e:
        print(f'❌ Ошибка проверки Redis: {e}')
    
    print('\n🎉 ПОЛНЫЙ СБРОС ЗАВЕРШЕН!')
    print('✅ Все базы данных очищены')
    print('✅ Все кэши удалены')
    print('✅ Все обработанные файлы сброшены')
    print('\n🚀 Система готова к полному переобучению!')

if __name__ == "__main__":
    main()
