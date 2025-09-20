#!/usr/bin/env python3
"""
Final test for the API
"""

import requests
import json

def test_api():
    """Test the API endpoints"""
    base_url = "http://localhost:8000"
    
    # Get token
    print("Getting access token...")
    token_response = requests.post(f"{base_url}/token")
    token_data = token_response.json()
    token = token_data.get("access_token")
    
    if not token:
        print("❌ Failed to get access token")
        return
        
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("✅ Got access token")
    
    # Test health endpoint
    print("Testing health endpoint...")
    health_response = requests.get(f"{base_url}/health")
    print(f"Health status: {health_response.status_code}")
    print(f"Health data: {health_response.json()}")
    
    # Test submit_query endpoint
    print("Testing submit_query endpoint...")
    query_data = {
        "query": "Анализ LSR на СП31 + письмо",
        "source": "frontend",
        "user_id": "test_user"
    }
    
    submit_response = requests.post(
        f"{base_url}/submit_query",
        headers=headers,
        data=json.dumps(query_data)
    )
    
    print(f"Submit query status: {submit_response.status_code}")
    if submit_response.status_code == 200:
        response_data = submit_response.json()
        print("✅ Submit query successful")
        print(f"Response: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
    else:
        print(f"❌ Submit query failed: {submit_response.text}")

if __name__ == "__main__":
    test_api()