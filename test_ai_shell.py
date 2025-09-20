#!/usr/bin/env python3
"""
Test script to verify AI Shell functionality
"""

import requests
import json

def test_ai_shell():
    """Test the AI Shell endpoint"""
    base_url = "http://localhost:8000"
    
    # First, get a test token
    print("Getting access token...")
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
    
    # Test AI Shell endpoint
    print("Testing AI Shell endpoint...")
    try:
        ai_data = {
            "prompt": "Hello, how are you?",
            "model": "test_model"
        }
        
        response = requests.post(
            f"{base_url}/ai",
            headers=headers,
            json=ai_data
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.text}")
        
        if response.status_code == 200:
            print("✓ AI Shell endpoint is working!")
            return True
        else:
            print("✗ AI Shell endpoint failed")
            return False
    except Exception as e:
        print(f"✗ Error testing AI Shell endpoint: {e}")
        return False

if __name__ == "__main__":
    test_ai_shell()