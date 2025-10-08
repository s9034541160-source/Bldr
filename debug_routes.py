import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the app
from main import app
from fastapi.routing import APIRoute

# Function to check routes
def check_routes(label):
    print(f"\n{label}:")
    print("Number of routes:", len(app.routes))
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

# Check routes immediately after import
check_routes("After import")

# Let's also check if the functions are defined
try:
    from main import root, health_check, auth_debug
    print("\nFunctions are defined:")
    print("  root:", root)
    print("  health_check:", health_check)
    print("  auth_debug:", auth_debug)
except Exception as e:
    print(f"\nError importing functions: {e}")