import requests
import json

# Test all Pro Tools endpoints
def test_all_pro_tools():
    # Get a test token
    token_response = requests.post("http://localhost:8000/token")
    if token_response.status_code != 200:
        print("Failed to get token")
        return
    
    token = token_response.json()["access_token"]
    print(f"Got token: {token}")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test tools data
    tools_data = {
        "/tools/generate_letter": {
            "template_id": "compliance_sp31",
            "recipient": "Test Recipient",
            "sender": "Test Sender",
            "subject": "Test Subject",
            "compliance_details": ["Test detail 1", "Test detail 2"],
            "violations": ["Test violation 1"]
        },
        "/tools/auto_budget": {
            "project_name": "Test Project",
            "positions": [
                {
                    "code": "01.01.01",
                    "name": "Test Work",
                    "unit": "m2",
                    "quantity": 100,
                    "unit_cost": 5000
                }
            ],
            "regional_coefficients": {},
            "overheads_percentage": 15,
            "profit_percentage": 10
        },
        "/tools/generate_ppr": {
            "project_name": "Test Project",
            "project_code": "TP001",
            "location": "Test Location",
            "client": "Test Client",
            "works_seq": [
                {
                    "name": "Foundation",
                    "description": "Foundation work",
                    "duration": 30,
                    "deps": [],
                    "resources": {}
                }
            ]
        }
    }
    
    # Test each tool
    for endpoint, data in tools_data.items():
        print(f"\nTesting {endpoint}...")
        response = requests.post(
            f"http://localhost:8000{endpoint}",
            headers=headers,
            json=data
        )
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Status: {result.get('status', 'Unknown')}")
            if result.get('status') == 'success':
                print("✅ Tool working correctly")
            else:
                print(f"❌ Tool failed: {result.get('error', 'Unknown error')}")
        else:
            print(f"❌ Tool failed with status {response.status_code}")
            try:
                print(f"Error: {response.json()}")
            except:
                print("Could not parse error response")

if __name__ == "__main__":
    test_all_pro_tools()