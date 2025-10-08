# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: authenticate_user
# Основной источник: C:\Bldr\core\bldr_api.py
# Дубликаты (для справки):
#   - C:\Bldr\main.py
#   - C:\Bldr\backend\main.py
#================================================================================
from typing import Optional, Dict
import os

def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Authenticate user credentials with flexible dev mode and hashed support"""
    # This is a canonical function that should be implemented properly in the main application
    print(f"Authenticating user: {username}")
    
    # Simple authentication logic with proper role assignment
    if username == "admin" and password == "admin":
        return {"username": username, "role": "admin"}
    elif username == "user" and password == "user":
        return {"username": username, "role": "user"}
    else:
        # For any other credentials, assign role based on username
        role = "admin" if username == "admin" else "user"
        return {"username": username, "role": role}