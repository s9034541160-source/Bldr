#!/usr/bin/env python3
"""
Test LM Studio connection with requests
"""

import requests
import json

def test_lm_studio():
    """Test LM Studio connection"""
    url = "http://localhost:1234/v1/chat/completions"
    
    payload = {
        "messages": [
            {
                "role": "user",
                "content": "Say hello in one word"
            }
        ],
        "temperature": 0.1,
        "max_tokens": 100
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_lm_studio()