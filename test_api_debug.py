import requests
import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

# Test the API with debug information
def test_api_debug():
    # Import the trainer from the API to see what's happening
    try:
        from core.bldr_api import trainer
        print(f"API trainer: {trainer}")
        if trainer:
            print(f"API trainer tools system: {trainer.tools_system}")
            print(f"API trainer tools system type: {type(trainer.tools_system)}")
            if hasattr(trainer.tools_system, 'tool_methods'):
                print(f"API trainer available tools: {list(trainer.tools_system.tool_methods.keys())}")
    except Exception as e:
        print(f"Error importing trainer from API: {e}")
    
    # Get a test token
    token_response = requests.post("http://localhost:8000/token")
    if token_response.status_code != 200:
        print("Failed to get token")
        return
    
    token = token_response.json()["access_token"]
    print(f"Got token: {token}")
    
    # Test the generate_letter endpoint with the correct parameter name
    letter_data = {
        "template_id": "compliance_sp31",
        "recipient": "Test Recipient",
        "sender": "Test Sender",
        "subject": "Test Subject",
        "compliance_details": ["Test detail 1", "Test detail 2"],
        "violations": ["Test violation 1"]
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        "http://localhost:8000/tools/generate_letter",
        headers=headers,
        json=letter_data
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response data: {response.json()}")

if __name__ == "__main__":
    test_api_debug()