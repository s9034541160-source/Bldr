import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

def test_token_generation():
    """Test token generation endpoint"""
    print("Testing token generation...")
    try:
        response = requests.post(f"{BASE_URL}/token")
        if response.status_code == 200:
            token_data = response.json()
            print(f"✅ Token generated successfully: {token_data}")
            return token_data.get("access_token")
        else:
            print(f"❌ Failed to generate token: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error generating token: {e}")
        return None

def test_pro_tools_endpoint(token, endpoint, data):
    """Test a pro tools endpoint with authentication"""
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}
    print(f"Testing {endpoint}...")
    try:
        response = requests.post(f"{BASE_URL}{endpoint}", json=data, headers=headers)
        if response.status_code == 200:
            print(f"✅ {endpoint} successful: {response.json()}")
            return True
        else:
            print(f"❌ {endpoint} failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing {endpoint}: {e}")
        return False

def main():
    print("Testing Pro Tools Authentication...")
    
    # Test token generation
    token = test_token_generation()
    if not token:
        print("Cannot proceed without token")
        return
    
    # Test a simple pro tools endpoint
    test_data = {
        "template": "compliance_sp31",
        "recipient": "Test Recipient",
        "sender": "Test Sender",
        "subject": "Test Subject"
    }
    
    test_pro_tools_endpoint(token, "/tools/generate_letter", test_data)

if __name__ == "__main__":
    main()