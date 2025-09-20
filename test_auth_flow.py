#!/usr/bin/env python3
"""
Test script to verify the complete authentication flow for AI Shell
"""

import requests
import json

def test_auth_flow():
    """Test the complete authentication flow"""
    base_url = "http://localhost:8000"
    
    print("=== Testing Authentication Flow ===")
    
    # 1. Test token generation
    print("\n1. Testing token generation...")
    try:
        token_response = requests.post(f"{base_url}/token")
        token_response.raise_for_status()
        token_data = token_response.json()
        token = token_data["access_token"]
        print(f"✓ Token generated successfully")
        print(f"  Token: {token[:30]}...")
    except Exception as e:
        print(f"✗ Failed to generate token: {e}")
        return False
    
    # 2. Test AI endpoint with valid token
    print("\n2. Testing AI endpoint with valid token...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    ai_data = {
        "prompt": "Test prompt for AI Shell",
        "model": "test_model"
    }
    
    try:
        response = requests.post(
            f"{base_url}/ai",
            headers=headers,
            json=ai_data
        )
        
        if response.status_code == 200:
            print("✓ AI endpoint works with valid token")
            response_data = response.json()
            print(f"  Response: {response_data}")
        else:
            print(f"✗ AI endpoint failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error testing AI endpoint: {e}")
        return False
    
    # 3. Test AI endpoint with invalid token
    print("\n3. Testing AI endpoint with invalid token...")
    invalid_headers = {
        "Authorization": "Bearer invalid_token",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{base_url}/ai",
            headers=invalid_headers,
            json=ai_data
        )
        
        if response.status_code == 401:
            print("✓ AI endpoint correctly rejects invalid token")
            response_data = response.json()
            print(f"  Error message: {response_data.get('detail', 'No detail')}")
        else:
            print(f"⚠ Unexpected response for invalid token: {response.status_code}")
    except Exception as e:
        print(f"Error testing invalid token: {e}")
    
    # 4. Test AI endpoint without token
    print("\n4. Testing AI endpoint without token...")
    no_auth_headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{base_url}/ai",
            headers=no_auth_headers,
            json=ai_data
        )
        
        if response.status_code == 403:
            print("✓ AI endpoint correctly rejects requests without token")
        else:
            print(f"⚠ Unexpected response for missing token: {response.status_code}")
    except Exception as e:
        print(f"Error testing missing token: {e}")
    
    print("\n=== Authentication Flow Test Complete ===")
    return True

if __name__ == "__main__":
    test_auth_flow()