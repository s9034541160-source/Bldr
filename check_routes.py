import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the app
from main import app
from fastapi.routing import APIRoute

# Print all registered routes
print("Number of routes:", len(app.routes))
print("Registered endpoints:")
routes_found = []
for route in app.routes:
    if isinstance(route, APIRoute):
        print(f"  {route.path}")
        routes_found.append(route.path)

# Check for specific endpoints
specific_endpoints = ["/", "/health", "/auth/debug"]
print("\nChecking for specific endpoints:")
for endpoint in specific_endpoints:
    found = endpoint in routes_found
    status = "✓" if found else "✗"
    print(f"  {status} {endpoint} - {'Registered' if found else 'Not registered'}")