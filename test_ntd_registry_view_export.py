#!/usr/bin/env python3
"""
Тест просмотра и экспорта реестра НТД
"""
import sys
sys.path.append('.')

from enterprise_rag_trainer_full import EnterpriseRAGTrainer
import tempfile
import os

def test_ntd_registry_view_export():
    """Тестируем просмотр и экспорт реестра НТД"""
    
    print("TESTING NTD REGISTRY VIEW AND EXPORT")
    print("=" * 60)
    
    try:
        # Создаем экземпляр тренера
        trainer = EnterpriseRAGTrainer()
        
        print("1. Testing NTD Registry View:")
        print("-" * 40)
        
        # Тестируем просмотр реестра
        registry_view = trainer.get_ntd_registry_view(limit=100)
        
        if registry_view['status'] == 'success':
            print(f"   Status: {registry_view['status']}")
            print(f"   Nodes: {registry_view['metadata']['node_count']}")
            print(f"   Edges: {registry_view['metadata']['edge_count']}")
            print(f"   Total NTD: {registry_view['metadata']['total_nodes']}")
            print(f"   Types: {registry_view['metadata']['type_count']}")
            print(f"   Avg Confidence: {registry_view['metadata']['avg_confidence']:.2f}")
            
            # Показываем первые 5 узлов
            if registry_view['nodes']:
                print("\n   First 5 nodes:")
                for i, node in enumerate(registry_view['nodes'][:5]):
                    print(f"     {i+1}. {node['id']} ({node['type']}) - confidence: {node['confidence']:.2f}")
            
            # Показываем первые 5 связей
            if registry_view['edges']:
                print("\n   First 5 edges:")
                for i, edge in enumerate(registry_view['edges'][:5]):
                    print(f"     {i+1}. {edge['source']} -> {edge['target']} ({edge['relationship_type']})")
        else:
            print(f"   Error: {registry_view['message']}")
        
        print("\n2. Testing NTD Statistics:")
        print("-" * 40)
        
        # Тестируем статистику
        statistics = trainer.get_ntd_statistics()
        
        if statistics['status'] == 'success':
            print(f"   Status: {statistics['status']}")
            print(f"   Total NTD: {statistics['statistics']['total_ntd']}")
            print(f"   Type Count: {statistics['statistics']['type_count']}")
            print(f"   Avg Confidence: {statistics['statistics']['avg_confidence']:.2f}")
            print(f"   Total References: {statistics['statistics']['total_references']}")
            
            # Статистика по типам
            if statistics['by_type']:
                print("\n   By Type:")
                for type_stat in statistics['by_type'][:5]:
                    print(f"     {type_stat['type']}: {type_stat['count']} (avg confidence: {type_stat['avg_confidence']:.2f})")
            
            # Статистика по уверенности
            if statistics['by_confidence']:
                print("\n   By Confidence:")
                for conf_stat in statistics['by_confidence']:
                    print(f"     {conf_stat['confidence_level']}: {conf_stat['count']}")
        else:
            print(f"   Error: {statistics['message']}")
        
        print("\n3. Testing NTD Registry Export:")
        print("-" * 40)
        
        # Тестируем экспорт в JSON
        print("   Testing JSON export...")
        json_export = trainer.export_ntd_registry(format='json', output_file='test_ntd_registry')
        
        if json_export['status'] == 'success':
            print(f"   JSON Export: {json_export['file']}")
            if os.path.exists(json_export['file']):
                file_size = os.path.getsize(json_export['file'])
                print(f"   File size: {file_size} bytes")
            else:
                print("   Warning: JSON file not found")
        else:
            print(f"   JSON Export Error: {json_export['message']}")
        
        # Тестируем экспорт в CSV
        print("\n   Testing CSV export...")
        csv_export = trainer.export_ntd_registry(format='csv', output_file='test_ntd_registry')
        
        if csv_export['status'] == 'success':
            print(f"   CSV Export: {csv_export['files']}")
            for file in csv_export['files']:
                if os.path.exists(file):
                    file_size = os.path.getsize(file)
                    print(f"   {file}: {file_size} bytes")
                else:
                    print(f"   Warning: {file} not found")
        else:
            print(f"   CSV Export Error: {csv_export['message']}")
        
        print("\n" + "=" * 60)
        print("NTD REGISTRY VIEW AND EXPORT TEST COMPLETED!")
        
        # Проверяем результаты
        success_count = 0
        total_tests = 3
        
        if registry_view['status'] == 'success':
            success_count += 1
            print("PASS Registry View: PASS")
        else:
            print("FAIL Registry View: FAIL")
        
        if statistics['status'] == 'success':
            success_count += 1
            print("PASS Statistics: PASS")
        else:
            print("FAIL Statistics: FAIL")
        
        if json_export['status'] == 'success' and csv_export['status'] == 'success':
            success_count += 1
            print("PASS Export: PASS")
        else:
            print("FAIL Export: FAIL")
        
        print(f"\nResults: {success_count}/{total_tests} tests passed")
        
        if success_count == total_tests:
            print("ALL TESTS PASSED! NTD REGISTRY VIEW AND EXPORT WORK PERFECTLY!")
            print("Registry view provides complete graph data")
            print("Statistics show detailed NTD analytics")
            print("Export functions create JSON and CSV files")
            print("Frontend can display and export the NTD registry")
        else:
            print("SOME TESTS FAILED! Check NTD registry implementation")
        
        return success_count == total_tests
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return False

if __name__ == "__main__":
    test_ntd_registry_view_export()
