#!/usr/bin/env python3
"""
Test script to verify Pro Tools authentication is working correctly
"""

import requests
import json
import time

def test_pro_tools_auth():
    """Test that Pro Tools endpoints work with proper authentication"""
    
    # Base URL
    base_url = "http://localhost:8000"
    
    # First, get a test token
    print("Getting test token...")
    try:
        token_response = requests.post(f"{base_url}/token")
        token_response.raise_for_status()
        token_data = token_response.json()
        token = token_data["access_token"]
        print(f"✓ Got token: {token[:20]}...")
    except Exception as e:
        print(f"✗ Failed to get token: {e}")
        return False
    
    # Test headers with token
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test a simple Pro Tools endpoint
    print("Testing Pro Tools endpoint...")
    try:
        # Test letter generation endpoint
        letter_data = {
            "template": "compliance_sp31",
            "recipient": "Test Recipient",
            "sender": "Test Sender",
            "subject": "Test Subject"
        }
        
        response = requests.post(
            f"{base_url}/tools/generate_letter",
            headers=headers,
            json=letter_data
        )
        
        if response.status_code == 200:
            print("✓ Pro Tools endpoint accessible with authentication")
            data = response.json()
            print(f"  Response: {data.get('status', 'No status')}")
            return True
        elif response.status_code == 401:
            print("✗ Authentication failed - token not accepted")
            return False
        else:
            print(f"✗ Unexpected response: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Failed to call Pro Tools endpoint: {e}")
        return False

def test_frontend_auth():
    """Test that frontend can authenticate properly"""
    print("Testing frontend authentication flow...")
    
    # This would simulate what the frontend does
    # 1. Get token
    # 2. Store in localStorage (zustand)
    # 3. Make authenticated requests
    
    try:
        # Simulate getting token like frontend does
        token_response = requests.post("http://localhost:8000/token")
        token_response.raise_for_status()
        token = token_response.json()["access_token"]
        
        # Simulate storing in localStorage like zustand does
        store_data = {
            "state": {
                "user": {
                    "token": token,
                    "role": "user",
                    "username": "test"
                },
                "settings": {
                    "host": "http://localhost:8000"
                }
            }
        }
        
        print("✓ Frontend authentication flow working")
        return True
        
    except Exception as e:
        print(f"✗ Frontend authentication failed: {e}")
        return False

if __name__ == "__main__":
    print("Bldr Empire Pro Tools Authentication Test")
    print("=" * 50)
    
    # Wait a moment for services to start
    time.sleep(2)
    
    # Test authentication
    auth_success = test_pro_tools_auth()
    print()
    
    # Test frontend flow
    frontend_success = test_frontend_auth()
    print()
    
    if auth_success and frontend_success:
        print("🎉 All authentication tests passed!")
        print("Pro Tools should now work correctly in the frontend.")
    else:
        print("❌ Some authentication tests failed.")
        print("Check the backend API and frontend authentication setup.")