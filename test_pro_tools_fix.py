import requests
import json

# Test the Pro Tools fix
def test_pro_tools_fix():
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
    
    if response.status_code == 200:
        print("✅ Pro Tools fix is working!")
    else:
        print("❌ Pro Tools fix failed")

if __name__ == "__main__":
    test_pro_tools_fix()