import requests
import json

# Get token
token_response = requests.post("http://localhost:8000/token")
if token_response.status_code != 200:
    print(f"Failed to get token: {token_response.status_code} - {token_response.text}")
    exit(1)

token_data = token_response.json()
token = token_data["access_token"]
print(f"Got token: {token}")

# Test /ai endpoint
ai_response = requests.post(
    "http://localhost:8000/ai",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    },
    json={
        "prompt": "test"
    }
)

print(f"AI endpoint response: {ai_response.status_code}")
print(f"AI endpoint content: {ai_response.text}")

# Test /bot endpoint with form data
bot_response = requests.post(
    "http://localhost:8000/bot",
    headers={
        "Authorization": f"Bearer {token}",
    },
    data={
        "cmd": "test"
    }
)

print(f"Bot endpoint response: {bot_response.status_code}")
print(f"Bot endpoint content: {bot_response.text}")