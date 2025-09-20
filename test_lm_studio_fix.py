#!/usr/bin/env python3
"""
Test script to verify LM Studio fix for /ai endpoint
"""

import requests
import json
import time

def test_lm_studio_fix():
    """Test the /ai endpoint with proper LM Studio integration"""
    print("Testing LM Studio fix for /ai endpoint...")
    
    # First get a token
    token_url = "http://localhost:8000/token"
    try:
        token_response = requests.post(token_url)
        if token_response.status_code != 200:
            print(f"❌ Failed to get access token: {token_response.status_code}")
            return
            
        token_data = token_response.json()
        token = token_data.get("access_token")
        
        if not token:
            print("❌ Failed to get access token")
            return
            
        print("✅ Got access token")
        
        # Test the /ai endpoint
        ai_url = "http://localhost:8000/ai"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        test_data = {
            "prompt": "Say hello in one word",
            "model": "llama3"  # or whatever model you have loaded in LM Studio
        }
        
        print("📝 Testing /ai endpoint with prompt: 'Say hello in one word'")
        
        response = requests.post(ai_url, headers=headers, json=test_data)
        
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ /ai endpoint is working correctly with LM Studio")
        elif response.status_code == 503:
            # Check if the error is about no model loaded (which means our fix is working)
            if "No models loaded" in response.text:
                print("✅ /ai endpoint fix is working! The request is now properly sent to LM Studio.")
                print("   (You need to load a model in LM Studio to get a full response)")
            else:
                print("❌ /ai endpoint is still not working correctly")
        else:
            print("❌ /ai endpoint is still not working correctly")
            
    except Exception as e:
        print(f"❌ Error testing /ai endpoint: {e}")

if __name__ == "__main__":
    test_lm_studio_fix()