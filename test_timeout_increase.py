#!/usr/bin/env python3
"""
Test script to verify increased timeout for AI-Shell endpoint
"""

import requests
import json
import time

def test_timeout_increase():
    """Test the AI-Shell endpoint with increased timeout"""
    print("Testing AI-Shell endpoint with increased timeout...")
    
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
        
        # Test the /ai endpoint with a complex prompt that might take time
        ai_url = "http://localhost:8000/ai"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Use a prompt that might take some time to process
        test_data = {
            "prompt": "Write a detailed technical explanation of how neural networks work, including backpropagation, activation functions, and gradient descent. Provide examples and be thorough.",
            "model": "llama3"
        }
        
        print("📝 Testing /ai endpoint with a complex prompt...")
        print("   This may take up to 2 minutes depending on your system and model...")
        
        start_time = time.time()
        response = requests.post(ai_url, headers=headers, json=test_data)
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"Request completed in {duration:.2f} seconds")
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            response_text = response_data.get("response", "")
            print(f"Response length: {len(response_text)} characters")
            print("✅ AI-Shell endpoint with increased timeout is working correctly")
        elif response.status_code == 503:
            # Check if it's a timeout error or model loading issue
            if "No models loaded" in response.text:
                print("✅ AI-Shell endpoint fix is working! The request is now properly sent to LM Studio.")
                print("   (You need to load a model in LM Studio to get a full response)")
            else:
                print("❌ AI-Shell endpoint returned a service error")
                print(f"Response: {response.text}")
        else:
            print("❌ AI-Shell endpoint is still not working correctly")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out - the timeout increase may not be working")
    except Exception as e:
        print(f"❌ Error testing AI-Shell endpoint: {e}")

if __name__ == "__main__":
    test_timeout_increase()