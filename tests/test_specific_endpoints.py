# Test defining specific endpoints from main.py
from fastapi import FastAPI, Depends
from fastapi.responses import HTMLResponse
import os
from datetime import datetime

# Import the functions from main.py
from CANONICAL_FUNCTIONS.load_users_db import load_users_db
from CANONICAL_FUNCTIONS.verify_api_token import verify_api_token

app = FastAPI()

# Test root endpoint
@app.get("/", response_class=HTMLResponse)
async def root():
    """Главная страница API"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>SuperBuilder Tools API</title>
    </head>
    <body>
        <h1>Test</h1>
    </body>
    </html>
    '''

# Test health endpoint
@app.get("/health")
async def health_check():
    """Enhanced health check endpoint"""
    try:
        components = {"api": "running", "endpoints": len(app.routes), "timestamp": datetime.now().isoformat()}
        return {"status": "healthy", "service": "SuperBuilder Tools API", "timestamp": datetime.now().isoformat(), "version": "1.0.0", "components": components}
    except Exception as e:
        return {"status": "error", "error": str(e), "timestamp": datetime.now().isoformat()}

# Test auth debug endpoint
@app.get("/auth/debug")
async def auth_debug():
    """Debug endpoint to check auth configuration"""
    load_users_db()
    return {"skip_auth": os.getenv("SKIP_AUTH", "false"), "dev_mode": os.getenv("DEV_MODE", "false"), "secret_key_set": bool(os.getenv("SECRET_KEY")), "algorithm": os.getenv("ALGORITHM", "HS256"), "expire_minutes": os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"), "available_users": []}

# Test auth validate endpoint
@app.get("/auth/validate")
async def validate_token(current_user: dict = Depends(verify_api_token)):
    """Validate token and return user info"""
    return {"valid": True, "user": current_user.get("sub"), "role": current_user.get("role", "user"), "skip_auth": current_user.get("skip_auth", False)}

print(f"Number of routes: {len(app.routes)}")
endpoint_paths = [getattr(route, 'path', str(route)) for route in app.routes]
print("Registered endpoints:")
for path in sorted(endpoint_paths):
    print(f"  {path}")