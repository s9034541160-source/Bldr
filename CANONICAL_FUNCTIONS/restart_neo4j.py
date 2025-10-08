# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: restart_neo4j
# Основной источник: C:\Bldr\emergency_full_reset.py
# Дубликаты (для справки):
#   - C:\Bldr\recovery_script.py
#================================================================================
def restart_neo4j():
    """ПЕРЕЗАПУСК NEO4J"""
    print("\n🔄 ПЕРЕЗАПУСК NEO4J")
    print("=" * 20)
    
    neo4j_desktop_paths = [
        r"C:\Users\%USERNAME%\AppData\Local\Programs\Neo4j Desktop\Neo4j Desktop.exe",
        r"C:\Program Files\Neo4j Desktop\Neo4j Desktop.exe"
    ]
    
    for path in neo4j_desktop_paths:
        expanded_path = os.path.expandvars(path)
        if os.path.exists(expanded_path):
            print(f"   🚀 Запускаем: {expanded_path}")
            subprocess.Popen([expanded_path], shell=True)
            break
    
    print("⏳ Ждем запуска Neo4j (30 секунд)...")
    time.sleep(30)
    print("✅ Neo4j должен быть готов")