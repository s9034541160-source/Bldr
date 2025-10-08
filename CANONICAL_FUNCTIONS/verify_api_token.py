# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: verify_api_token
# Основной источник: C:\Bldr\core\bldr_api.py
# Дубликаты (для справки):
#   - C:\Bldr\main.py
#   - C:\Bldr\backend\main.py
#================================================================================
from fastapi import HTTPException, status, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import jwt
import os

# Security scheme for header-based auth
security = HTTPBearer(auto_error=False)

def verify_api_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    token_query: Optional[str] = Query(None, alias="token")
):
    """Verify API token for protected endpoints - supports both header and query parameter auth"""
    
    # Check if authentication should be skipped
    skip_auth = os.getenv("SKIP_AUTH", "false").lower() == "true"
    if skip_auth:
        return {"sub": "anonymous", "skip_auth": True}
    
    # Try to get token from header first (standard way)
    token = None
    if credentials and credentials.credentials:
        token = credentials.credentials
    
    # Fallback: try to get token from query parameter (for SSE)
    if not token and token_query:
        token = token_query
    
    # If no token found anywhere
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token provided (neither in Authorization header nor in query parameter)",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify the token
    try:
        SECRET_KEY = os.getenv("SECRET_KEY", "bldr_empire_secret_key_change_in_production")
        ALGORITHM = os.getenv("ALGORITHM", "HS256")
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )