import requests
import json

# Test the projects endpoint
try:
    response = requests.get("http://localhost:8000/api/projects/")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Try to create a project
    project_data = {
        "name": "Test Project",
        "code": "TP001",
        "location": "Test Location",
        "status": "planned"
    }
    
    response = requests.post(
        "http://localhost:8000/api/projects/",
        headers={"Content-Type": "application/json"},
        data=json.dumps(project_data)
    )
    print(f"Create Project Status Code: {response.status_code}")
    print(f"Create Project Response: {response.text}")
    
except Exception as e:
    print(f"Error: {e}")