#!/usr/bin/env python3
"""
Test the /submit_query API endpoint
"""

import os
import sys
import requests
import json
import time

# Set environment variable for OpenAI API key (not actually needed for LM Studio)
os.environ["OPENAI_API_KEY"] = "not-needed"

def test_submit_query_api():
    """Test the /submit_query API endpoint"""
    print("Testing /submit_query API endpoint...")
    
    # API endpoint
    url = "http://localhost:8000/submit_query"
    
    # Test data
    test_data = {
        "query": "Анализ LSR на СП31 + письмо",
        "source": "frontend",
        "user_id": "test_user",
        "project_id": None
    }
    
    # Headers (we'll need to get a token first)
    try:
        # First get a token
        token_url = "http://localhost:8000/token"
        token_response = requests.post(token_url)
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
        print(f"📝 Testing with query: {test_data['query']}")
        
        # Send request to /submit_query
        print("🚀 Sending request to /submit_query...")
        start_time = time.time()
        
        response = requests.post(url, headers=headers, data=json.dumps(test_data))
        
        end_time = time.time()
        
        print(f"✅ Response received in {end_time - start_time:.2f} seconds")
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print("📋 Response data:")
            print(json.dumps(response_data, ensure_ascii=False, indent=2))
            
            # Check if we have the expected fields
            expected_fields = ["plan", "responses", "final", "files"]
            for field in expected_fields:
                if field in response_data:
                    print(f"✅ Field '{field}' present in response")
                else:
                    print(f"❌ Field '{field}' missing from response")
                    
            print("🎉 API test completed successfully!")
        else:
            print(f"❌ API returned error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_submit_query_api()