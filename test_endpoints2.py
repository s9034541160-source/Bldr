import requests
import time

# Wait a moment for the server to fully start
time.sleep(2)

# Test various endpoints
endpoints = [
    "/",
    "/health",
    "/auth/debug",
    "/debug/health",
    "/debug/health-status",
    "/debug/health-check",
    "/status",
    "/debug/status",
    "/routes"
]

print("Testing endpoints:")
for endpoint in endpoints:
    try:
        response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
        print(f"  {endpoint}: {response.status_code}")
    except Exception as e:
        print(f"  {endpoint}: Error - {e}")