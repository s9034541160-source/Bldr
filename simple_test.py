from fastapi import FastAPI, HTTPException, status, BackgroundTasks, WebSocket, WebSocketDisconnect, UploadFile, File, Form, Depends, Request
from fastapi.responses import JSONResponse, Response, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import jwt
import os
import json
import uuid
import time

# Create a simple FastAPI app
app = FastAPI()

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root():
    """Главная страница API"""
    return "<h1>Test Root Endpoint</h1>"

@app.get("/health")
async def health_check():
    """Enhanced health check endpoint"""
    return {"status": "healthy"}

@app.get("/auth/debug")
async def auth_debug():
    """Debug endpoint to check auth configuration"""
    return {"skip_auth": "false"}

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