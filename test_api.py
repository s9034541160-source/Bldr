import requests
import json

# Test the AI chat endpoint
url = "http://localhost:8000/api/ai/chat"
headers = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXIiLCJleHAiOjE3ODk2MzAxNzd9.C7XrKk-5MCKdl7fJFSk0n_f-4cILYljt0ILcCpphdaY",
    "Content-Type": "application/json"
}
data = {
    "message": "привет. расскажи о себе. что знаешь, что умеешь?",
    "context_search": True,
    "max_context": 3
}

try:
    response = requests.post(url, headers=headers, json=data)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")