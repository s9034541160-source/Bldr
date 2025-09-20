import requests
import json

# Test the conversational query feature
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXIiLCJleHAiOjE3NTgwNjMwNzh9.YXZO6X93H9A949c377NzAEhp0kZ2TKmN4EJvu8Znxog'
}

# Test data with a conversational query
data = {
    'query': 'привет. расскажи о себе. что знаешь, что умеешь?',
    'source': 'test',
    'user_id': 'test_user'
}

try:
    response = requests.post('http://localhost:8000/submit_query', headers=headers, json=data)
    print(f'Status Code: {response.status_code}')
    print(f'Response: {response.text}')
    
    # Parse the response to check if it's natural language or JSON
    response_data = response.json()
    result = response_data.get('result', '')
    
    # Check if the result contains JSON (indicating it's still returning JSON)
    if 'plan' in result or 'complexity' in result or result.startswith('План выполнения:'):
        print('❌ Issue still exists: Response is still returning JSON instead of natural language')
    else:
        print('✅ Fixed: Response is returning natural language text')
        
except Exception as e:
    print(f'Error: {e}')