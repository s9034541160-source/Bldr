import requests
import json

# Test accessing projects API at /api/projects
url = "http://localhost:8000/api/projects"

try:
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")