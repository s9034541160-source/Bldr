#!/usr/bin/env python3
"""
Простой тест подключения к Neo4j
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neopassword")

def test_neo4j_connection():
    """Тестирование подключения к Neo4j с разными вариантами"""
    
    print("🔍 Тест подключения к Neo4j")
    print("=" * 40)
    print(f"URI: {NEO4J_URI}")
    print(f"User: {NEO4J_USER}")
    print(f"Password: {'*' * len(NEO4J_PASSWORD)}")
    print()
    
    # Тест 1: Основной URI
    print("1️⃣ Тест с основным URI...")
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        with driver.session() as session:
            result = session.run("RETURN 'Connection successful' as message")
            record = result.single()
            print(f"✅ Успех: {record['message']}")
            driver.close()
            return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Тест 2: localhost вместо 127.0.0.1
    print("\n2️⃣ Тест с localhost...")
    try:
        uri_localhost = "neo4j://localhost:7687"
        driver = GraphDatabase.driver(uri_localhost, auth=(NEO4J_USER, NEO4J_PASSWORD))
        with driver.session() as session:
            result = session.run("RETURN 'Connection successful with localhost' as message")
            record = result.single()
            print(f"✅ Успех: {record['message']}")
            driver.close()
            return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Тест 3: bolt:// протокол
    print("\n3️⃣ Тест с bolt протоколом...")
    try:
        uri_bolt = "bolt://localhost:7687"
        driver = GraphDatabase.driver(uri_bolt, auth=(NEO4J_USER, NEO4J_PASSWORD))
        with driver.session() as session:
            result = session.run("RETURN 'Connection successful with bolt' as message")
            record = result.single()
            print(f"✅ Успех: {record['message']}")
            driver.close()
            return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Тест 4: Пустой пароль (дефолт)
    print("\n4️⃣ Тест с пустым паролем...")
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, ""))
        with driver.session() as session:
            result = session.run("RETURN 'Connection successful with empty password' as message")
            record = result.single()
            print(f"✅ Успех: {record['message']}")
            driver.close()
            return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Тест 5: Дефолтный пароль neo4j
    print("\n5️⃣ Тест с дефолтным паролем 'neo4j'...")
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, "neo4j"))
        with driver.session() as session:
            result = session.run("RETURN 'Connection successful with default password' as message")
            record = result.single()
            print(f"✅ Успех: {record['message']}")
            driver.close()
            return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    print("\n❌ Все тесты подключения провалились")
    print("🔧 Рекомендации:")
    print("   1. Проверьте, что Neo4j Desktop запущен")
    print("   2. Убедитесь, что инстанс базы данных активен")
    print("   3. Проверьте учетные данные в Neo4j Desktop")
    print("   4. Убедитесь, что порт 7687 не заблокирован")
    
    return False

if __name__ == "__main__":
    test_neo4j_connection()