#!/usr/bin/env python3
"""
Simple test script for AI endpoint
"""

import requests
import json
import os

# Configuration
API_BASE = 'http://localhost:8000'

def get_auth_token():
    """Get authentication token for API access"""
    try:
        # Try to get token from environment variable
        token = os.getenv('API_TOKEN')
        if token:
            return token
            
        # If no env token, try to generate one (for testing only)
        response = requests.post(f"{API_BASE}/token")
        if response.status_code == 200:
            return response.json().get('access_token')
        else:
            print(f"⚠️  Could not get auth token: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"⚠️  Error getting auth token: {str(e)}")
        return None

def test_ai_request():
    """Test the AI request"""
    print("🚀 Testing AI Request")
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("❌ No authentication token available")
        return
    
    # Make AI request
    try:
        payload = {
            "prompt": "Say hello in Russian.",
            "model": "llama3.1"
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        print("📤 Sending AI request...")
        response = requests.post(f"{API_BASE}/ai", json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ AI Request Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ Failed to start AI request: {response.status_code} - {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")

if __name__ == "__main__":
    test_ai_request()