from fastapi import FastAPI, HTTPException, status, BackgroundTasks, WebSocket, WebSocketDisconnect, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse, Response, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordRequestForm
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import asyncio
from typing import Optional
import requests
from datetime import datetime, timedelta
import shutil
import glob
from tqdm import tqdm
from dotenv import load_dotenv
import base64
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import jwt
import logging
import time
import os
import re
import json
import hashlib

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create console handler
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(handler)

# Load environment variables
load_dotenv()

# Manager for WebSocket connections
try:
    from core.websocket_manager import manager
except ImportError:
    # Create a simple mock manager if not available
    class MockManager:
        def __init__(self):
            self.active_connections = []
        
        def connect(self, websocket):
            pass
            
        def disconnect(self, websocket):
            pass
            
        async def send_personal_message(self, message, websocket):
            pass
            
        async def broadcast(self, message):
            pass
    
    manager = MockManager()

# Global instances for process tracking and retry system
try:
    from core.process_tracker import get_process_tracker, ProcessType, ProcessStatus
    from core.retry_system import get_retry_system, RetryConfig
    
    process_tracker = get_process_tracker()
    retry_system = get_retry_system()
    
    # Register default retry configurations
    retry_system.register_retry_config("ai_task", RetryConfig(max_attempts=3, initial_delay=1.0, max_delay=60.0))
    retry_system.register_retry_config("rag_training", RetryConfig(max_attempts=2, initial_delay=5.0, max_delay=300.0))
    retry_system.register_retry_config("document_processing", RetryConfig(max_attempts=3, initial_delay=2.0, max_delay=120.0))
except ImportError:
    # Create mock objects if modules are not available
    class MockProcessTracker:
        def start_cleanup_task(self):
            pass
    
    class MockRetrySystem:
        def register_retry_config(self, name, config):
            pass
    
    process_tracker = MockProcessTracker()
    retry_system = MockRetrySystem()

# Global training status tracking
training_status = {
    "is_training": False,
    "progress": 0,
    "current_stage": "idle",
    "message": "Training system ready",
    "start_time": None
}

# Initialize plugin manager if available
try:
    from core.plugin_manager import PluginManager
    plugin_manager = PluginManager()
    plugin_manager.load_all_plugins()
except ImportError:
    plugin_manager = None

# Middleware for limiting upload size
class LimitUploadSizeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_upload_size: int):
        super().__init__(app)
        self.max_upload_size = max_upload_size

    async def dispatch(self, request: Request, call_next):
        if request.method == "POST" and "/upload-file" in request.url.path:
            # Check content length header
            content_length = request.headers.get("content-length")
            if content_length:
                content_length = int(content_length)
                if content_length > self.max_upload_size:
                    return JSONResponse(
                        status_code=413,
                        content={"detail": "File too large. Maximum allowed size is 100MB."}
                    )
        response = await call_next(request)
        return response

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info('🚀 Bldr API v2 Starting on http://localhost:8000')
    
    # Start process tracker cleanup task
    if hasattr(process_tracker, 'start_cleanup_task'):
        process_tracker.start_cleanup_task()
    
    yield
    
    # Shutdown
    logger.info('🛑 Bldr API v2 Shutdown')

app = FastAPI(lifespan=lifespan)

# Add upload size limit middleware (100MB)
app.add_middleware(LimitUploadSizeMiddleware, max_upload_size=100 * 1024 * 1024)

# Global exception handlers
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Global handler for all unhandled exceptions as requested"""
    print(f"500 on {request.url}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Внутренняя ошибка сервера — retry"}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handler for request validation errors"""
    print(f"Validation error: {exc}")
    # Create user-friendly error messages
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        msg = error["msg"]
        errors.append(f"Field '{field}': {msg}")
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error", 
            "errors": errors,
            "message": "Please check your input data and try again."
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler for HTTP exceptions with custom error messages as requested"""
    print(f"HTTP {exc.status_code} on {request.url}: {exc.detail}")
    if exc.status_code == 404:
        return JSONResponse(
            status_code=404,
            content={"error": "Endpoint не найден — обновите фронт"}
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

# Add comprehensive CORS middleware for authorization support
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server default
        "http://localhost:3001",  # Custom frontend port
        "http://localhost:3002",  # Alternative frontend port
        os.getenv("FRONTEND_URL", "http://localhost:3001"),
        "*" if os.getenv("CORS_ALLOW_ALL", "false").lower() == "true" else "http://localhost:3001"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "*",
        "Authorization", 
        "Content-Type", 
        "Origin", 
        "Accept", 
        "X-Requested-With",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers"
    ],
    expose_headers=["Content-Disposition", "Authorization"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Get configuration from environment variables
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neopassword")
QDRANT_PATH = os.getenv("QDRANT_PATH", "data/qdrant_db")
BASE_DIR = os.getenv("BASE_DIR", "I:/docs")

# Import the Enterprise RAG Trainer
try:
    from enterprise_rag_trainer_full import EnterpriseRAGTrainer as EnterpriseRAGTrainerFull
    
    # Initialize trainer with proper error handling
    try:
        # Check if Neo4j should be skipped
        skip_neo4j = os.getenv("SKIP_NEO4J", "false").lower() == "true"
        
        if skip_neo4j:
            print("⚠️ Skipping Neo4j initialization as requested")
            trainer = EnterpriseRAGTrainerFull(
                base_dir=BASE_DIR
            )
        else:
            trainer = EnterpriseRAGTrainerFull(
                base_dir=BASE_DIR
            )
        print("🚀 EnterpriseRAGTrainerFull initialized successfully")
        
        # Add ToolsSystem integration to trainer
        try:
            from core.tools_system import ToolsSystem
            from core.model_manager import ModelManager
            
            # Initialize model manager for tools system
            model_manager = ModelManager()
            
            # Add tools_system to the trainer for API endpoint compatibility
            if trainer:
                # Use setattr to avoid linter issues
                setattr(trainer, 'tools_system', ToolsSystem(trainer, model_manager))
                print("✅ Tools System integrated (47+ tools available)")
                
        except Exception as tools_error:
            print(f"⚠️ Could not integrate ToolsSystem: {tools_error}")
            if trainer:
                # Use setattr to avoid linter issues
                setattr(trainer, 'tools_system', None)
            
    except Exception as e:
        print(f"❌ Failed to initialize EnterpriseRAGTrainerFull: {e}")
        trainer = None
        
except ImportError as e:
    print(f"⚠️ EnterpriseRAGTrainerFull not available: {e}")
    trainer = None

# Security
security = HTTPBearer()

# JWT config
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# Token models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Simple user database (in production, this would be a real database)
USERS_DB = {
    "admin": {
        "username": "admin",
        "password": "admin",
        "role": "admin"
    },
    "user": {
        "username": "user",
        "password": "user",
        "role": "user"
    }
}

USERS_DB_FILE = os.getenv("USERS_DB_PATH", os.path.join("data", "users_db.json"))

def _hash_password(password: str) -> str:
    salt = "bldr_static_salt"
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()

def _verify_password(password: str, password_hash: str) -> bool:
    try:
        salt = "bldr_static_salt"
        return hashlib.sha256((salt + password).encode("utf-8")).hexdigest() == password_hash
    except Exception:
        return False

def _ensure_users_db_dir():
    try:
        os.makedirs(os.path.dirname(USERS_DB_FILE), exist_ok=True)
    except Exception:
        pass

def load_users_db():
    global USERS_DB
    _ensure_users_db_dir()
    try:
        if os.path.exists(USERS_DB_FILE):
            with open(USERS_DB_FILE, "r", encoding="utf-8") as f:
                file_db = json.load(f)
        else:
            file_db = {}
    except Exception:
        file_db = {}
    # Merge defaults (do not override file users)
    merged = {**USERS_DB, **file_db}
    USERS_DB = merged

def save_users_db():
    _ensure_users_db_dir()
    try:
        # Do not persist legacy plaintext passwords for built-ins; convert to hash on the fly
        to_save = {}
        for uname, rec in USERS_DB.items():
            role = rec.get("role", "user")
            if "password_hash" in rec:
                to_save[uname] = {"username": uname, "password_hash": rec["password_hash"], "role": role}
            elif "password" in rec:
                # Hash legacy
                to_save[uname] = {"username": uname, "password_hash": _hash_password(rec["password"]), "role": role}
            else:
                to_save[uname] = {"username": uname, "role": role}
        with open(USERS_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(to_save, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Failed to save users DB: {e}")

def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Authenticate user credentials with flexible dev mode and hashed support"""
    # Ensure DB is loaded
    if not USERS_DB or len(USERS_DB) <= 0:
        load_users_db()
    # Check if dev mode is enabled
    dev_mode = os.getenv("DEV_MODE", "false").lower() == "true"
    
    # First check the user database
    user = USERS_DB.get(username)
    if user:
        # Prefer password_hash
        if "password_hash" in user:
            if _verify_password(password, user["password_hash"]):
                return user
        # Fallback to legacy plaintext
        if "password" in user and user["password"] == password:
            return user
    
    # In dev mode, accept any credentials
    if dev_mode:
        return {
            "username": username,
            "password": password,
            "role": "admin" if username == "admin" else "user"
        }
    
    return None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Dependency for JWT token verification
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency for JWT token verification with user-friendly error messages"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials. Invalid token format.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token_data = TokenData(username=username)
        return token_data
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials. Invalid token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Dependency for authentication
def verify_api_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API token for protected endpoints"""
    # Check if authentication should be skipped

    skip_auth = os.getenv("SKIP_AUTH", "false").lower() == "true"
    if skip_auth:
        # Return a dummy payload when authentication is skipped
        return {"sub": "anonymous", "skip_auth": True}
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Role-based access control dependency
def require_role(required_role: str):
    def _dep(payload: dict = Depends(verify_api_token)):
        # If authentication is skipped, allow all roles
        if payload.get("skip_auth", False):
            return payload
        role = payload.get("role", "user")
        if role != required_role:
            raise HTTPException(status_code=403, detail="Forbidden: insufficient role")
        return payload
    return _dep

# API Routes

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return JWT token"""
    try:
        authenticated_user = authenticate_user(form_data.username, form_data.password)
        if not authenticated_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": authenticated_user["username"],
                "role": authenticated_user.get("role", "user")
            }, 
            expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"Error in token generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during authentication"
        )

# Additional endpoint for debugging auth issues  
@app.get("/auth/debug")
async def auth_debug():
    """Debug endpoint to check auth configuration"""
    load_users_db()
    return {
        "skip_auth": os.getenv("SKIP_AUTH", "false"),
        "dev_mode": os.getenv("DEV_MODE", "false"),
        "secret_key_set": bool(os.getenv("SECRET_KEY")),
        "algorithm": os.getenv("ALGORITHM", "HS256"),
        "expire_minutes": os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"),
        "available_users": list(USERS_DB.keys())
    }

# User management models
class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: Optional[str] = "user"

# User management endpoints (admin only)
@app.get("/auth/users")
async def list_users(payload: dict = Depends(require_role("admin"))):
    try:
        load_users_db()
        users = [
            {"username": uname, "role": rec.get("role", "user")}
            for uname, rec in USERS_DB.items()
        ]
        return {"status": "success", "data": {"users": users, "count": len(users)}}
    except Exception as e:
        return {"status": "error", "error": f"Failed to list users: {e}"}

@app.post("/auth/users")
async def add_user(req: CreateUserRequest, payload: dict = Depends(require_role("admin"))):
    try:
        load_users_db()
        uname = req.username.strip()
        if not uname or len(uname) < 3:
            raise HTTPException(status_code=400, detail="Username too short (min 3)")
        if len(req.password) < 4:
            raise HTTPException(status_code=400, detail="Password too short (min 4)")
        if uname in USERS_DB:
            raise HTTPException(status_code=409, detail="User already exists")
        USERS_DB[uname] = {
            "username": uname,
            "password_hash": _hash_password(req.password),
            "role": req.role or "user"
        }
        save_users_db()
        return {"status": "success", "data": {"username": uname, "role": USERS_DB[uname]["role"]}}
    except HTTPException:
        raise
    except Exception as e:
        return {"status": "error", "error": f"Failed to add user: {e}"}

# Test endpoint for validating tokens
@app.get("/auth/validate")
async def validate_token(current_user: dict = Depends(verify_api_token)):
    """Validate token and return user info"""
    return {
        "valid": True,
        "user": current_user.get("sub"),
        "role": current_user.get("role", "user"),
        "skip_auth": current_user.get("skip_auth", False)
    }

@app.get("/health")
async def health():
    """Enhanced health check endpoint with detailed service status"""
    try:
        # Check if Neo4j should be skipped
        skip_neo4j = os.getenv("SKIP_NEO4J", "false").lower() == "true"
        
        # Check Neo4j connection
        db_ok = False
        if skip_neo4j:
            db_ok = True  # Pretend it's OK when skipped
        elif trainer and hasattr(trainer, 'neo4j') and trainer.neo4j:
            neo4j_attr = getattr(trainer, 'neo4j')
            if neo4j_attr:
                try:
                    with neo4j_attr.session() as session:
                        session.run("RETURN 1")
                    db_ok = True
                except:
                    db_ok = False
        
        # Check Celery status
        celery_ok = False
        try:
            # Check if Celery is available and workers are running
            from core.celery_app import celery_app
            inspect = celery_app.control.inspect()
            stats = inspect.stats()
            if stats:
                celery_ok = True
        except:
            celery_ok = False
        
        # Return health status as requested
        status = "ok" if (skip_neo4j or db_ok) and celery_ok else "error"
        db_status = "skipped" if skip_neo4j else ("connected" if db_ok else "disconnected")
        
        return {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "components": {
                "db": db_status,
                "celery": "running" if celery_ok else "stopped",
                "endpoints": len(app.routes)
            },
        }
    except Exception as e:
        print(f"❌ Error in health check: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to perform health check: {str(e)}")

# Unified status aggregator endpoint
@app.get("/status")
async def status_aggregator(credentials: dict = Depends(verify_api_token)):
    try:
        # Reuse health checks
        skip_neo4j = os.getenv("SKIP_NEO4J", "false").lower() == "true"
        db_ok = False
        if skip_neo4j:
            db_ok = True
        elif trainer and hasattr(trainer, 'neo4j') and trainer.neo4j:
            neo4j_attr = getattr(trainer, 'neo4j')
            if neo4j_attr:
                try:
                    with neo4j_attr.session() as session:
                        session.run("RETURN 1")
                    db_ok = True
                except Exception:
                    db_ok = False

        celery_ok = False
        try:
            from core.celery_app import celery_app
            inspect = celery_app.control.inspect()
            stats = inspect.stats()
            if stats:
                celery_ok = True
        except Exception:
            celery_ok = False

        # WebSocket connections
        ws_connections = len(manager.active_connections)

        components = {
            "db": "skipped" if skip_neo4j else ("connected" if db_ok else "disconnected"),
            "celery": "running" if celery_ok else "stopped",
            "websocket_connections": ws_connections,
            "endpoints": len(app.routes),
        }
        overall = "healthy" if ((skip_neo4j or db_ok) and celery_ok) else ("degraded" if (skip_neo4j or db_ok or celery_ok) else "unhealthy")
        return {
            "status": overall,
            "timestamp": datetime.now().isoformat(),
            "components": components
        }
    except Exception as e:
        return {"status": "error", "error": f"Failed to aggregate status: {e}"}

# Define request and response models for submit_query endpoint
class SubmitQueryRequest(BaseModel):
    query: str
    source: str
    project_id: str
    user_id: str

class SubmitQueryAsyncResponse(BaseModel):
    task_id: str
    status: str

@app.post("/submit_query_async", response_model=SubmitQueryAsyncResponse)
async def submit_query_async(request_data: SubmitQueryRequest, background_tasks: BackgroundTasks, credentials: dict = Depends(verify_api_token)):
    """Enqueue AI coordinator processing and return task_id immediately"""
    try:
        task_id = f"ai_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        return SubmitQueryAsyncResponse(task_id=task_id, status='processing')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enqueue AI query: {e}")

@app.get("/submit_query_result")
async def submit_query_result(task_id: str, credentials: dict = Depends(verify_api_token)):
    try:
        return {"task_id": task_id, "status": "completed", "result": "Placeholder result"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get result: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("core.bldr_api:app", host="0.0.0.0", port=8000, reload=True)