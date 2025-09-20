#!/usr/bin/env python3
"""
Сброс пароля Neo4j через консольные команды
"""

import subprocess
import os
import time
from pathlib import Path

def find_neo4j_path():
    """Найти путь к Neo4j"""
    # Возможные пути установки Neo4j Desktop
    possible_paths = [
        r"C:\Users\{}\AppData\Local\Neo4j\Relate\Data\projects\project-*\dbmss\dbms-*\bin".format(os.getenv('USERNAME')),
        r"C:\Program Files\Neo4j CE 4.*\bin",
        r"C:\Program Files\Neo4j CE 5.*\bin", 
        r"C:\Neo4j\bin",
        r"C:\neo4j-*\bin"
    ]
    
    for path_pattern in possible_paths:
        if '*' in path_pattern:
            # Используем glob для поиска путей с wildcards
            import glob
            matches = glob.glob(path_pattern)
            for match in matches:
                if os.path.exists(os.path.join(match, 'neo4j-admin.bat')):
                    return match
        else:
            if os.path.exists(os.path.join(path_pattern, 'neo4j-admin.bat')):
                return path_pattern
    
    return None

def reset_neo4j_password():
    """Сброс пароля Neo4j"""
    print("🔐 Сброс пароля Neo4j")
    print("=" * 40)
    
    # Найти Neo4j
    neo4j_path = find_neo4j_path()
    if not neo4j_path:
        print("❌ Neo4j не найден")
        print("💡 Попробуйте установить пароль через Neo4j Desktop:")
        print("   1. Откройте Neo4j Desktop")
        print("   2. Выберите базу данных")
        print("   3. Нажмите на три точки -> Settings")
        print("   4. Установите пароль: neopassword")
        return False
    
    print(f"✅ Neo4j найден: {neo4j_path}")
    
    # Остановить Neo4j (если запущен)
    print("🛑 Останавливаем Neo4j...")
    try:
        subprocess.run([os.path.join(neo4j_path, 'neo4j.bat'), 'stop'], 
                      capture_output=True, text=True, timeout=30)
    except:
        pass
    
    time.sleep(5)
    
    # Сбросить пароль
    print("🔄 Сбрасываем пароль на 'neopassword'...")
    try:
        result = subprocess.run([
            os.path.join(neo4j_path, 'neo4j-admin.bat'),
            'dbms', 'set-initial-password', 'neopassword'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Пароль успешно установлен")
        else:
            print(f"⚠️  Результат: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Ошибка сброса пароля: {e}")
    
    # Запустить Neo4j
    print("🚀 Запускаем Neo4j...")
    try:
        subprocess.run([os.path.join(neo4j_path, 'neo4j.bat'), 'start'], 
                      capture_output=True, text=True, timeout=30)
        print("✅ Neo4j перезапущен")
    except Exception as e:
        print(f"⚠️  Ошибка запуска: {e}")
    
    return True

def main():
    if not reset_neo4j_password():
        print("\n🔧 Альтернативные способы:")
        print("1. Через Neo4j Desktop:")
        print("   - Откройте Neo4j Desktop")
        print("   - Выберите проект/базу")
        print("   - Settings -> Password: neopassword")
        print()
        print("2. Временно отключить Neo4j:")
        print("   - Добавьте SKIP_NEO4J=true в .env файл")
        print("   - Система будет работать без графовой базы")

if __name__ == "__main__":
    main()