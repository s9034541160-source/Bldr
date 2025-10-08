import jwt
import os
from datetime import datetime, timedelta

# JWT config from bldr_api.py
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

print(f"SECRET_KEY: {SECRET_KEY}")
print(f"ALGORITHM: {ALGORITHM}")
print(f"ACCESS_TOKEN_EXPIRE_MINUTES: {ACCESS_TOKEN_EXPIRE_MINUTES}")

# Create a test token
def create_access_token(data: dict):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Test token creation
try:
    test_token = create_access_token(data={"sub": "test_user"})
    print(f"Test token created: {test_token}")
    
    # Test token verification
    payload = jwt.decode(test_token, SECRET_KEY, algorithms=[ALGORITHM])
    print(f"Token payload: {payload}")
    print("Token verification successful!")
except Exception as e:
    print(f"Error: {e}")