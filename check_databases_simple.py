#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простая проверка наполнения баз данных RAG системы
"""

import requests
import json
import os
from neo4j import GraphDatabase

def check_qdrant():
    """Проверка Qdrant"""
    print("=== ПРОВЕРКА QDRANT ===")
    try:
        response = requests.get('http://localhost:6333/collections/enterprise_docs')
        if response.status_code == 200:
            data = response.json()
            print("OK Коллекция enterprise_docs существует")
            
            stats = data.get('result', {})
            points_count = stats.get('points_count', 0)
            vectors_count = stats.get('vectors_count', 0)
            
            print(f"Статистика:")
            print(f"   - Точки (points): {points_count}")
            print(f"   - Векторы: {vectors_count}")
            
            # Получаем несколько точек
            scroll_response = requests.post('http://localhost:6333/collections/enterprise_docs/points/scroll', 
                                         json={'limit': 3})
            if scroll_response.status_code == 200:
                points_data = scroll_response.json()
                points = points_data.get('result', {}).get('points', [])
                
                print(f"\nОбразцы данных ({len(points)} точек):")
                for i, point in enumerate(points):
                    print(f"\n   Точка {i+1}:")
                    print(f"     ID: {point.get('id')}")
                    payload = point.get('payload', {})
                    print(f"     Ключи payload: {list(payload.keys())}")
                    
                    if 'content' in payload:
                        content = payload['content']
                        preview = content[:100] + '...' if len(content) > 100 else content
                        print(f"     Контент: {preview}")
                    
                    if 'file_path' in payload:
                        print(f"     Файл: {payload['file_path']}")
                        
        else:
            print(f"ERROR Ошибка подключения к Qdrant: {response.status_code}")
            
    except Exception as e:
        print(f"ERROR Ошибка проверки Qdrant: {e}")

def check_neo4j():
    """Проверка Neo4j"""
    print("\n=== ПРОВЕРКА NEO4J ===")
    try:
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=None)
        
        with driver.session() as session:
            # Проверяем количество узлов
            result = session.run("MATCH (n) RETURN labels(n) as labels, count(n) as count")
            nodes_info = {}
            for record in result:
                labels = record['labels']
                count = record['count']
                if labels:
                    label = labels[0]
                    nodes_info[label] = count
            
            print("Статистика узлов:")
            for label, count in nodes_info.items():
                print(f"   - {label}: {count}")
            
            # Проверяем связи
            result = session.run("MATCH ()-[r]->() RETURN type(r) as rel_type, count(r) as count")
            relationships = {}
            for record in result:
                rel_type = record['rel_type']
                count = record['count']
                relationships[rel_type] = count
            
            print("\nСтатистика связей:")
            for rel_type, count in relationships.items():
                print(f"   - {rel_type}: {count}")
            
            # Проверяем работы
            result = session.run("MATCH (w:Work) RETURN w.name as name, w.doc_type as doc_type LIMIT 3")
            works = list(result)
            if works:
                print(f"\nОбразцы работ ({len(works)}):")
                for i, work in enumerate(works):
                    print(f"   {i+1}. {work['name']} (тип: {work['doc_type']})")
                    
        driver.close()
        print("OK Neo4j проверен успешно")
        
    except Exception as e:
        print(f"ERROR Ошибка проверки Neo4j: {e}")

def check_processed_files():
    """Проверка файла processed_files.json"""
    print("\n=== ПРОВЕРКА PROCESSED_FILES.JSON ===")
    try:
        if os.path.exists("processed_files.json"):
            with open("processed_files.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                valid_files = [item for item in data if isinstance(item, dict)]
                print(f"OK Обработано файлов: {len(valid_files)}")
                
                if valid_files:
                    print("\nПоследние обработанные файлы:")
                    for i, file_info in enumerate(valid_files[-3:]):
                        print(f"   {i+1}. {file_info.get('file_path', 'N/A')}")
                        print(f"      Тип: {file_info.get('doc_type', 'N/A')}")
                        print(f"      Хеш: {file_info.get('file_hash', 'N/A')[:16]}...")
        else:
            print("ERROR Файл processed_files.json не найден")
            
    except Exception as e:
        print(f"ERROR Ошибка проверки processed_files.json: {e}")

if __name__ == "__main__":
    print("ПРОВЕРКА НАПОЛНЕНИЯ БАЗ ДАННЫХ RAG СИСТЕМЫ")
    print("=" * 60)
    
    check_qdrant()
    check_neo4j()
    check_processed_files()
    
    print("\n" + "=" * 60)
    print("ПРОВЕРКА ЗАВЕРШЕНА")
