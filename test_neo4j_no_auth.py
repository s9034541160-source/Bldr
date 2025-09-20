#!/usr/bin/env python3
"""
Тест подключения к Neo4j без аутентификации
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")

def test_no_auth():
    """Тест подключения без аутентификации"""
    print("🔓 Тест подключения к Neo4j без пароля")
    print("=" * 40)
    
    try:
        # Подключение без auth параметра
        driver = GraphDatabase.driver(NEO4J_URI)
        with driver.session() as session:
            result = session.run("RETURN 'Connected without password!' as message")
            record = result.single()
            print(f"✅ Успех: {record['message']}")
            driver.close()
            return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_with_new_password():
    """Тест с новым паролем neopassword"""
    print("\n🔐 Тест с паролем 'neopassword'")
    print("=" * 40)
    
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=("neo4j", "neopassword"))
        with driver.session() as session:
            result = session.run("RETURN 'Connected with neopassword!' as message")
            record = result.single()
            print(f"✅ Успех: {record['message']}")
            driver.close()
            return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def main():
    """Основной тест"""
    print("🚀 Тестирование Neo4j после сброса блокировки")
    print()
    
    # Сначала тест без пароля
    if test_no_auth():
        print("🎉 Подключение без пароля работает!")
        print("💡 Теперь можете установить пароль 'neopassword' в Neo4j Desktop")
    
    # Потом тест с паролем (если уже установлен)
    if test_with_new_password():
        print("🎉 Подключение с паролем работает!")
        print("✅ Neo4j готов для RAG обучения!")
        
        # Обновляем .env файл
        update_env_password("neopassword")
    
def update_env_password(password):
    """Обновляем пароль в .env файле"""
    try:
        with open(".env", 'r') as f:
            lines = f.readlines()
        
        # Обновляем или добавляем строку с паролем
        updated = False
        for i, line in enumerate(lines):
            if line.startswith("NEO4J_PASSWORD="):
                lines[i] = f"NEO4J_PASSWORD={password}\r\n"
                updated = True
                break
        
        if not updated:
            lines.append(f"NEO4J_PASSWORD={password}\r\n")
        
        with open(".env", 'w') as f:
            f.writelines(lines)
        
        print(f"✅ Пароль обновлён в .env: {password}")
        
    except Exception as e:
        print(f"⚠️  Ошибка обновления .env: {e}")

if __name__ == "__main__":
    main()