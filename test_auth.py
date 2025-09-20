import requests
import json
import time

print("=== Bldr API Authentication Test ===")

# Wait a moment for the server to fully initialize
time.sleep(2)

# Test the token endpoint
url = "http://localhost:8000/token"
data = {
    "username": "admin",
    "password": "admin"
}

print("Testing token generation...")
try:
    response = requests.post(url, data=data)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        token_data = response.json()
        print(f"Token Data: {token_data}")
        access_token = token_data.get("access_token")
        if access_token:
            print("✅ Token generation successful!")
            
            # Test using the token to access a protected endpoint
            headers = {"Authorization": f"Bearer {access_token}"}
            health_url = "http://localhost:8000/health"
            print("\nTesting health endpoint with token...")
            health_response = requests.get(health_url, headers=headers)
            print(f"Health Status Code: {health_response.status_code}")
            if health_response.status_code == 200:
                print("✅ Health endpoint access successful!")
                print(f"Health Data: {health_response.json()}")
            else:
                print(f"❌ Health endpoint access failed: {health_response.text}")
        else:
            print("❌ No access token in response")
    else:
        print(f"❌ Token generation failed: {response.text}")
except Exception as e:
    print(f"❌ Token generation error: {e}")