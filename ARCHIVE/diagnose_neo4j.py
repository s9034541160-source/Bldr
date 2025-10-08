#!/usr/bin/env python3
"""
Детальная диагностика Neo4j подключения
"""

from neo4j import GraphDatabase
import socket

def check_port_connection():
    """Проверка TCP подключения к порту 7687"""
    print("🔌 Проверка TCP подключения к порту 7687...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('localhost', 7687))
        sock.close()
        
        if result == 0:
            print("✅ Порт 7687 доступен")
            return True
        else:
            print("❌ Порт 7687 недоступен")
            return False
    except Exception as e:
        print(f"❌ Ошибка проверки порта: {e}")
        return False

def test_neo4j_versions():
    """Тест разных версий протокола"""
    protocols = [
        "neo4j://localhost:7687",
        "bolt://localhost:7687", 
        "neo4j://127.0.0.1:7687",
        "bolt://127.0.0.1:7687"
    ]
    
    user = "neo4j"
    password = "neopassword"
    
    print("\n🔄 Тестирование разных протоколов...")
    
    for protocol in protocols:
        print(f"\n   Протокол: {protocol}")
        
        try:
            driver = GraphDatabase.driver(protocol, auth=(user, password))
            
            # Получаем информацию о сервере
            with driver.session() as session:
                result = session.run("""
                    CALL dbms.components() YIELD name, versions, edition
                    RETURN name, versions, edition
                """)
                
                print("   ✅ Подключение успешно!")
                for record in result:
                    print(f"      {record['name']}: {record['versions']} ({record['edition']})")
                
                driver.close()
                return protocol
                
        except Exception as e:
            error_str = str(e)
            if "authentication failure" in error_str.lower():
                print("   ❌ Неверный пароль")
            elif "connection refused" in error_str.lower():
                print("   ❌ Подключение отклонено")
            elif "timeout" in error_str.lower():
                print("   ❌ Тайм-аут подключения")
            else:
                print(f"   ❌ Ошибка: {error_str}")
    
    return None

def test_first_time_setup():
    """Тест первоначальной настройки (если пароль по умолчанию)"""
    print("\n🔧 Тест первоначальной настройки...")
    
    try:
        # При первом запуске пароль может быть "neo4j"
        driver = GraphDatabase.driver("neo4j://localhost:7687", auth=("neo4j", "neo4j"))
        
        with driver.session() as session:
            # Попробуем сменить пароль
            session.run("ALTER CURRENT USER SET PASSWORD FROM 'neo4j' TO 'neopassword'")
            print("✅ Пароль изменён с 'neo4j' на 'neopassword'")
            
        driver.close()
        
        # Теперь пробуем подключиться с новым паролем
        driver = GraphDatabase.driver("neo4j://localhost:7687", auth=("neo4j", "neopassword"))
        with driver.session() as session:
            result = session.run("RETURN 'Password changed successfully!' as msg")
            record = result.single()
            print(f"✅ {record['msg']}")
        driver.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка настройки: {e}")
        return False

def main():
    """Главная диагностика"""
    print("🔍 Детальная диагностика Neo4j")
    print("=" * 40)
    
    # 1. Проверка порта
    if not check_port_connection():
        print("\n❌ Neo4j недоступен на порту 7687")
        print("💡 Убедитесь, что инстанс Bldr_2 запущен в Neo4j Desktop")
        return
    
    # 2. Тест протоколов
    working_protocol = test_neo4j_versions()
    if working_protocol:
        print(f"\n🎉 Найден рабочий протокол: {working_protocol}")
        update_env_config(working_protocol)
        return
    
    # 3. Тест первоначальной настройки
    if test_first_time_setup():
        print("\n🎉 Первоначальная настройка выполнена!")
        update_env_config("neo4j://localhost:7687")
        return
    
    print("\n❌ Все тесты провалились")
    print("\n🔧 Рекомендации:")
    print("1. Откройте Neo4j Browser: http://localhost:7474")
    print("2. Попробуйте подключиться вручную")
    print("3. Проверьте логи Neo4j в Desktop")
    print("4. Убедитесь что инстанс Bldr_2 активен")

def update_env_config(uri):
    """Обновляем конфигурацию в .env"""
    print(f"\n💾 Обновляем .env с рабочими настройками...")
    
    try:
        with open(".env", 'r') as f:
            lines = f.readlines()
        
        # Обновляем настройки
        settings = {
            "NEO4J_URI": uri,
            "NEO4J_USER": "neo4j",
            "NEO4J_PASSWORD": "neopassword"
        }
        
        for setting, value in settings.items():
            updated = False
            for i, line in enumerate(lines):
                if line.startswith(f"{setting}="):
                    lines[i] = f"{setting}={value}\r\n"
                    updated = True
                    break
            
            if not updated:
                lines.append(f"{setting}={value}\r\n")
        
        with open(".env", 'w') as f:
            f.writelines(lines)
        
        print("✅ .env файл обновлён")
        
    except Exception as e:
        print(f"⚠️  Ошибка обновления .env: {e}")

if __name__ == "__main__":
    main()