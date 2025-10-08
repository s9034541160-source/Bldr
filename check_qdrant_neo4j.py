#!/usr/bin/env python3
"""
Быстрый тест Qdrant (HTTP) + Neo4j (Bolt)
Neo4j доступ: neo4j://127.0.0.1:7687
Пользователь: neo4j
Пароль: neopassword
"""

import sys
import requests
from neo4j import GraphDatabase


# --- Qdrant ---
def check_qdrant(qdrant_url: str, collection: str) -> bool:
    print(f"Проверяю Qdrant на {qdrant_url} ...")
    try:
        r = requests.get(f"{qdrant_url}/collections", timeout=5)
        r.raise_for_status()
        data = r.json()
        collections = [c["name"] for c in data.get("result", {}).get("collections", [])]
        print("Доступные коллекции:", collections)

        if collection in collections:
            try:
                r = requests.post(
                    f"{qdrant_url}/collections/{collection}/points/count",
                    json={"exact": True},
                    timeout=5,
                )
                r.raise_for_status()
                cnt = r.json().get("result", {}).get("count")
                print(f"Коллекция {collection}: {cnt} точек")
            except Exception as e:
                print(f"⚠ Не удалось получить количество точек: {e}")
        else:
            print(f"⚠ Коллекция {collection} не найдена")

        return True
    except Exception as e:
        print(f"Ошибка при подключении к Qdrant: {e}")
        return False


# --- Neo4j ---
def check_neo4j(bolt_url: str, user: str, password: str) -> bool:
    print(f"\nПроверяю Neo4j (Bolt) на {bolt_url} ...")
    try:
        driver = GraphDatabase.driver(bolt_url, auth=(user, password))
        with driver.session() as session:
            nodes = session.run("MATCH (n) RETURN count(n) AS cnt").single()["cnt"]
            rels = session.run("MATCH ()-[r]->() RETURN count(r) AS cnt").single()["cnt"]

            print(f"Узлов в базе: {nodes}")
            print(f"Связей в базе: {rels}")

            if rels > 0:
                print("\nПримеры связей:")
                result = session.run("MATCH (n)-[r]->(m) RETURN n, type(r), m LIMIT 5")
                for rec in result:
                    print(f"{rec['n']} -[{rec['type(r)']}]-> {rec['m']}")

        driver.close()
        return True
    except Exception as e:
        print(f"Ошибка при подключении к Neo4j: {e}")
        return False


# --- Main ---
def main():
    qdrant_url = "http://localhost:6333"
    collection = "enterprise_docs"
    neo4j_url = "neo4j://127.0.0.1:7687"
    neo4j_user = "neo4j"
    neo4j_pass = "neopassword"  # захардкожено

    ok1 = check_qdrant(qdrant_url, collection)
    ok2 = check_neo4j(neo4j_url, neo4j_user, neo4j_pass)

    if ok1 and ok2:
        print("\n✅ Оба сервиса работают корректно")
        sys.exit(0)
    else:
        print("\n❌ Есть проблемы, см. вывод выше")
        sys.exit(2)


if __name__ == "__main__":
    main()
