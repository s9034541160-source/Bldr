#!/usr/bin/env python3
"""Test real search with СП металлоконструкции"""

import requests
import json

# Test search with real query
url = 'http://localhost:8000/tools/search_rag_database'
headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTc1ODk4NjIzNn0.KRLlJ7N3cmmSK0_g-TNmqJ5WHsGgZXPeFhsrO0pCsY4',
    'Content-Type': 'application/json'
}
data = {
    'query': 'СП металлоконструкции',
    'k': 5,
    'threshold': 0.3,
    'use_sbert': False,
    'include_metadata': False,
    'search_mode': 'semantic'
}

try:
    response = requests.post(url, headers=headers, json=data)
    print(f'Status: {response.status_code}')
    result = response.json()
    print(f'Results count: {len(result.get("data", {}).get("results", []))}')
    print(f'Total found: {result.get("data", {}).get("total_found", 0)}')
    print(f'Result type: {result.get("result_type", "NOT SET")}')
    print(f'Result table: {len(result.get("result_table", []))} rows')
    if result.get('data', {}).get('results'):
        print('First result:', result['data']['results'][0])
    else:
        print('No results found!')
    print('Full response keys:', list(result.keys()))
    if 'result_table' in result:
        print('Result table sample:', result['result_table'][:2] if result['result_table'] else 'Empty')
except Exception as e:
    print(f'Error: {e}')
