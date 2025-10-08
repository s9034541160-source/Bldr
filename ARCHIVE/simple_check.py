import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")

# Простая проверка API
try:
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.get("http://localhost:8000/health", timeout=5)
    print(f"API Status: {response.status_code}")
    
    # Тест поиска
    response = requests.post(
        "http://localhost:8000/query",
        json={"query": "ГОСТ", "k": 1},
        headers=headers,
        timeout=10
    )
    print(f"Search Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        results = data.get('results', [])
        print(f"Results found: {len(results)}")
    
except Exception as e:
    print(f"Error: {e}")