import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the API token
api_token = os.getenv('API_TOKEN')
print(f"API Token loaded: {api_token[:20]}..." if api_token else "No API token found")

# Test the /bot endpoint with authentication
if api_token:
    headers = {'Authorization': f'Bearer {api_token}'}
    try:
        response = requests.post(
            'http://localhost:8000/bot',
            data={'cmd': '/help'},
            headers=headers,
            timeout=10
        )
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("Cannot test without API token")