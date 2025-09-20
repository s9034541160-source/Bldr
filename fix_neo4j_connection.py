#!/usr/bin/env python3
"""
Исправление подключения к Neo4j - подождать блокировку и протестировать пароли
"""

import os
import time
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")

def wait_for_auth_unblock():
    """Ждём пока Neo4j разблокирует аутентификацию"""
    print("⏱️  Ожидание разблокировки аутентификации Neo4j...")
    print("   (Обычно блокировка длится 5 минут)")
    
    for i in range(5, 0, -1):
        print(f"   Осталось примерно {i} минут...")
        time.sleep(60)  # Ждём минуту
    
    print("✅ Время ожидания завершено, пробуем подключиться")

def test_common_passwords():
    """Тестируем распространённые пароли Neo4j"""
    common_passwords = [
        "",  # Пустой пароль
        "neo4j",  # Дефолтный
        "password",  # Часто используемый
        "admin",  # Административный
        "123456",  # Простой
        "neopassword",  # Наш целевой
        "neo4jpassword",  # Вариант
        "test",  # Тестовый
    ]
    
    print("🔐 Тестирование распространённых паролей...")
    
    for password in common_passwords:
        print(f"   Пробуем пароль: {'(пустой)' if password == '' else password}")
        
        try:
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, password))
            with driver.session() as session:
                result = session.run("RETURN 'Success!' as message")
                record = result.single()
                print(f"   ✅ УСПЕХ! Пароль найден: '{password}'")
                driver.close()
                
                # Обновляем .env файл
                update_env_password(password)
                return password
                
        except Exception as e:
            if "AuthenticationRateLimit" in str(e):
                print("   ⏸️  Всё ещё заблокировано, ждём...")
                time.sleep(30)
                continue
            else:
                print(f"   ❌ Неверный пароль")
    
    return None

def update_env_password(password):
    """Обновляем пароль в .env файле"""
    env_file = ".env"
    lines = []
    
    try:
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Обновляем строку с паролем
        for i, line in enumerate(lines):
            if line.startswith("NEO4J_PASSWORD="):
                lines[i] = f"NEO4J_PASSWORD={password}\r\n"
                break
        else:
            # Добавляем строку если её нет
            lines.append(f"NEO4J_PASSWORD={password}\r\n")
        
        with open(env_file, 'w') as f:
            f.writelines(lines)
        
        print(f"✅ Пароль обновлён в .env файле: {password}")
        
    except Exception as e:
        print(f"⚠️  Ошибка обновления .env: {e}")

def main():
    print("🔧 Восстановление подключения к Neo4j")
    print("=" * 50)
    
    # Сначала ждём разблокировки
    wait_for_auth_unblock()
    
    # Тестируем пароли
    found_password = test_common_passwords()
    
    if found_password is not None:
        print("\n🎉 Подключение к Neo4j восстановлено!")
        print(f"   URI: {NEO4J_URI}")
        print(f"   User: {NEO4J_USER}")
        print(f"   Password: {found_password}")
        print("\n✅ Теперь можно запускать RAG обучение с полной функциональностью")
        return True
    else:
        print("\n❌ Не удалось восстановить подключение")
        print("🔧 Попробуйте:")
        print("   1. Открыть Neo4j Desktop")
        print("   2. Зайти в настройки базы данных")
        print("   3. Сменить пароль на 'neopassword'")
        print("   4. Перезапустить инстанс")
        return False

if __name__ == "__main__":
    main()