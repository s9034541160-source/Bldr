import requests
import json

# Test API call
url = "http://localhost:8000/tools/search_rag_database"
headers = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTc1ODk4NDE1MH0.8g2qkZku01dlEcgho3DX-9VbW_2PVXmCGOOounf-6YY",
    "Content-Type": "application/json"
}
data = {"query": "test", "k": 5}

try:
    response = requests.post(url, headers=headers, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
