import requests
import json

# Test the Pro Tools in more detail
def test_tools_detailed():
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
    
    print("Testing tools endpoint...")
    response = requests.post(
        "http://localhost:8000/tools/generate_letter",
        headers=headers,
        json=letter_data
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response headers: {response.headers}")
    print(f"Response data: {response.json()}")
    
    # Also test the tools system directly
    print("\nTesting tools system validation...")
    try:
        from core.tools_system import validate_tool_parameters
        result = validate_tool_parameters("generate_letter", letter_data)
        print(f"Validation result: {result}")
    except Exception as e:
        print(f"Validation error: {e}")

if __name__ == "__main__":
    test_tools_detailed()