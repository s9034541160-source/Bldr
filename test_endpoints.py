import requests
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import app
from fastapi.routing import APIRoute

# Print all registered routes
print("Number of routes:", len(app.routes))
print("Registered endpoints:")
for route in app.routes:
    if isinstance(route, APIRoute):
        print(f"  {route.path}")

# Check for specific endpoints
specific_endpoints = ["/", "/health", "/auth/debug"]
print("\nChecking for specific endpoints:")
for endpoint in specific_endpoints:
    found = any(route.path == endpoint for route in app.routes if isinstance(route, APIRoute))
    status = "✓" if found else "✗"
    print(f"  {status} {endpoint} - {'Registered' if found else 'Not registered'}")

# Wait a moment for the server to fully start
time.sleep(5)

# Test the endpoints
try:
    # Test the root endpoint
    response = requests.get("http://localhost:8000/")
    print(f"Root endpoint status: {response.status_code}")
    print(f"Root endpoint content: {response.text[:100]}...")
except Exception as e:
    print(f"Error accessing root endpoint: {e}")

try:
    # Test the docs endpoint
    response = requests.get("http://localhost:8000/docs")
    print(f"Docs endpoint status: {response.status_code}")
except Exception as e:
    print(f"Error accessing docs endpoint: {e}")

try:
    # Test the health endpoint
    response = requests.get("http://localhost:8000/health")
    print(f"Health endpoint status: {response.status_code}")
    print(f"Health endpoint content: {response.text}")
except Exception as e:
    print(f"Error accessing health endpoint: {e}")

try:
    # Test the auth debug endpoint
    response = requests.get("http://localhost:8000/auth/debug")
    print(f"Auth debug endpoint status: {response.status_code}")
    print(f"Auth debug endpoint content: {response.text}")
except Exception as e:
    print(f"Error accessing auth debug endpoint: {e}")