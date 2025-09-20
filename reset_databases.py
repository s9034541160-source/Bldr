#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Скрипт для полной очистки всех баз данных перед повторным запуском
"""

import os
import shutil
import json
from pathlib import Path

def reset_databases():
    """Очищает все базы данных"""
    
    print("🔄 СБРОС ВСЕХ БАЗ ДАННЫХ")
    print("=" * 40)
    
    base_dir = os.getenv("BASE_DIR", "I:/docs")
    
    # 1. Очистка JSON файлов обработанных документов
    processed_files = [
        f"{base_dir}/reports/processed_files.json",
        f"{base_dir}/clean_base/processed_files.json",
        "C:/Bldr/processed_files.json"
    ]
    
    for file_path in processed_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"✅ Удален: {file_path}")
            except Exception as e:
                print(f"❌ Ошибка удаления {file_path}: {e}")
    
    # 2. Очистка Qdrant базы
    qdrant_path = f"{base_dir}/qdrant_db"
    if os.path.exists(qdrant_path):
        try:
            shutil.rmtree(qdrant_path)
            print(f"✅ Удалена Qdrant база: {qdrant_path}")
        except Exception as e:
            print(f"❌ Ошибка удаления Qdrant: {e}")
    
    # 3. Очистка FAISS индекса
    faiss_files = [
        f"{base_dir}/faiss_index.index",
        f"{base_dir}/clean_base/faiss_index.index"
    ]
    
    for file_path in faiss_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"✅ Удален FAISS индекс: {file_path}")
            except Exception as e:
                print(f"❌ Ошибка удаления FAISS: {e}")
    
    # 4. Очистка Neo4j базы (только если локальная)
    neo4j_data_path = f"{base_dir}/neo4j_data"
    if os.path.exists(neo4j_data_path):
        try:
            shutil.rmtree(neo4j_data_path)
            print(f"✅ Удалена Neo4j база: {neo4j_data_path}")
        except Exception as e:
            print(f"❌ Ошибка удаления Neo4j: {e}")
    
    # 5. Очистка SQLite баз NTD
    ntd_db_files = [
        f"{base_dir}/norms_db/ntd_local.db",
        f"{base_dir}/clean_base/ntd_local.db"
    ]
    
    for file_path in ntd_db_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"✅ Удалена NTD база: {file_path}")
            except Exception as e:
                print(f"❌ Ошибка удаления NTD: {e}")
    
    # 6. Очистка отчетов
    reports_dir = f"{base_dir}/reports"
    if os.path.exists(reports_dir):
        try:
            shutil.rmtree(reports_dir)
            print(f"✅ Удалены отчеты: {reports_dir}")
        except Exception as e:
            print(f"❌ Ошибка удаления отчетов: {e}")
    
    # 7. Создание пустых файлов для корректной работы
    os.makedirs(f"{base_dir}/reports", exist_ok=True)
    os.makedirs(f"{base_dir}/norms_db", exist_ok=True)
    
    # Пустой JSON файл обработанных документов
    with open(f"{base_dir}/reports/processed_files.json", "w") as f:
        json.dump({}, f)
    
    print("\n🎉 ВСЕ БАЗЫ ДАННЫХ ОЧИЩЕНЫ!")
    print("💡 Теперь можно запускать обработку заново")

if __name__ == "__main__":
    reset_databases()