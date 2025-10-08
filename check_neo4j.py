#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка Neo4j базы данных
"""

from neo4j import GraphDatabase

def check_neo4j():
    """Проверка Neo4j"""
    print("=== ПРОВЕРКА NEO4J ===")
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
                    name = work['name']
                    doc_type = work['doc_type']
                    print(f"   {i+1}. {name} (тип: {doc_type})")
            
            # Проверяем документы
            result = session.run("MATCH (d:Document) RETURN d.path as path, d.doc_type as doc_type LIMIT 3")
            docs = list(result)
            if docs:
                print(f"\nОбразцы документов ({len(docs)}):")
                for i, doc in enumerate(docs):
                    path = doc['path']
                    doc_type = doc['doc_type']
                    print(f"   {i+1}. {path} (тип: {doc_type})")
                    
        driver.close()
        print("OK Neo4j проверен успешно")
        
    except Exception as e:
        print(f"ERROR Ошибка проверки Neo4j: {e}")

if __name__ == "__main__":
    check_neo4j()