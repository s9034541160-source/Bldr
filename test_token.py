#!/usr/bin/env python3
"""
Test script to verify token generation and authentication
"""
import requests
import json

# Test the token endpoint
url = "http://localhost:8000/token"
data = {
    "username": "admin",
    "password": "admin"
}

try:
    response = requests.post(url, data=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")


# Configuration
API_BASE = 'http://localhost:8000'
TEST_QUERY = "привет. расскажи о себе. что знаешь, что умеешь?"

def test_token_generation():
    """Test token generation endpoint"""
    print("Testing token generation...")
    try:
        response = requests.post(f'{API_BASE}/token')
        if response.status_code == 200:
            token_data = response.json()
            print(f"✅ Token generated successfully: {token_data.get('access_token')[:20]}...")
            return token_data.get('access_token')
        else:
            print(f"❌ Token generation failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Token generation error: {e}")
        return None

def test_submit_query(token):
    """Test submit_query endpoint with token"""
    print(f"\nTesting submit_query with token...")
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        payload = {
            "query": TEST_QUERY,
            "source": "frontend",
            "user_id": "test_user"
        }
        
        response = requests.post(f'{API_BASE}/submit_query', json=payload, headers=headers)
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Query submitted successfully: {json.dumps(data, ensure_ascii=False, indent=2)}")
            return True
        else:
            print(f"❌ Query submission failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Query submission error: {e}")
        return False

def main():
    """Main test function"""
    print("=== Bldr API Authentication Test ===")
    
    # Test token generation
    token = test_token_generation()
    if not token:
        print("Cannot proceed without token")
        return
    
    # Test submit query
    success = test_submit_query(token)
    
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Some tests failed!")

if __name__ == "__main__":
    main()