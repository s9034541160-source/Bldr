#!/usr/bin/env python3
"""
ПОЛНЫЙ СБРОС ВСЕХ ДАННЫХ RAG СИСТЕМЫ
Очищает Qdrant, Neo4j, processed_files.json и перемещает файлы обратно
"""

import os
import json
import shutil
from pathlib import Path
from qdrant_client import QdrantClient
from neo4j import GraphDatabase

def reset_qdrant():
    """Очистка Qdrant"""
    try:
        client = QdrantClient(host="localhost", port=6333)
        client.delete_collection("enterprise_docs")
        print("✅ Qdrant collection 'enterprise_docs' deleted")
        
        # Пересоздаем коллекцию
        client.create_collection(
            collection_name="enterprise_docs",
            vectors_config={"size": 768, "distance": "Cosine"}
        )
        print("✅ Qdrant collection 'enterprise_docs' recreated")
    except Exception as e:
        print(f"❌ Qdrant reset failed: {e}")

def reset_neo4j():
    """Очистка Neo4j"""
    try:
        driver = GraphDatabase.driver("bolt://localhost:7687")
        with driver.session() as session:
            # Удаляем все узлы и связи
            session.run("MATCH (n) DETACH DELETE n")
            print("✅ Neo4j database cleared")
    except Exception as e:
        print(f"❌ Neo4j reset failed: {e}")

def reset_processed_files():
    """Очистка processed_files.json"""
    try:
        if os.path.exists("processed_files.json"):
            os.remove("processed_files.json")
            print("✅ processed_files.json deleted")
    except Exception as e:
        print(f"❌ processed_files.json reset failed: {e}")

def move_files_back():
    """Перемещение файлов из processed обратно в исходную папку"""
    try:
        processed_dir = Path("I:/docs/processed")
        source_dir = Path("I:/docs/downloaded/minstroyrf")
        
        if processed_dir.exists():
            # Перемещаем все файлы обратно
            for file_path in processed_dir.rglob("*"):
                if file_path.is_file():
                    relative_path = file_path.relative_to(processed_dir)
                    dest_path = source_dir / relative_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(file_path), str(dest_path))
                    print(f"✅ Moved back: {relative_path}")
            
            # Удаляем пустые папки
            for empty_dir in processed_dir.rglob("*"):
                if empty_dir.is_dir() and not any(empty_dir.iterdir()):
                    empty_dir.rmdir()
                    print(f"✅ Removed empty dir: {empty_dir}")
            
            print("✅ All files moved back to source directory")
        else:
            print("ℹ️ No processed directory found")
    except Exception as e:
        print(f"❌ File move back failed: {e}")

def main():
    """Полный сброс системы"""
    print("🔄 ПОЛНЫЙ СБРОС RAG СИСТЕМЫ")
    print("=" * 50)
    
    # Подтверждение
    confirm = input("⚠️ Это удалит ВСЕ данные! Продолжить? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Отменено пользователем")
        return
    
    print("\n🔄 Начинаем сброс...")
    
    # 1. Очистка Qdrant
    print("\n1️⃣ Очистка Qdrant...")
    reset_qdrant()
    
    # 2. Очистка Neo4j
    print("\n2️⃣ Очистка Neo4j...")
    reset_neo4j()
    
    # 3. Очистка processed_files.json
    print("\n3️⃣ Очистка processed_files.json...")
    reset_processed_files()
    
    # 4. Перемещение файлов обратно
    print("\n4️⃣ Перемещение файлов обратно...")
    move_files_back()
    
    print("\n🎉 ПОЛНЫЙ СБРОС ЗАВЕРШЕН!")
    print("✅ Теперь можно запускать .\\rag для полной переобработки всех файлов")

if __name__ == "__main__":
    main()
