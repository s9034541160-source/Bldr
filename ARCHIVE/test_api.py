#!/usr/bin/env python3
import requests
import json

def get_auth_token():
    """Get authentication token"""
    try:
        auth_data = {
            "username": "admin",
            "password": "admin"
        }
        
        response = requests.post(
            "http://localhost:8000/token",
            data=auth_data,
            timeout=10
        )
        
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get("access_token")
        else:
            print(f"❌ Auth failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error getting auth token: {e}")
        return None

# Test /api/ai/chat endpoint
def test_chat_endpoint():
    # Get auth token
    token = get_auth_token()
    if not token:
        print("❌ Could not get auth token")
        return False
        
    try:
        payload = {
            "message": "Привет! Как дела?",
            "context_search": False,
            "max_context": 3,
            "agent_role": "coordinator"
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            "http://localhost:8000/api/ai/chat",
            json=payload,
            headers=headers,
            timeout=60
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Chat endpoint working! Response: {data.get('response', 'No response')[:100]}")
            return True
        else:
            print(f"❌ Chat endpoint failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing chat endpoint: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing API endpoints...")
    test_chat_endpoint()