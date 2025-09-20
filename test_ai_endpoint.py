import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the API token
api_token = os.getenv('API_TOKEN')
print(f"API Token: {api_token[:20]}..." if api_token else "No API token found")

# Test the AI endpoint
if api_token:
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'prompt': 'Привет, расскажи о себе',
        'model': 'deepseek/deepseek-r1-0528-qwen3-8b'
    }
    
    try:
        response = requests.post(
            'http://localhost:8000/ai',
            headers=headers,
            json=data,
            timeout=30
        )
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"Task ID: {response_data.get('task_id')}")
            print(f"Status: {response_data.get('status')}")
            print(f"Message: {response_data.get('message')}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error making request: {e}")
else:
    print("Cannot test without API token")