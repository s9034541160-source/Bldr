#!/usr/bin/env python3
"""
Тест API для НТД
"""
import requests
import json
import time

def test_ntd_api():
    """Тестируем API для НТД"""
    base_url = "http://localhost:8000/api/ntd"
    
    print("TESTING NTD API")
    print("=" * 50)
    
    # 1. Проверка здоровья
    print("1. Health Check...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # 2. Статистика НТД
    print("2. NTD Statistics...")
    try:
        response = requests.get(f"{base_url}/statistics")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            stats = response.json()
            print(f"   Total NTD: {stats.get('total_ntd', 0)}")
            print(f"   Total Documents: {stats.get('total_documents', 0)}")
            print(f"   Total Relations: {stats.get('total_relations', 0)}")
            print(f"   By Type: {stats.get('by_type', [])}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # 3. Поиск НТД
    print("3. Search NTD...")
    try:
        response = requests.get(f"{base_url}/search?q=СП&limit=5")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            results = response.json()
            print(f"   Found {len(results)} results")
            for result in results[:3]:
                print(f"   - {result.get('canonical_id', 'N/A')} ({result.get('document_type', 'N/A')})")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # 4. Сеть связей
    print("4. NTD Network...")
    try:
        response = requests.get(f"{base_url}/network")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            network = response.json()
            print(f"   Nodes: {len(network.get('nodes', []))}")
            print(f"   Edges: {len(network.get('edges', []))}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    print("NTD API test completed!")

if __name__ == "__main__":
    test_ntd_api()
