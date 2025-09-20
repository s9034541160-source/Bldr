import requests
import json

try:
    response = requests.get('http://localhost:8000/health', timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Content: {response.text}")
    if response.status_code == 200:
        data = response.json()
        print(f"Health Status: {data.get('status')}")
        print(f"Components: {data.get('components')}")
except Exception as e:
    print(f"Error: {e}")