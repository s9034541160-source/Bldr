#!/usr/bin/env python3
"""
Тест улучшенного парсинга НТД с обходом защиты
"""
import asyncio
import sys
import json
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.append('.')

try:
    from core.improved_ntd_registry_manager import ImprovedNTDRegistryManager
    print("OK: ImprovedNTDRegistryManager imported successfully")
except ImportError as e:
    print(f"ERROR: Failed to import ImprovedNTDRegistryManager: {e}")
    sys.exit(1)

async def test_improved_parsing():
    """Тестируем улучшенный парсинг"""
    print("TESTING IMPROVED NTD PARSING")
    print("=" * 50)
    
    try:
        # Создаем улучшенный менеджер
        manager = ImprovedNTDRegistryManager()
        print("OK: ImprovedNTDRegistryManager created successfully")
        
        # Показываем источники с приоритетами
        print(f"\nAvailable sources: {len(manager.sources)}")
        for source_name, config in manager.sources.items():
            print(f"  - {source_name}: {config['category']} (priority: {config['priority']}) -> {config['url_pattern']}")
        
        # Запускаем улучшенное обновление реестра
        print("\n" + "="*60)
        print("STARTING IMPROVED REGISTRY UPDATE")
        print("="*60)
        
        results = await manager.update_registry_improved(categories=['construction', 'standards'])
        
        print(f"\nUpdate results:")
        print(f"  - Sources processed: {len(results['sources_processed'])}")
        print(f"  - Documents found: {results['documents_found']}")
        print(f"  - Documents saved: {results['documents_saved']}")
        print(f"  - Errors: {len(results['errors'])}")
        
        if results['errors']:
            print("\nErrors:")
            for error in results['errors']:
                print(f"  - {error}")
        
        # Показываем детали по источникам
        print("\nSource details:")
        for source_result in results['sources_processed']:
            print(f"  - {source_result['source']} (priority {source_result['priority']}): {source_result['documents_found']} found, {source_result['documents_saved']} saved")
        
        # Получаем статистику реестра
        print("\n" + "="*60)
        print("REGISTRY STATISTICS")
        print("="*60)
        
        stats = manager.get_registry_stats()
        print(f"Total documents: {stats.get('total_documents', 0)}")
        print(f"Status counts: {stats.get('status_counts', {})}")
        print(f"Category counts: {stats.get('category_counts', {})}")
        
        # Показываем топ канонических имен
        top_names = stats.get('top_canonical_names', [])
        if top_names:
            print(f"\nTop canonical names:")
            for name, count in top_names[:5]:
                print(f"  - {name} (found {count} times)")
        
        # Проверяем качество данных
        print("\n" + "="*60)
        print("DATA QUALITY CHECK")
        print("="*60)
        
        await check_improved_data_quality(manager)
        
        print(f"\nImproved parsing test completed!")
        
    except Exception as e:
        print(f"ERROR during testing: {e}")
        import traceback
        traceback.print_exc()

async def check_improved_data_quality(manager):
    """Проверяем качество данных в улучшенном реестре"""
    try:
        import sqlite3
        
        conn = sqlite3.connect(manager.db_path)
        cursor = conn.cursor()
        
        # 1. Общий объем данных
        cursor.execute("SELECT COUNT(*) FROM ntd_registry_test")
        total_count = cursor.fetchone()[0]
        print(f"1. Total records: {total_count}")
        
        if total_count == 0:
            print("   WARNING: No records found in registry!")
            return
        
        # 2. Проверка на изменения
        cursor.execute("""
            SELECT canonical_id, source_url 
            FROM ntd_registry_test 
            WHERE canonical_id LIKE '%ИЗМ%' OR canonical_id LIKE '%_пр%' OR canonical_id LIKE '%Изм%'
            LIMIT 5
        """)
        amendments = cursor.fetchall()
        print(f"2. Amendments found: {len(amendments)}")
        for amendment in amendments:
            print(f"   - {amendment[0]}")
        
        # 3. Проверка синонимов
        cursor.execute("""
            SELECT canonical_id, ntd_synonyms 
            FROM ntd_registry_test 
            WHERE ntd_synonyms != '[]' AND ntd_synonyms != 'null' AND ntd_synonyms != '""'
            LIMIT 3
        """)
        synonyms_records = cursor.fetchall()
        print(f"3. Records with synonyms: {len(synonyms_records)}")
        for record in synonyms_records:
            try:
                synonyms = json.loads(record[1])
                print(f"   - {record[0]}: {synonyms}")
            except:
                print(f"   - {record[0]}: {record[1]}")
        
        # 4. Проверка качества канонических имен
        cursor.execute("""
            SELECT canonical_id 
            FROM ntd_registry_test 
            WHERE canonical_id LIKE 'СП %' OR canonical_id LIKE 'СНиП %' OR canonical_id LIKE 'ГОСТ %'
            LIMIT 5
        """)
        quality_names = cursor.fetchall()
        print(f"4. Quality canonical names: {len(quality_names)}")
        for name in quality_names:
            print(f"   - {name[0]}")
        
        # 5. Проверка источников
        cursor.execute("""
            SELECT source_url, COUNT(*) as count 
            FROM ntd_registry_test 
            GROUP BY source_url 
            ORDER BY count DESC 
            LIMIT 5
        """)
        sources = cursor.fetchall()
        print(f"5. Top sources:")
        for source, count in sources:
            print(f"   - {source}: {count} documents")
        
        conn.close()
        
        # Оценка качества
        if total_count >= 10:
            print("   SUCCESS: Registry has sufficient data for testing")
        else:
            print("   WARNING: Registry has insufficient data")
            
        if len(amendments) > 0:
            print("   SUCCESS: Amendment detection is working")
        else:
            print("   WARNING: No amendments detected")
            
        if len(synonyms_records) > 0:
            print("   SUCCESS: Synonym extraction is working")
        else:
            print("   WARNING: No synonyms found")
        
    except Exception as e:
        print(f"ERROR checking data quality: {e}")

if __name__ == "__main__":
    asyncio.run(test_improved_parsing())
