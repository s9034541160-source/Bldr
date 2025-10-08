#!/usr/bin/env python3
"""
Быстрый тест разных паролей Neo4j
"""

from neo4j import GraphDatabase

def test_passwords():
    """Тест разных паролей"""
    uri = "neo4j://localhost:7687"
    user = "neo4j"
    
    passwords = [
        "neopassword",
        "neo4j", 
        "",
        "password",
        "admin",
        "test"
    ]
    
    print("🔐 Быстрый тест паролей Neo4j")
    print("=" * 35)
    
    for password in passwords:
        print(f"Пробуем: {'(пустой)' if password == '' else password}")
        
        try:
            driver = GraphDatabase.driver(uri, auth=(user, password))
            with driver.session() as session:
                result = session.run("RETURN 'Connected!' as msg")
                record = result.single()
                print(f"✅ УСПЕХ! Пароль: '{password}'")
                driver.close()
                return password
        except Exception as e:
            if "rate limit" in str(e).lower():
                print("⏸️  Блокировка")
                break
            else:
                print("❌ Неверно")
    
    return None

if __name__ == "__main__":
    found = test_passwords()
    if found is not None:
        print(f"\n🎉 Рабочий пароль: '{found}'")
    else:
        print("\n❌ Пароль не найден или блокировка активна")
        print("💡 Попробуйте подождать 5 минут или проверить пароль в Neo4j Desktop")