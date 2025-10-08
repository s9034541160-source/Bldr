#!/usr/bin/env python3
"""Проверка рёбер и зависимостей в Neo4j"""

import neo4j

def check_edges():
    """Проверяем все типы связей"""
    try:
        driver = neo4j.GraphDatabase.driver('neo4j://127.0.0.1:7687', auth=('neo4j', 'neopassword'))
        session = driver.session()
        
        # Проверяем все типы связей
        result = session.run('MATCH ()-[r]->() RETURN type(r) as rel_type, count(r) as count ORDER BY count DESC')
        print("=== ВСЕ СВЯЗИ ===")
        for record in result:
            print(f"{record['rel_type']}: {record['count']}")
        
        # Проверяем PRECEDES связи
        result = session.run('MATCH ()-[r:PRECEDES]->() RETURN count(r) as precedes_count')
        precedes_count = result.single()['precedes_count']
        print(f"\nPRECEDES рёбра: {precedes_count}")
        
        # Проверяем Work узлы
        result = session.run('MATCH (w:Work) RETURN count(w) as work_count')
        work_count = result.single()['work_count']
        print(f"Work узлы: {work_count}")
        
        session.close()
        driver.close()
        
        return precedes_count, work_count
    except Exception as e:
        print(f"Error: {e}")
        return 0, 0

if __name__ == "__main__":
    print("🔍 Проверяем рёбра и зависимости...")
    precedes, works = check_edges()
    
    print(f"\n📊 Анализ:")
    print(f"Work узлов: {works}")
    print(f"PRECEDES рёбер: {precedes}")
    
    if precedes == 0 and works > 0:
        print("❌ ПРОБЛЕМА: Есть Work узлы, но нет PRECEDES рёбер!")
        print("🔧 Тренер не сохраняет зависимости!")
    elif precedes > 0:
        print("✅ PRECEDES рёбра создаются!")
    else:
        print("⚠️ Нет Work узлов - возможно тренер не запущен")
