import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import the authenticate_user function directly from backend
from main import authenticate_user

print("=== Direct Authentication Test ===")

# Test admin user
print("Testing admin user...")
result = authenticate_user("admin", "admin")
print(f"Admin result: {result}")

# Test user user
print("Testing user user...")
result = authenticate_user("user", "user")
print(f"User result: {result}")

# Test invalid credentials
print("Testing invalid credentials...")
result = authenticate_user("invalid", "invalid")
print(f"Invalid result: {result}")