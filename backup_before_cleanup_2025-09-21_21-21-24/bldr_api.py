from fastapi import FastAPI, HTTPException, status, BackgroundTasks, WebSocket, WebSocketDisconnect, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse, Response, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordRequestForm
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseModel
import asyncio
from typing import Optional
import requests  # For bot calls
from datetime import datetime, timedelta
import shutil
import glob
from tqdm import tqdm  # For progress, but API async so simulate
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

# Optional strong hashing
try:
    import bcrypt  # type: ignore
    _BCRYPT_AVAILABLE = True
except Exception:
    _BCRYPT_AVAILABLE = False


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

# Import slowapi for rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import APScheduler for cron jobs
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

# Import project management API
from core.projects_api import router as projects_router

# Try to import Neo4j with proper error handling
NEO4J_AVAILABLE = False
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Warning: Neo4j not available: {e}")

# Try to import Qdrant with proper error handling
QDRANT_AVAILABLE = False
try:
    from qdrant_client import QdrantClient
    QDRANT_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Warning: Qdrant not available: {e}")

# Load environment variables
load_dotenv()

# Import Sentry for error tracking (if available)
sentry_sdk = None
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    # Initialize Sentry
    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[
                FastApiIntegration(),
            ],
            traces_sample_rate=1.0,
        )
except ImportError:
    logger.info("Sentry not available, skipping error tracking")
    pass

# Import Prometheus for metrics (if available)
prometheus_client = None
Instrumentator = None
try:
    import prometheus_client
    from prometheus_fastapi_instrumentator import Instrumentator
except ImportError:
    logger.info("Prometheus not available, skipping metrics")
    pass

# Import plugin manager
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.plugin_manager import PluginManager

# Import RAG API models
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from rag_api_models import (
    RAGSearchRequest, RAGSearchResponse, RAGSearchResult,
    RAGTrainingRequest, RAGTrainingResponse, RAGStatusResponse,
    AIChatMessage, AIChatResponse,
    DocumentAnalysisRequest, DocumentAnalysisResponse
)

# Import norms updater
from core.norms_updater import NormsUpdater

# Manager for WebSocket connections
# Moved to separate file to avoid circular imports
from core.websocket_manager import manager
from core.process_tracker import get_process_tracker, ProcessType, ProcessStatus
from core.retry_system import get_retry_system, RetryConfig
from core.schemas import ok, err

# Redis for async AI tasks
try:
    import redis  # type: ignore
    _AI_REDIS_AVAILABLE = True
except Exception:
    _AI_REDIS_AVAILABLE = False

# Global instances for process tracking and retry system
process_tracker = get_process_tracker()
retry_system = get_retry_system()

# Register default retry configurations
retry_system.register_retry_config("ai_task", RetryConfig(max_attempts=3, initial_delay=1.0, max_delay=60.0))
retry_system.register_retry_config("rag_training", RetryConfig(max_attempts=2, initial_delay=5.0, max_delay=300.0))
retry_system.register_retry_config("document_processing", RetryConfig(max_attempts=3, initial_delay=2.0, max_delay=120.0))

# Global training status tracking
training_status = {
    "is_training": False,
    "progress": 0,
    "current_stage": "idle",
    "message": "Training system ready",
    "start_time": None
}

# Add imports for the multi-agent system
coordinator_agent = None
specialist_agents_manager = None
try:
    from core.agents.coordinator_agent import CoordinatorAgent
    from core.agents.specialist_agents import SpecialistAgentsManager
    # Initialize the multi-agent system
    coordinator_agent = CoordinatorAgent()
    specialist_agents_manager = SpecialistAgentsManager()
    AGENTS_AVAILABLE = True
    logger.info("✅ Multi-agent system initialized successfully")
except ImportError as e:
    logger.warning(f"Warning: Multi-agent system not available: {e}")
    AGENTS_AVAILABLE = False
except Exception as e:
    logger.warning(f"Warning: Multi-agent system failed to initialize: {e}")
    AGENTS_AVAILABLE = False

# Initialize plugin manager
plugin_manager = PluginManager()
plugin_manager.load_all_plugins()

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

# Optional unified response middleware (backward compatible)
class UnifiedResponseMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        try:
            from core.schemas import should_unify, unify_body
            # Only for JSON
            media = getattr(response, 'media_type', None)
            if not media or 'json' not in str(media).lower():
                return response
            if not should_unify(request):
                return response
            # Extract body (works for JSONResponse)
            body = None
            if hasattr(response, 'body_iterator'):
                chunks = []
                async for chunk in response.body_iterator:
                    chunks.append(chunk)
                raw = b"".join(chunks)
                import json as _json
                try:
                    obj = _json.loads(raw.decode('utf-8'))
                except Exception:
                    return response
                unified = unify_body(obj)
                from fastapi.responses import JSONResponse as _JR
                return _JR(content=unified, status_code=response.status_code)
            return response
        except Exception:
            return response

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize scheduler
scheduler = AsyncIOScheduler(
    jobstores={
        'default': MemoryJobStore()
    },
    executors={
        'default': ThreadPoolExecutor(20)
    },
    job_defaults={
        'coalesce': False,
        'max_instances': 3
    }
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info('🚀 Bldr API v2 Starting on http://localhost:8000')
    
    # Start process tracker cleanup task
    process_tracker.start_cleanup_task()
    
    # Note: Celery worker handles scheduled tasks now
    logger.info("✅ Celery worker will handle scheduled tasks")
    
    yield
    
    # Shutdown
    logger.info('🛑 Bldr API v2 Shutdown')

app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter

# Rate limiting is handled by slowapi middleware
# No custom exception handler needed

# NOTE: Project management routes are now included in the main app (main.py)
# to avoid conflicts when mounting this app under /api/tools
# DO NOT include projects_router here
# app.include_router(projects_router)

# Include Meta-Tools API routes
try:
    from backend.api.meta_tools_api import router as meta_tools_router
    app.include_router(meta_tools_router)
    logger.info("✅ Meta-Tools API подключен")
except ImportError as e:
    logger.warning(f"⚠️ Meta-Tools API недоступен: {e}")

# Include File Analysis Tools API routes
try:
    from backend.api.tools_api import router as tools_router
    app.include_router(tools_router)
    logger.info("✅ Tools API (File Analysis) подключен")
except ImportError as e:
    logger.warning(f"⚠️ Tools API недоступен: {e}")

# Add upload size limit middleware (100MB)
app.add_middleware(LimitUploadSizeMiddleware, max_upload_size=100 * 1024 * 1024)
# Optional unified response middleware (opt-in via ?unify=true or headers)
app.add_middleware(UnifiedResponseMiddleware)

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

# Add Prometheus instrumentation if available
if Instrumentator:
    Instrumentator().instrument(app).expose(app)

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
BASE_DIR = os.getenv("BASE_DIR", "I:/docs")  # Changed default to I:/docs to avoid C: space issues

# Init trainer, neo4j, qdrant (same as trainer)
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import the Enterprise RAG Trainer (latest and most powerful version)
from enterprise_rag_trainer_full import EnterpriseRAGTrainer as EnterpriseRAGTrainerFull
from scripts.fast_bldr_rag_trainer import FastBldrRAGTrainer

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
    print("🚀 EnterpriseRAGTrainerFull initialized successfully - СУПЕР-ПУПЕР-МЕГА-ПАВЕР-ЭНТЕРПРАЙЗ версия!")
    
    # Add Master ToolsSystem integration to Enterprise trainer through adapter
    from core.tools_adapter import get_tools_adapter
    from core.model_manager import ModelManager
    
    # Initialize model manager for tools system
    model_manager = ModelManager()
    
    # Add master tools_system to the trainer through adapter for API endpoint compatibility
    # Use setattr to avoid type checking issues
    if trainer:
        master_tools_adapter = get_tools_adapter(trainer, model_manager)
        setattr(trainer, 'tools_system', master_tools_adapter)
        print("✅ Master Tools System integrated through adapter (47+ tools available)")
    
    # Rebind coordinator with tools system
    try:
        if 'master_tools_adapter' in locals() and master_tools_adapter is not None:
            if coordinator_agent is None:
                from core.agents.coordinator_agent import CoordinatorAgent as _CA
                coordinator_agent = _CA(tools_system=master_tools_adapter)
            else:
                setattr(coordinator_agent, 'tools_system', master_tools_adapter)
            logger.info("🔗 Coordinator connected to Master Tools System")
    except Exception as e:
        logger.warning(f"Could not connect Coordinator to tools system: {e}")
    
    # Initialize fast trainer for speed-optimized processing
    fast_trainer = FastBldrRAGTrainer(
        base_dir=BASE_DIR,
        neo4j_uri=NEO4J_URI,
        neo4j_user=NEO4J_USER,
        neo4j_pass=NEO4J_PASSWORD,
        qdrant_path=QDRANT_PATH
    )
    print("⚡ FastBldrRAGTrainer initialized for fast processing")
except Exception as e:
    print(f"❌ Failed to initialize EnterpriseRAGTrainerFull: {e}")
    trainer = None
    fast_trainer = None

# Initialize norms updater
norms_updater = NormsUpdater()

# Function to run norms update job via Celery
def update_norms_job():
    """Scheduled job to update norms from official sources via Celery"""
    try:
        print("🚀 Starting scheduled norms update job via Celery...")
        # Import Celery task
        from core.celery_norms import update_norms_task
        # Send task to Celery worker
        task = update_norms_task.delay()  # type: ignore
        print(f"✅ Scheduled norms update task sent to Celery: {task.id}")
        return task
    except Exception as e:
        print(f"❌ Error sending scheduled norms update job to Celery: {e}")

# Function to manually trigger norms update
async def manual_update_norms(categories: Optional[List[str]] = None):
    """Manually trigger norms update"""
    try:
        print(f"🚀 Starting manual norms update for categories: {categories or 'all'}")
        results = await norms_updater.update_norms_daily(categories)
        print(f"✅ Manual norms update completed: {results['documents_downloaded']} documents downloaded")
        
        # Process newly downloaded documents
        if trainer and results['documents_downloaded'] > 0:
            print("🔄 Processing newly downloaded documents...")
            # Use getattr to avoid type checking issues
            if hasattr(trainer, 'train'):
                getattr(trainer, 'train')()  # This will process new documents in the norms_db
            print("✅ New documents processed and indexed")
            
        return results
    except Exception as e:
        print(f"❌ Error in manual norms update: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update norms: {str(e)}")

# Security
security = HTTPBearer()

# JWT config
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# User model for authentication
class User(BaseModel):
    username: str
    password: str

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
    },
    # For development - accept any user/pass if DEV_MODE is enabled
    "test": {
        "username": "test",
        "password": "test",
        "role": "user"
    }
}

USERS_DB_FILE = os.getenv("USERS_DB_PATH", os.path.join("data", "users_db.json"))

def _hash_password(password: str) -> str:
    if _BCRYPT_AVAILABLE:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    # Fallback (dev): sha256 with static salt
    salt = "bldr_static_salt"
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()

def _verify_password(password: str, password_hash: str) -> bool:
    try:
        if _BCRYPT_AVAILABLE and password_hash and password_hash.startswith("$2"):
            return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
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

# ===== Async AI task storage =====
_AI_REDIS_URL = os.getenv('REDIS_URL') or os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
_AI_REDIS_CLIENT = None

def _get_ai_redis():
    global _AI_REDIS_CLIENT
    if not _AI_REDIS_AVAILABLE:
        raise RuntimeError('Redis not available for AI tasks')
    if _AI_REDIS_CLIENT is None:
        _AI_REDIS_CLIENT = redis.Redis.from_url(_AI_REDIS_URL, decode_responses=True)
        try:
            _AI_REDIS_CLIENT.ping()
        except Exception as e:
            raise RuntimeError(f'Redis ping failed: {e}')
    return _AI_REDIS_CLIENT

def _ai_task_key(task_id: str) -> str:
    return f"bldr:ai:task:{task_id}"

def _ai_active_set() -> str:
    return "bldr:ai:tasks:active"

def _ai_completed_set() -> str:
    return "bldr:ai:tasks:completed"
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
        return ok(data={"users": users, "count": len(users)})
    except Exception as e:
        return err(f"Failed to list users: {e}")

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
        return ok(data={"username": uname, "role": USERS_DB[uname]["role"]})
    except HTTPException:
        raise
    except Exception as e:
        return err(f"Failed to add user: {e}")

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
    """Enhanced health check endpoint with detailed service status including Celery"""
    try:
        # Check if Neo4j should be skipped
        skip_neo4j = os.getenv("SKIP_NEO4J", "false").lower() == "true"
        
        # Check Neo4j connection
        db_ok = False
        if skip_neo4j:
            db_ok = True  # Pretend it's OK when skipped
        elif NEO4J_AVAILABLE and trainer and hasattr(trainer, 'neo4j'):
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
            # Import Celery app to check status
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
        elif NEO4J_AVAILABLE and trainer and hasattr(trainer, 'neo4j'):
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
        return ok(data={
            "status": overall,
            "timestamp": datetime.now().isoformat(),
            "components": components
        })
    except Exception as e:
        return err(f"Failed to aggregate status: {e}")

# Utility functions with better error messages
def format_ifc_error(error: Exception) -> str:
    """Format IFC-related errors with user-friendly messages"""
    error_str = str(error)
    if "ifcopenshell" in error_str.lower():
        return "Invalid IFC file format. Please check that the file is a valid IFC model."
    elif "corrupted" in error_str.lower() or "invalid" in error_str.lower():
        return "The IFC file appears to be corrupted or invalid. Please try with a different file."
    else:
        return f"Error processing IFC file: {error_str}"

def format_file_error(error: Exception, filename: Optional[str] = None) -> str:
    """Format file-related errors with user-friendly messages"""
    error_str = str(error)
    if "permission" in error_str.lower():
        return "Permission denied. Please check file permissions and try again."
    elif "not found" in error_str.lower() or "no such file" in error_str.lower():
        if filename:
            return f"File not found: {filename}. Please check the file path and try again."
        else:
            return "File not found. Please check the file path and try again."
    elif "too large" in error_str.lower() or "size" in error_str.lower():
        return "File is too large. Maximum allowed size is 100MB."
    else:
        return f"Error processing file: {error_str}"

# API Routes
# NOTE: WebSocket endpoint moved to main.py to avoid conflicts
# All endpoints are now directly in main.py without mounting

# Define request and response models for submit_query endpoint
class SubmitQueryRequest(BaseModel):
    query: str
    source: str
    project_id: str
    user_id: str

# ===== Async AI chat endpoints =====

class SubmitQueryAsyncResponse(BaseModel):
    task_id: str
    status: str

@app.post("/submit_query_async", response_model=SubmitQueryAsyncResponse)
async def submit_query_async(request_data: SubmitQueryRequest, background_tasks: BackgroundTasks, credentials: dict = Depends(verify_api_token)):
    """Enqueue AI coordinator processing and return task_id immediately"""
    try:
        if not _AI_REDIS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Redis not available for async tasks")
        r = _get_ai_redis()
        task_id = f"ai_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        now = datetime.now().isoformat()
        r.set(_ai_task_key(task_id), json.dumps({
            'id': task_id,
            'status': 'pending',
            'stage': 'queued',
            'created_at': now,
            'updated_at': now
        }, ensure_ascii=False))
        r.sadd(_ai_active_set(), task_id)
        # Run background
        background_tasks.add_task(_process_ai_task, task_id, request_data.dict())
        return SubmitQueryAsyncResponse(task_id=task_id, status='processing')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enqueue AI query: {e}")

@app.get("/submit_query_result")
async def submit_query_result(task_id: str, credentials: dict = Depends(verify_api_token)):
    try:
        if not _AI_REDIS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Redis not available")
        r = _get_ai_redis()
        raw = r.get(_ai_task_key(task_id))
        if not raw:
            raise HTTPException(status_code=404, detail="Task not found")
        return json.loads(raw)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get result: {e}")

async def _broadcast_ai(stage: str, status: str, log: str, data: Optional[Dict[str, Any]] = None):
    try:
        payload = {'stage': stage, 'status': status, 'log': log}
        if data is not None:
            payload['data'] = data
        await manager.broadcast(json.dumps(payload, ensure_ascii=False))
    except Exception:
        pass

def _ai_task_update(r, task_id: str, **kwargs):
    raw = r.get(_ai_task_key(task_id))
    task = json.loads(raw) if raw else {'id': task_id}
    changed = False
    for k, v in kwargs.items():
        if v is not None:
            task[k] = v
            changed = True
    if changed:
        task['updated_at'] = datetime.now().isoformat()
        r.set(_ai_task_key(task_id), json.dumps(task, ensure_ascii=False))

def _finalize_ai_task(r, task_id: str, status: str):
    r.srem(_ai_active_set(), task_id)
    r.sadd(_ai_completed_set(), task_id)
    r.expire(_ai_task_key(task_id), 48*3600)

async def _process_ai_task(task_id: str, req: Dict[str, Any]):
    """Background processing for AI query; mirrors submit_query flow but reports progress."""
    r = _get_ai_redis()
    _ai_task_update(r, task_id, status='running', stage='planning')
    await _broadcast_ai('planning', 'running', '🧠 Генерация плана...')
    try:
        class _Tmp(BaseModel):
            query: str
            source: str
            project_id: str
            user_id: str
        request_data = _Tmp(**req)

        if not trainer:
            raise RuntimeError('Trainer not available')
        if hasattr(trainer, 'tools_system') and trainer.tools_system:
            tools_system = trainer.tools_system
        else:
            from core.tools_system import ToolsSystem
            from core.model_manager import ModelManager
            tools_system = ToolsSystem(trainer, ModelManager())

        from core.agents.coordinator_agent import CoordinatorAgent
        from core.agents.specialist_agents import SpecialistAgentsManager
        coordinator = CoordinatorAgent(tools_system=tools_system)
        specialist_manager = SpecialistAgentsManager()

        request_context = {
            "source": request_data.source,
            "project_id": request_data.project_id,
            "user_id": request_data.user_id
        }
        if request_data.source == "tg":
            request_context["channel"] = "telegram"
        elif request_data.source == "shell":
            request_context["channel"] = "ai_shell"
        else:
            request_context["channel"] = "frontend"
        coordinator.set_request_context(request_context)

        plan = coordinator.generate_plan(request_data.query)
        _ai_task_update(r, task_id, stage='executing')
        await _broadcast_ai('executing', 'running', '🔧 Выполнение плана...')
        
        results = specialist_manager.execute_plan(plan, tools_system)
        _ai_task_update(r, task_id, stage='finalizing')
        await _broadcast_ai('finalizing', 'running', '📝 Формирование ответа...')
        
        # Fallback: if no results or errors only, do a quick RAG search
        try:
            if (not results or all((rr.get('status') == 'error') for rr in (results if isinstance(results, list) else []))) and tools_system:
                sr = tools_system.execute_tool('search_rag_database', query=request_data.query, k=3)
                if isinstance(results, list):
                    results.append({'tool': 'search_rag_database', 'result': sr, 'status': (sr.get('status') if isinstance(sr, dict) else 'completed')})
                else:
                    results = [{'tool': 'search_rag_database', 'result': sr, 'status': (sr.get('status') if isinstance(sr, dict) else 'completed')}]
        except Exception as _e:
            logger.warning(f"Async fallback RAG failed: {_e}")

        # Generate actionable final response with sources
        try:
            final_text = coordinator.generate_final_response(request_data.query, plan or {}, results if isinstance(results, list) else [], 0)
        except Exception as _e:
            logger.warning(f"generate_final_response failed: {_e}")
            final_text = coordinator.generate_response(request_data.query).get('response', '')

        data = {
            "query": request_data.query,
            "plan": plan,
            "execution_results": results,
            "final_response": final_text,
            "status": "completed"
        }
        _ai_task_update(r, task_id, status='completed', result=data)
        _finalize_ai_task(r, task_id, 'completed')
        await _broadcast_ai('completed', 'completed', '✅ Готово', data)
    except Exception as e:
        _ai_task_update(r, task_id, status='error', error=str(e))
        _finalize_ai_task(r, task_id, 'error')
        await _broadcast_ai('error', 'error', f"❌ Ошибка: {e}")

@app.post("/submit_query")
async def submit_query_endpoint(request_data: SubmitQueryRequest, background_tasks: BackgroundTasks, credentials: dict = Depends(verify_api_token)):
    """Submit a query to the multi-agent system for processing"""
    try:
        # Check if trainer is available
        if not trainer:
            raise HTTPException(status_code=500, detail="Trainer not available")
            
        # Get tools system - either from trainer or create a new one
        if hasattr(trainer, 'tools_system') and trainer.tools_system:
            tools_system = trainer.tools_system
        else:
            # Create a new tools system if not available
            from core.tools_system import ToolsSystem
            from core.model_manager import ModelManager
            model_manager = ModelManager()
            tools_system = ToolsSystem(trainer, model_manager)
            
        # Import the multi-agent system components
        from core.agents.coordinator_agent import CoordinatorAgent
        from core.agents.specialist_agents import SpecialistAgentsManager
        
        # Initialize the multi-agent system with the tools system
        coordinator = CoordinatorAgent(tools_system=tools_system)
        specialist_manager = SpecialistAgentsManager()
        
        # Set request context for proper response delivery and conversation history
        request_context = {
            "source": request_data.source,
            "project_id": request_data.project_id,
            "user_id": request_data.user_id
        }
        
        # Add channel information based on source
        if request_data.source == "tg":
            request_context["channel"] = "telegram"
        elif request_data.source == "shell":
            request_context["channel"] = "ai_shell"
        else:
            request_context["channel"] = "frontend"
        
        coordinator.set_request_context(request_context)
        
        # Generate execution plan using the coordinator
        print(f"🧠 Generating execution plan for query: {request_data.query}")
        plan = coordinator.generate_plan(request_data.query)
        print(f"📋 Plan generated: {plan}")
        
        # Execute plan with specialist agents using the tools system
        print("🏃 Executing plan with specialist agents...")
        results = specialist_manager.execute_plan(plan, tools_system)
        print(f"✅ Plan executed. Results: {results}")
        
        # Generate final natural language response using the coordinator
        print("📝 Generating final response...")
        final_response = coordinator.generate_response(request_data.query)
        print(f"📄 Final response generated: {final_response}")
        
        # Prepare the response with proper structure
        response_data = {
            "query": request_data.query,
            "plan": plan,
            "execution_results": results,
            "final_response": final_response,
            "status": "completed"
        }
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/processes")
async def list_processes(
    process_type: Optional[str] = None,
    status: Optional[str] = None,
    credentials: dict = Depends(verify_api_token)
):
    """List all tracked processes with optional filtering"""
    try:
        # Convert string parameters to enums if provided
        process_type_enum = None
        status_enum = None
        
        if process_type:
            try:
                process_type_enum = ProcessType(process_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid process_type: {process_type}")
        
        if status:
            try:
                status_enum = ProcessStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        processes = process_tracker.list_processes(process_type=process_type_enum, status=status_enum)
        return {"processes": processes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list processes: {str(e)}")

@app.get("/processes/{process_id}")
async def get_process_status(
    process_id: str,
    credentials: dict = Depends(verify_api_token)
):
    """Get status of a specific process"""
    try:
        process_info = process_tracker.get_process(process_id)
        if not process_info:
            raise HTTPException(status_code=404, detail=f"Process {process_id} not found")
        
        return {"process": process_info}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get process status: {str(e)}")

@app.post("/processes/{process_id}/cancel")
async def cancel_process(
    process_id: str,
    credentials: dict = Depends(verify_api_token)
):
    """Cancel a running process"""
    try:
        success = process_tracker.cancel_process(process_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Process {process_id} not found or already completed")
        
        # Also cancel any scheduled retries
        retry_system.cancel_retry(process_id)
        
        return {"status": "success", "message": f"Process {process_id} cancelled"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel process: {str(e)}")

@app.get("/processes/types")
async def get_process_types(credentials: dict = Depends(verify_api_token)):
    """Get list of available process types"""
    try:
        types = [ptype.value for ptype in ProcessType]
        return {"process_types": types}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get process types: {str(e)}")

@app.get("/processes/statuses")
async def get_process_statuses(credentials: dict = Depends(verify_api_token)):
    """Get list of available process statuses"""
    try:
        statuses = [status.value for status in ProcessStatus]
        return {"process_statuses": statuses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get process statuses: {str(e)}")

class AICall(BaseModel):
    prompt: str
    model: str = os.getenv("DEFAULT_MODEL", "deepseek/deepseek-r1-0528-qwen3-8b")
    # Multimedia support for Telegram bot
    image_data: Optional[str] = None  # Base64 encoded image
    voice_data: Optional[str] = None  # Base64 encoded voice
    document_data: Optional[str] = None  # Base64 encoded document
    document_name: Optional[str] = None  # Document filename

# Plugin models
class PluginConfig(BaseModel):
    service: str
    credentials: Dict[str, Any]

class WebhookRegistration(BaseModel):
    event_type: str
    callback_url: str
    secret: Optional[str] = None

# Tool execution models
class ToolExecutionRequest(BaseModel):
    name: str
    args: Dict[str, Any]

# Image analysis models
class ImageAnalysisRequest(BaseModel):
    image_base64: str
    type: str = "full"

# TTS models
class TTSRequest(BaseModel):
    text: str
    provider: Optional[str] = None  # 'silero' | 'edge' | 'elevenlabs'
    voice: Optional[str] = None
    language: Optional[str] = None
    format: Optional[str] = None  # 'mp3' | 'ogg'

# Train request model
class TrainRequest(BaseModel):
    custom_dir: Optional[str] = None
    fast_mode: bool = False


@app.get("/api/training/status")
async def training_status_endpoint(credentials: dict = Depends(verify_api_token)):
    """Get training status"""
    global training_status
    
    try:
        if trainer:
            # Use global training status
            status_response = {
                "status": "success" if training_status["current_stage"] != "error" else "error",
                "is_training": training_status["is_training"],
                "mode": training_status.get("mode", "normal"),
                "progress": training_status["progress"],
                "current_stage": training_status["current_stage"],
                "message": training_status["message"]
            }
            
            # Add elapsed time if training is active
            if training_status["start_time"] and training_status["is_training"]:
                elapsed = int(time.time() - training_status["start_time"])
                status_response["elapsed_seconds"] = elapsed
                
            return status_response
        else:
            return {
                "status": "error",
                "is_training": False,
                "progress": 0,
                "current_stage": "unavailable",
                "message": "Trainer not initialized"
            }
    except Exception as e:
        return {
            "status": "error",
            "is_training": False,
            "progress": 0,
            "current_stage": "error",
            "message": f"Error checking training status: {str(e)}"
        }

# Query request model
class QueryRequest(BaseModel):
    query: str
    k: int = 4
    category: Optional[str] = None




async def run_ai_with_updates(task_id: str, request_data: AICall):
    """Run AI request with periodic status updates"""
    import json
    try:
        import requests
        import os
        import time
        from threading import Thread, Event
        
        # Send initial update
        await send_stage_update(task_id, "AI request started", 0)
        
        # LM Studio endpoint - using the same pattern as other parts of the system
        lm_studio_url = os.getenv("LLM_BASE_URL", "http://localhost:1234")
        endpoint = f"{lm_studio_url}/v1/chat/completions"
        
        # Check if this is a coordinator role request by looking at the model or prompt context
        is_coordinator_request = (
            "coordinator" in request_data.model.lower() or 
            "координатор" in request_data.prompt.lower() or
            "Выступая в роли" in request_data.prompt and "координатор" in request_data.prompt.lower()
        )
        
        # If this is a coordinator request, use the multi-agent system
        if is_coordinator_request and AGENTS_AVAILABLE:
            try:
                # Import the multi-agent system components
                from core.agents.coordinator_agent import CoordinatorAgent
                
                # Initialize the coordinator agent with proper system context
                coordinator = CoordinatorAgent(lm_studio_url=lm_studio_url)
                
                # Extract the actual query from the prompt (removing role context)
                actual_query = request_data.prompt
                if "Выступая в роли" in actual_query:
                    # Extract query after the role context
                    parts = actual_query.split(": ", 1)
                    if len(parts) > 1:
                        actual_query = parts[1]
            
                # Generate natural language response using the coordinator
                print(f"🧠 Generating response for query: {actual_query}")
                await send_stage_update(task_id, "Generating response", 20)
                natural_language_response = coordinator.generate_response(actual_query)
                print(f"📋 Response generated: {natural_language_response}")
                
                # Return the natural language response
                response_data = {
                    "status": "completed",
                    "result": natural_language_response,
                    "error": None
                }
            except Exception as e:
                error_msg = f"Coordinator agent error: {str(e)}"
                response_data = {
                    "status": "error",
                    "result": None,
                    "error": error_msg
                }
                logger.error(error_msg)
            # Send the final update
            await send_stage_update(task_id, "Task completed", 100, data=json.dumps(response_data))
        else:
            # Prepare payload
            payload = {
                "model": request_data.model,
                "messages": [{"role": "user", "content": request_data.prompt}],
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            # Send request to LM Studio
            response = requests.post(endpoint, json=payload)
            
            # Process the response
            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                response_data = {
                    "status": "completed",
                    "result": content,
                    "error": None
                }
            else:
                error_msg = response.text
                response_data = {
                    "status": "error",
                    "result": None,
                    "error": error_msg
                }
                logger.error(error_msg)
            # Send the final update
            await send_stage_update(task_id, "Task completed", 100, data=json.dumps(response_data))

    except Exception as e:
        error_msg = f"Unexpected error during AI request: {str(e)}"
        logger.error(error_msg)
        await send_stage_update(task_id, "Task failed", 100, data=json.dumps({
            "status": "error",
            "result": None,
            "error": error_msg
        }))

# File upload models
class FileUploadResponse(BaseModel):
    filename: str
    file_path: str
    size: int
    status: str

# Function to send stage updates via WebSocket
async def send_stage_update(stage: str, log: str, progress: int = 0, data: str = "", status: str = "processing"):
    message = json.dumps({
        "stage": stage,
        "log": log,
        "progress": progress,
        "data": data,
        "status": status
    })
    await manager.broadcast(message)

# Enhanced training function with real-time updates
async def run_training_with_updates(custom_dir: Optional[str] = None, fast_mode: bool = False):
    global training_status
    
    try:
        mode = "fast" if fast_mode else "normal"
        print(f"🚀 Starting {mode} training process with custom_dir={custom_dir}")
        
        # Update global status
        training_status["is_training"] = True
        training_status["mode"] = mode
        training_status["progress"] = 0
        training_status["current_stage"] = "initializing"
        training_status["message"] = "⚡ Быстрая валидация документа..." if fast_mode else "Начальная валидация документа..."
        training_status["start_time"] = time.time()
        
        # Send initial update
        await send_stage_update("1/14", "Начальная валидация документа...", 0)
        
        # Run actual training in a separate thread to avoid blocking the event loop
        if fast_mode and fast_trainer:
            print(f"⚡ Using FAST training mode for improved performance")
            
            # Get current event loop reference
            current_loop = asyncio.get_running_loop()
            
            # Define update callback function for fast mode
            def update_callback(stage: str, log: str, progress: int = 0):
                # Update global status
                training_status["current_stage"] = stage
                training_status["message"] = log
                training_status["progress"] = progress
                
                # Schedule the update asynchronously using the saved loop reference
                try:
                    asyncio.run_coroutine_threadsafe(
                        send_stage_update(stage, log, progress), 
                        current_loop
                    )
                except Exception as e:
                    logger.error(f"Error sending stage update: {str(e)}")
                
            # Run fast training
            if custom_dir:
                print(f"⚡ Running FAST training with custom directory: {custom_dir}")
                if hasattr(fast_trainer, 'base_dir'):
                    original_base_dir = getattr(fast_trainer, 'base_dir')
                    setattr(fast_trainer, 'base_dir', custom_dir)
                    await asyncio.to_thread(fast_trainer.fast_train, update_callback)
                    setattr(fast_trainer, 'base_dir', original_base_dir)
            else:
                print(f"⚡ Running FAST training with default directory")
                await asyncio.to_thread(fast_trainer.fast_train, update_callback)
                
        elif trainer:
            # Get current event loop reference
            current_loop = asyncio.get_running_loop()
            
            # Define update callback function that can be called from sync context
            def update_callback(stage: str, log: str, progress: int = 0):
                # Update global status
                training_status["current_stage"] = stage
                training_status["message"] = log
                training_status["progress"] = progress
                
                # Schedule the update asynchronously using the saved loop reference
                try:
                    asyncio.run_coroutine_threadsafe(
                        send_stage_update(stage, log, progress), 
                        current_loop
                    )
                except Exception as e:
                    logger.error(f"Error sending stage update: {str(e)}")
            
            # If custom directory is provided, temporarily override the base_dir
            if custom_dir:
                if hasattr(trainer, 'base_dir') and hasattr(trainer, 'train'):
                    original_base_dir = getattr(trainer, 'base_dir')
                    setattr(trainer, 'base_dir', Path(custom_dir))
                    await asyncio.to_thread(getattr(trainer, 'train'), max_files=None)
                    # Restore original base_dir
                    setattr(trainer, 'base_dir', original_base_dir)
            else:
                if hasattr(trainer, 'train'):
                    await asyncio.to_thread(getattr(trainer, 'train'), max_files=None)
        else:
            training_status["is_training"] = False
            training_status["current_stage"] = "error"
            training_status["message"] = "Trainer not available"
            await send_stage_update("error", "Trainer not available", 0)
            return
        
        # Update final status
        training_status["is_training"] = False
        training_status["progress"] = 100
        training_status["current_stage"] = "completed"
        training_status["message"] = "🎉 Обработка документа завершена успешно"
        
        # Send completion message
        await send_stage_update("complete", "🎉 Обработка документа завершена успешно", 100)
        
    except Exception as e:
        # Update error status
        training_status["is_training"] = False
        training_status["current_stage"] = "error"
        training_status["message"] = f"Ошибка во время обучения: {str(e)}"
        
        await send_stage_update("error", f"Ошибка во время обучения: {str(e)}", 0)

@app.post("/train")
async def train_endpoint(request: Request, background_tasks: BackgroundTasks, train_data: TrainRequest, credentials: dict = Depends(verify_api_token)):
    # Start training in background with real-time updates
    background_tasks.add_task(run_training_with_updates, train_data.custom_dir, train_data.fast_mode)
    
    mode_message = "(FAST MODE - 5-10x faster, lightweight processing)" if train_data.fast_mode else "(14 stages symbiotism processing)"
    return {
        "status": "Train started background", 
        "message": f"Training started {mode_message}... logs via WebSocket", 
        "custom_dir": train_data.custom_dir,
        "fast_mode": train_data.fast_mode
    }

@app.post("/ai")
async def ai_shell_endpoint(request: Request, request_data: AICall, credentials: dict = Depends(verify_api_token)):
    # Use the new async AI processor for truly non-blocking requests
    from core.async_ai_processor import get_ai_processor
    
    ai_processor = get_ai_processor()
    task_id = f"ai_task_{int(time.time())}_{id(request_data)}"
    
    # Submit request with multimedia support
    task_result = await ai_processor.submit_ai_request(
        task_id=task_id,
        prompt=request_data.prompt,
        model=request_data.model,
        image_data=request_data.image_data,
        voice_data=request_data.voice_data,
        document_data=request_data.document_data,
        document_name=request_data.document_name
    )
    
    return {
        "status": "processing",
        "message": "AI request queued for async processing. Use WebSocket or /ai/status/{task_id} for updates.",
        "task_id": task_id,
        "model": request_data.model,
        "estimated_time": "1-30 minutes"
    }

@app.get("/ai/status/{task_id}")
async def get_ai_task_status_endpoint(task_id: str, credentials: dict = Depends(verify_api_token)):
    """Get status of a specific AI task"""
    from core.async_ai_processor import get_ai_processor
    
    ai_processor = get_ai_processor()
    task_result = ai_processor.get_task_status(task_id)
    
    if not task_result:
        raise HTTPException(status_code=404, detail="Task not found")
    
    response = {
        "task_id": task_id,
        "status": task_result.status,
        "stage": task_result.stage,
        "progress": task_result.progress,
        "created_at": task_result.created_at
    }
    
    if task_result.result:
        response["result"] = task_result.result
        
    if task_result.error:
        response["error"] = task_result.error
    
    return response

@app.get("/ai/tasks")
async def list_ai_tasks_endpoint(credentials: dict = Depends(verify_api_token)):
    """List all active AI tasks"""
    from core.async_ai_processor import get_ai_processor
    
    ai_processor = get_ai_processor()
    tasks = ai_processor.list_active_tasks()
    
    return {
        "active_tasks": len(tasks),
        "max_concurrent": ai_processor.max_concurrent_tasks,
        "tasks": tasks
    }

@app.get("/metrics")
async def metrics_endpoint(request: Request):
    """Prometheus metrics endpoint"""
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
    except ImportError:
        return JSONResponse(content={"error": "Prometheus not available"}, status_code=503)

@app.get("/metrics-json")
async def metrics_json_endpoint(request: Request):
    """JSON metrics endpoint for frontend"""
    try:
        # Return sample metrics data in the format expected by the frontend
        return JSONResponse(content={
            "total_chunks": 10000,
            "avg_ndcg": 0.95,
            "coverage": 0.97,
            "conf": 0.99,
            "viol": 99,
            "entities": {
                "ORG": 3500,
                "MONEY": 2800,
                "PERCENT": 1200,
                "WORK": 1500,
                "TECH": 2000
            }
        })
    except Exception as e:
        return JSONResponse(content={"error": f"Failed to fetch metrics: {str(e)}"}, status_code=503)

@app.post("/db")
async def db_query(request: Request, cypher: str, credentials: dict = Depends(require_role("admin"))):
    if not NEO4J_AVAILABLE:
        return {"cypher": cypher, "records": [], "error": "Neo4j not available"}
        
    if trainer and hasattr(trainer, 'neo4j'):
        neo4j_attr = getattr(trainer, 'neo4j')
        if neo4j_attr:
            try:
                with neo4j_attr.session() as session:
                    result = session.run(cypher)  # type: ignore
                    records = [dict(record) for record in result]
                return {"cypher": cypher, "records": records}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    else:
        return {"cypher": cypher, "records": [], "error": "Neo4j driver not initialized"}

@app.post("/bot")
async def bot_cmd(request: Request, cmd: str = Form(...), credentials: dict = Depends(verify_api_token)):
    """
    Send command to Telegram bot with proper configuration checks
    """
    # Check if Telegram bot is properly configured
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not telegram_token or telegram_token == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        return {
            "cmd": cmd, 
            "status": "not_configured", 
            "message": "Telegram bot token not configured. Please set TELEGRAM_BOT_TOKEN environment variable.",
            "setup_instructions": "1. Get bot token from @BotFather on Telegram\n2. Set TELEGRAM_BOT_TOKEN=your_token in .env file\n3. Restart the server"
        }
    
    # Check if Telegram bot module is available
    try:
        from integrations.telegram_bot import send_command_to_bot, TELEGRAM_AVAILABLE
        
        if not TELEGRAM_AVAILABLE:
            return {
                "cmd": cmd,
                "status": "dependencies_missing",
                "message": "Telegram libraries not installed. Install with: pip install python-telegram-bot",
                "dependencies": ["python-telegram-bot"]
            }
            
    except ImportError as e:
        return {
            "cmd": cmd,
            "status": "module_not_found",
            "message": f"Telegram bot module not available: {str(e)}",
            "error": str(e)
        }
    
    # Actually send the command to the Telegram bot
    try:
        success = send_command_to_bot(cmd)
        if success:
            return {
                "cmd": cmd, 
                "status": "sent", 
                "message": "Command sent to Telegram bot successfully",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "cmd": cmd,
                "status": "failed",
                "message": "Failed to send command to Telegram bot - check bot logs for details"
            }
    except Exception as e:
        return {
            "cmd": cmd,
            "status": "error",
            "message": f"Error sending command to Telegram bot: {str(e)}",
            "error": str(e)
        }

@app.post("/files-scan")
async def files_scan(request: Request, path: str = Form(...), credentials: dict = Depends(verify_api_token)):
    # Validate path to prevent directory traversal attacks
    if ".." in path or path.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid path")
    
    # Check if path exists
    if not os.path.exists(path):
        raise HTTPException(status_code=400, detail="Path does not exist")
    
    files = glob.glob(os.path.join(path, '**', '*.*'), recursive=True)
    copied = []
    for f in files:
        try:
            # Validate file type
            ext = Path(f).suffix.lower()
            if ext not in ['.pdf', '.docx', '.xlsx', '.jpg', '.png', '.tiff', '.dwg']:
                continue
                
            # Use BASE_DIR environment variable or default to I:/docs
            base_dir_env = os.getenv("BASE_DIR", "I:/docs")
            dest = Path(base_dir_env) / "norms_db" / Path(f).name
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                shutil.copy2(f, dest)
            copied.append(str(dest))
        except Exception as e:
            print(f"Error copying file {f}: {e}")
            continue
            
    return {"scanned": len(files), "copied": len(copied), "path": path}

@app.post("/upload-file")
async def upload_file(request: Request, file: UploadFile = File(...), credentials: dict = Depends(verify_api_token)):
    """Upload a file with security validation - generic upload for RAG training"""
    try:
        # Validate file type
        allowed_extensions = {'.pdf', '.docx', '.xlsx', '.jpg', '.png', '.tiff', '.dwg'}
        if file.filename:
            file_ext = Path(file.filename).suffix.lower()
        else:
            raise HTTPException(status_code=400, detail="File name is missing")
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Validate file size (limit to 100MB)
        contents = await file.read()
        if len(contents) > 100 * 1024 * 1024:  # 100MB
            raise HTTPException(status_code=400, detail="File size exceeds 100MB limit")
        
        # Reset file pointer
        await file.seek(0)
        
        # Generate unique filename to prevent conflicts
        if file.filename:
            unique_filename = f"{uuid.uuid4()}_{file.filename}"
        else:
            unique_filename = f"{uuid.uuid4()}_unnamed_file"
            
        # Use BASE_DIR environment variable or default to I:/docs
        base_dir_env = os.getenv("BASE_DIR", "I:/docs")
        norms_db_dir = Path(base_dir_env) / "norms_db"
        norms_db_dir.mkdir(parents=True, exist_ok=True)
        file_path = norms_db_dir / unique_filename
        
        # Save file with proper error handling
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except PermissionError:
            raise HTTPException(status_code=500, detail=f"Permission denied when saving file: {file_path}")
        except OSError as e:
            raise HTTPException(status_code=500, detail=f"OS error when saving file: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error when saving file: {str(e)}")
        
        # Process the file with RAG trainer
        status_result = "uploaded_only"
        if trainer:
            try:
                # Use the correct method for processing a single file
                if hasattr(trainer, '_process_single_file'):
                    success = getattr(trainer, '_process_single_file')(str(file_path))
                    status_result = "processed" if success else "uploaded_only"
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")
                status_result = "uploaded_only"
        
        if file.filename:
            filename = file.filename
        else:
            filename = "unnamed_file"
            
        return FileUploadResponse(
            filename=filename,
            file_path=str(file_path),
            size=len(contents),
            status=status_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.post("/upload-for-training")
async def upload_for_rag_training(request: Request, file: UploadFile = File(...), credentials: dict = Depends(verify_api_token)):
    """Upload a file specifically for RAG system training"""
    try:
        # Validate file type
        allowed_extensions = {'.pdf', '.docx', '.xlsx', '.jpg', '.png', '.tiff', '.dwg'}
        if file.filename:
            file_ext = Path(file.filename).suffix.lower()
        else:
            raise HTTPException(status_code=400, detail="File name is missing")
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Validate file size (limit to 100MB)
        contents = await file.read()
        if len(contents) > 100 * 1024 * 1024:  # 100MB
            raise HTTPException(status_code=400, detail="File size exceeds 100MB limit")
        
        # Reset file pointer
        await file.seek(0)
        
        # Generate unique filename to prevent conflicts
        if file.filename:
            unique_filename = f"{uuid.uuid4()}_{file.filename}"
        else:
            unique_filename = f"{uuid.uuid4()}_unnamed_file"
            
        # Use BASE_DIR environment variable or default to I:/docs
        base_dir_env = os.getenv("BASE_DIR", "I:/docs")
        norms_db_dir = Path(base_dir_env) / "norms_db"
        norms_db_dir.mkdir(parents=True, exist_ok=True)
        file_path = norms_db_dir / unique_filename
        
        # Save file with proper error handling
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except PermissionError:
            raise HTTPException(status_code=500, detail=f"Permission denied when saving file: {file_path}")
        except OSError as e:
            raise HTTPException(status_code=500, detail=f"OS error when saving file: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error when saving file: {str(e)}")
        
        # Process the file with RAG trainer for training
        status_result = "uploaded_only"
        if trainer:
            try:
                # Use the correct method for processing a single file for training
                if hasattr(trainer, '_process_single_file'):
                    success = getattr(trainer, '_process_single_file')(str(file_path))
                    status_result = "processed" if success else "uploaded_only"
            except Exception as e:
                print(f"Error processing file {file_path} for training: {e}")
                status_result = "uploaded_only"
        
        if file.filename:
            filename = file.filename
        else:
            filename = "unnamed_file"
            
        return FileUploadResponse(
            filename=filename,
            file_path=str(file_path),
            size=len(contents),
            status=status_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file for training: {str(e)}")

@app.post("/upload-for-analysis")
async def upload_for_estimate_analysis(request: Request, file: UploadFile = File(...), credentials: dict = Depends(verify_api_token)):
    """Upload a file specifically for estimate/tender analysis"""
    try:
        # Validate file type - focus on estimate documents
        allowed_extensions = {'.pdf', '.docx', '.xlsx'}
        if file.filename:
            file_ext = Path(file.filename).suffix.lower()
        else:
            raise HTTPException(status_code=400, detail="File name is missing")
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type not allowed for analysis. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Validate file size (limit to 100MB)
        contents = await file.read()
        if len(contents) > 100 * 1024 * 1024:  # 100MB
            raise HTTPException(status_code=400, detail="File size exceeds 100MB limit")
        
        # Reset file pointer
        await file.seek(0)
        
        # Generate unique filename to prevent conflicts
        if file.filename:
            unique_filename = f"{uuid.uuid4()}_{file.filename}"
        else:
            unique_filename = f"{uuid.uuid4()}_unnamed_file"
            
        # Use BASE_DIR environment variable or default to I:/docs
        base_dir_env = os.getenv("BASE_DIR", "I:/docs")
        analysis_dir = Path(base_dir_env) / "analysis_uploads"
        analysis_dir.mkdir(parents=True, exist_ok=True)
        file_path = analysis_dir / unique_filename
        
        # Save file with proper error handling
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except PermissionError:
            raise HTTPException(status_code=500, detail=f"Permission denied when saving file: {file_path}")
        except OSError as e:
            raise HTTPException(status_code=500, detail=f"OS error when saving file: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error when saving file: {str(e)}")
        
        # Process the file for estimate analysis
        status_result = "uploaded_for_analysis"
        if trainer and hasattr(trainer, 'tools_system'):
            try:
                # Use estimate analysis tool
                tools_system = getattr(trainer, 'tools_system')
                result = tools_system.execute_tool("parse_gesn_estimate", {
                    "estimate_file": str(file_path)
                })
                if result.get("status") == "success":
                    status_result = "analysis_completed"
                else:
                    status_result = "analysis_failed"
            except Exception as e:
                print(f"Error analyzing file {file_path}: {e}")
                status_result = "analysis_failed"
        else:
            status_result = "uploaded_only"
        
        if file.filename:
            filename = file.filename
        else:
            filename = "unnamed_file"
            
        return FileUploadResponse(
            filename=filename,
            file_path=str(file_path),
            size=len(contents),
            status=status_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file for analysis: {str(e)}")

@app.post("/upload-from-client")
async def upload_from_telegram_or_shell(request: Request, file: UploadFile = File(...), credentials: dict = Depends(verify_api_token)):
    """Upload a file from Telegram or AI-shell with specific processing chain"""
    try:
        # Validate file type
        allowed_extensions = {'.pdf', '.docx', '.xlsx', '.jpg', '.png', '.tiff', '.dwg'}
        if file.filename:
            file_ext = Path(file.filename).suffix.lower()
        else:
            raise HTTPException(status_code=400, detail="File name is missing")
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Validate file size (limit to 100MB)
        contents = await file.read()
        if len(contents) > 100 * 1024 * 1024:  # 100MB
            raise HTTPException(status_code=400, detail="File size exceeds 100MB limit")
        
        # Reset file pointer
        await file.seek(0)
        
        # Generate unique filename to prevent conflicts
        if file.filename:
            unique_filename = f"{uuid.uuid4()}_{file.filename}"
        else:
            unique_filename = f"{uuid.uuid4()}_unnamed_file"
            
        # Use BASE_DIR environment variable or default to I:/docs
        base_dir_env = os.getenv("BASE_DIR", "I:/docs")
        client_uploads_dir = Path(base_dir_env) / "client_uploads"
        client_uploads_dir.mkdir(parents=True, exist_ok=True)
        file_path = client_uploads_dir / unique_filename
        
        # Save file with proper error handling
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except PermissionError:
            raise HTTPException(status_code=500, detail=f"Permission denied when saving file: {file_path}")
        except OSError as e:
            raise HTTPException(status_code=500, detail=f"OS error when saving file: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error when saving file: {str(e)}")
        
        # Process the file with client-specific processing chain
        status_result = "uploaded_for_client_processing"
        if trainer:
            try:
                # For client uploads, we might want to process differently
                # This could involve different tools or processing chains
                if hasattr(trainer, '_process_single_file'):
                    success = getattr(trainer, '_process_single_file')(str(file_path))
                    status_result = "client_processing_completed" if success else "uploaded_only"
            except Exception as e:
                print(f"Error processing file {file_path} from client: {e}")
                status_result = "uploaded_only"
        
        if file.filename:
            filename = file.filename
        else:
            filename = "unnamed_file"
            
        return FileUploadResponse(
            filename=filename,
            file_path=str(file_path),
            size=len(contents),
            status=status_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file from client: {str(e)}")

@app.get("/tools")
async def list_tools_endpoint(request: Request, category: Optional[str] = None, credentials: dict = Depends(verify_api_token)):
    """List all available tools with optional category filtering"""
    try:
        tools_result = None
        
        # Попытка 1: через trainer
        if trainer and hasattr(trainer, 'tools_system'):
            try:
                tools_system = getattr(trainer, 'tools_system')
                if hasattr(tools_system, 'list_available_tools'):
                    tools_result = tools_system.list_available_tools()
                elif hasattr(tools_system, 'discover_tools'):
                    tools_result = tools_system.discover_tools()
            except Exception as e:
                logger.warning(f"Trainer tools_system failed: {e}")
        
        # Попытка 2: через unified_tools_system
        if not tools_result:
            try:
                from core.unified_tools_system import unified_tools
                if hasattr(unified_tools, 'list_available_tools'):
                    tools_result = unified_tools.list_available_tools()
                elif hasattr(unified_tools, 'discover_tools'):
                    tools_result = unified_tools.discover_tools()
            except Exception as e:
                logger.warning(f"Unified tools system failed: {e}")
        
        # Попытка 3: fallback список инструментов
        if not tools_result:
            tools_result = {
                "status": "success",
                "data": {
                    "tools": {
                        "enhanced_search_internet_templates": {
                            "category": "document_generation",
                            "description": "Поиск шаблонов документов в интернете",
                            "ui_placement": "tools"
                        },
                        "adapt_template_for_company": {
                            "category": "document_generation", 
                            "description": "Адаптация шаблона под компанию",
                            "ui_placement": "tools"
                        },
                        "start_metrics_collection": {
                            "category": "monitoring",
                            "description": "Запуск сбора метрик",
                            "ui_placement": "tools"
                        }
                    },
                    "total_count": 3,
                    "categories": ["document_generation", "monitoring"]
                },
                "message": "Using fallback tools list"
            }
        
        # Filter by category if specified
        if category and tools_result:
            filtered_tools = {
                name: info for name, info in tools_result["data"]["tools"].items()
                if info.get("category") == category
            }
            tools_result["data"]["tools"] = filtered_tools
            tools_result["data"]["total_count"] = len(filtered_tools)
            tools_result["data"]["category"] = category
        
        return tools_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tools: {str(e)}")

# Alias endpoint to avoid 405 on GET /tools/list due to POST /tools/{tool_name}
@app.get("/tools/list")
async def list_tools_alias(request: Request, category: Optional[str] = None, credentials: dict = Depends(verify_api_token)):
    return await list_tools_endpoint(request, category, credentials)

@app.get("/tools/{tool_name}/info")
async def get_tool_info_endpoint(request: Request, tool_name: str, credentials: dict = Depends(verify_api_token)):
    """Get detailed information about a specific tool"""
    try:
        from core.unified_tools_system import unified_tools
        
        tool_info = unified_tools.get_tool_info(tool_name)
        
        if not tool_info:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        return {
            "status": "success",
            "tool_info": tool_info.__dict__
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tool info: {str(e)}")

@app.get("/tools/categories")
async def get_categories_endpoint(request: Request, credentials: dict = Depends(verify_api_token)):
    """Get all available tool categories"""
    try:
        from core.unified_tools_system import unified_tools
        
        categories = unified_tools.get_categories()
        
        return {
            "status": "success",
            "categories": categories,
            "total_count": len(categories)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")

@app.get("/tools/stats")
async def get_tools_stats_endpoint(request: Request, tool_name: Optional[str] = None, credentials: dict = Depends(verify_api_token)):
    """Get execution statistics for tools"""
    try:
        from core.unified_tools_system import unified_tools
        
        stats = unified_tools.get_execution_stats(tool_name)
        
        return {
            "status": "success",
            "stats": stats,
            "tool_name": tool_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@app.post("/tools/chain")
async def execute_tool_chain_endpoint(request: Request, chain: List[Dict[str, Any]], credentials: dict = Depends(verify_api_token)):
    """Execute a chain of tools with result passing"""
    try:
        from core.unified_tools_system import unified_tools
        results = unified_tools.execute_tool_chain(chain)
        
        return {
            "status": "success",
            "chain_results": [result.to_dict() for result in results],
            "total_steps": len(results),
            "successful_steps": sum(1 for r in results if r.is_success())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute tool chain: {str(e)}")

# Tool execution endpoints using getattr to avoid type checking issues
@app.post("/tools/{tool_name}")
async def execute_tool(request: Request, tool_name: str, tool_kwargs: Dict[str, Any], credentials: dict = Depends(verify_api_token)):
    """Universal tool execution with kwargs support and standardized responses"""
    try:
        # Use existing trainer tools_system with new kwargs support
        if trainer and hasattr(trainer, 'tools_system'):
            tools_system = getattr(trainer, 'tools_system')
            result = tools_system.execute_tool(tool_name, **tool_kwargs)
            return result
        else:
            raise HTTPException(status_code=503, detail="Tools system not available")
    except Exception as e:
        return {
            "status": "error",
            "error": f"Tool execution failed: {str(e)}",
            "tool_name": tool_name,
            "timestamp": datetime.now().isoformat()
        }

@app.post("/tools/generate_letter")
async def generate_letter_endpoint(request: Request, tool_args: Dict[str, Any], credentials: dict = Depends(verify_api_token)):
    """Generate official letter with LM Studio integration"""
    if not trainer:
        raise HTTPException(status_code=500, detail="Trainer not available")
        
    try:
        if hasattr(trainer, 'tools_system'):
            tools_system = getattr(trainer, 'tools_system')
            result = tools_system.execute_tool("generate_letter", tool_args)
            return result
        else:
            raise HTTPException(status_code=503, detail="Tools system not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate letter: {str(e)}")

@app.post("/tools/improve_letter")
async def improve_letter_endpoint(request: Request, tool_args: Dict[str, Any], credentials: dict = Depends(verify_api_token)):
    """Improve letter draft with LM Studio integration"""
    if not trainer:
        raise HTTPException(status_code=500, detail="Trainer not available")
        
    try:
        if hasattr(trainer, 'tools_system'):
            tools_system = getattr(trainer, 'tools_system')
            result = tools_system.execute_tool("improve_letter", tool_args)
            return result
        else:
            raise HTTPException(status_code=503, detail="Tools system not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to improve letter: {str(e)}")

@app.post("/tools/auto_budget")
async def auto_budget_endpoint(request: Request, tool_args: Dict[str, Any], credentials: dict = Depends(verify_api_token)):
    """Generate automatic budget"""
    if not trainer:
        raise HTTPException(status_code=500, detail="Trainer not available")
        
    try:
        if hasattr(trainer, 'tools_system'):
            tools_system = getattr(trainer, 'tools_system')
            result = tools_system.execute_tool("auto_budget", tool_args)
            return result
        else:
            raise HTTPException(status_code=503, detail="Tools system not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate budget: {str(e)}")

@app.post("/tools/generate_ppr")
async def generate_ppr_endpoint(request: Request, tool_args: Dict[str, Any], credentials: dict = Depends(verify_api_token)):
    """Generate PPR document"""
    if not trainer:
        raise HTTPException(status_code=500, detail="Trainer not available")
        
    try:
        if hasattr(trainer, 'tools_system'):
            tools_system = getattr(trainer, 'tools_system')
            result = tools_system.execute_tool("generate_ppr", tool_args)
            return result
        else:
            raise HTTPException(status_code=503, detail="Tools system not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PPR: {str(e)}")

@app.post("/tools/create_gpp")
async def create_gpp_endpoint(request: Request, tool_args: Dict[str, Any], credentials: dict = Depends(verify_api_token)):
    """Create GPP (Graphical Production Plan)"""
    if not trainer:
        raise HTTPException(status_code=500, detail="Trainer not available")
        
    try:
        if hasattr(trainer, 'tools_system'):
            tools_system = getattr(trainer, 'tools_system')
            result = tools_system.execute_tool("create_gpp", tool_args)
            return result
        else:
            raise HTTPException(status_code=503, detail="Tools system not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create GPP: {str(e)}")

@app.post("/tools/parse_gesn_estimate")
async def parse_gesn_estimate_endpoint(request: Request, tool_args: Dict[str, Any], credentials: dict = Depends(verify_api_token)):
    """Parse GESN/FER estimate"""
    if not trainer:
        raise HTTPException(status_code=500, detail="Trainer not available")
        
    try:
        if hasattr(trainer, 'tools_system'):
            tools_system = getattr(trainer, 'tools_system')
            result = tools_system.execute_tool("parse_gesn_estimate", tool_args)
            return result
        else:
            raise HTTPException(status_code=503, detail="Tools system not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse estimate: {str(e)}")

@app.post("/tools/analyze_tender")
async def analyze_tender_endpoint(request: Request, tool_args: Dict[str, Any], credentials: dict = Depends(verify_api_token)):
    """Analyze tender/project comprehensively"""
    if not trainer:
        raise HTTPException(status_code=500, detail="Trainer not available")
        
    try:
        if hasattr(trainer, 'tools_system'):
            tools_system = getattr(trainer, 'tools_system')
            result = tools_system.execute_tool("analyze_tender", tool_args)
            return result
        else:
            raise HTTPException(status_code=503, detail="Tools system not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze tender: {str(e)}")

# Add missing endpoints for super-feature tools
@app.post("/tools/analyze_bentley_model")
async def analyze_bentley_model_endpoint(request: Request, tool_args: Dict[str, Any], credentials: dict = Depends(verify_api_token)):
    """Analyze Bentley IFC model"""
    if not trainer:
        raise HTTPException(status_code=500, detail="Trainer not available")
        
    try:
        if hasattr(trainer, 'tools_system'):
            tools_system = getattr(trainer, 'tools_system')
            result = tools_system.execute_tool("analyze_bentley_model", tool_args)
            return result
        else:
            raise HTTPException(status_code=503, detail="Tools system not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze Bentley model: {str(e)}")

@app.post("/tools/autocad_export")
async def autocad_export_endpoint(request: Request, tool_args: Dict[str, Any], credentials: dict = Depends(verify_api_token)):
    """Export to AutoCAD DWG"""
    if not trainer:
        raise HTTPException(status_code=500, detail="Trainer not available")
        
    try:
        if hasattr(trainer, 'tools_system'):
            tools_system = getattr(trainer, 'tools_system')
            result = tools_system.execute_tool("autocad_export", tool_args)
            return result
        else:
            raise HTTPException(status_code=503, detail="Tools system not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export to AutoCAD: {str(e)}")

@app.post("/tools/monte_carlo_sim")
async def monte_carlo_sim_endpoint(request: Request, tool_args: Dict[str, Any], credentials: dict = Depends(verify_api_token)):
    """Monte Carlo simulation for risk analysis"""
    if not trainer:
        raise HTTPException(status_code=500, detail="Trainer not available")
        
    try:
        if hasattr(trainer, 'tools_system'):
            tools_system = getattr(trainer, 'tools_system')
            result = tools_system.execute_tool("monte_carlo_sim", tool_args)
            return result
        else:
            raise HTTPException(status_code=503, detail="Tools system not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run Monte Carlo simulation: {str(e)}")

@app.post("/analyze-tender")
async def analyze_tender_comprehensive_endpoint(
    request: Request, 
    tender_data: Dict[str, Any],
    region: str = "ekaterinburg",
    params: Optional[Dict[str, Any]] = None,
    credentials: dict = Depends(verify_api_token)
):
    """Comprehensive analysis of tender/project with full pipeline"""
    if not trainer:
        raise HTTPException(status_code=500, detail="Trainer not available")
    
    try:
        # Prepare tool arguments
        tool_args = {
            "tender_data": tender_data,
            "region": region,
            "params": params or {}
        }
        
        # Execute comprehensive analysis tool
        if hasattr(trainer, 'tools_system'):
            result = trainer.tools_system.execute_tool("comprehensive_analysis", tool_args)
        else:
            raise HTTPException(status_code=503, detail="Tools system not available")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze tender: {str(e)}")

@app.post("/analyze_image")
async def analyze_image(request: Request, request_data: ImageAnalysisRequest, credentials: dict = Depends(verify_api_token)):
    """Analyze image with real OpenCV/Tesseract processing"""
    try:
        # Try to import required libraries
        try:
            import cv2
            import numpy as np
            from PIL import Image
            import pytesseract
        except ImportError as e:
            raise HTTPException(status_code=500, detail=f"Required image processing libraries not available: {str(e)}")
        
        # Decode base64 image
        image_data = base64.b64decode(request_data.image_base64)
        
        # Save to temporary file
        temp_path = "temp_image.jpg"
        with open(temp_path, "wb") as f:
            f.write(image_data)
        
        # Process image based on type
        if request_data.type == "full":
            # Load image with OpenCV
            image = cv2.imread(temp_path)
            if image is None:
                raise HTTPException(status_code=400, detail="Invalid image data")
            
            # Edge detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Extract objects
            objects = []
            for i, contour in enumerate(contours[:20]):  # Limit to 20 objects
                x, y, w, h = cv2.boundingRect(contour)
                objects.append({
                    "id": f"obj_{i}",
                    "x": int(x),
                    "y": int(y),
                    "width": int(w),
                    "height": int(h),
                    "area": int(cv2.contourArea(contour))
                })
            
            # OCR with Tesseract
            pil_image = Image.open(temp_path)
            text = pytesseract.image_to_string(pil_image, lang='rus')
            
            # Extract measurements (simplified)
            measurements = {}
            # Look for dimensions in text
            import re
            dimension_matches = re.findall(r'(\d+(?:\.\d+)?)\s*(?:м|см|мм)', text)
            if dimension_matches:
                measurements["length"] = f"{dimension_matches[0]}м"
            
            # Clean up temporary file
            os.remove(temp_path)
            
            return JSONResponse(content={
                "objects": objects,
                "measurements": measurements,
                "text": text[:500]  # Limit text length
            })
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported analysis type: {request_data.type}")
            
    except Exception as e:
        # Clean up temporary file if it exists
        if os.path.exists("temp_image.jpg"):
            os.remove("temp_image.jpg")
        raise HTTPException(status_code=500, detail=f"Image analysis error: {str(e)}")

@app.post("/tts")
async def text_to_speech(request: Request, request_data: TTSRequest, credentials: dict = Depends(verify_api_token)):
    """Generate speech from text using selectable providers (silero|edge|elevenlabs) and formats (mp3|ogg)."""
    try:
        provider = getattr(request_data, 'provider', None) or os.getenv('TTS_PROVIDER', 'silero')
        voice = getattr(request_data, 'voice', None) or os.getenv('TTS_VOICE', 'ru-RU-SvetlanaNeural')
        language = getattr(request_data, 'language', None) or 'ru'
        fmt = getattr(request_data, 'format', None) or 'mp3'
        output_mp3 = 'response.mp3'
        output_ogg = 'response.ogg'
        
        if provider.lower() == 'edge':
            try:
                import asyncio, edge_tts
                text = request_data.text
                communicate = edge_tts.Communicate(text, voice)
                with open(output_mp3, 'wb') as f:
                    async def save():
                        async for chunk in communicate.stream():
                            if chunk["type"] == "audio":
                                f.write(chunk["data"])  # type: ignore
                    await save()
                # Convert to ogg if requested and ffmpeg present
                if fmt.lower() == 'ogg':
                    try:
                        import subprocess
                        subprocess.run(['ffmpeg','-y','-i',output_mp3,'-c:a','libopus',output_ogg], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        return JSONResponse(content={"audio_path": "/download/response.ogg", "status": "success"})
                    except Exception:
                        pass
                return JSONResponse(content={"audio_path": "/download/response.mp3", "status": "success"})
            except Exception as e:
                # Fallback to silero
                provider = 'silero'
        
        if provider.lower() == 'elevenlabs':
            try:
                import requests as _req
                api_key = os.getenv('ELEVENLABS_API_KEY')
                if not api_key:
                    raise RuntimeError('ELEVENLABS_API_KEY not set')
                url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice or '21m00Tcm4TlvDq8ikWAM'}"
                headers = {"xi-api-key": api_key, "accept":"audio/mpeg", "content-type":"application/json"}
                payload = {"text": request_data.text, "model_id":"eleven_monolingual_v1"}
                r = _req.post(url, headers=headers, json=payload, timeout=60)
                r.raise_for_status()
                with open(output_mp3,'wb') as f: f.write(r.content)
                if fmt.lower() == 'ogg':
                    try:
                        import subprocess
                        subprocess.run(['ffmpeg','-y','-i',output_mp3,'-c:a','libopus',output_ogg], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        return JSONResponse(content={"audio_path": "/download/response.ogg", "status": "success"})
                    except Exception:
                        pass
                return JSONResponse(content={"audio_path": "/download/response.mp3", "status": "success"})
            except Exception:
                provider = 'silero'
        
        # Default: silero
        try:
            import torch, torchaudio, yaml
        except ImportError as e:
            raise HTTPException(status_code=500, detail=f"Required TTS libraries not available: {str(e)}")
        
        torch.hub.download_url_to_file('https://raw.githubusercontent.com/snakers4/silero-models/master/models.yml','latest_silero_models.yml', progress=False)
        with open('latest_silero_models.yml', 'r', encoding='utf-8') as f:
            models = yaml.load(f, Loader=yaml.SafeLoader)
        tts_model = torch.hub.load(repo_or_dir='snakers4/silero-models', model='silero_tts', language='ru', speaker='v3_1_ru')
        audio = tts_model.apply_tts(text=request_data.text, speaker='v3_1_ru', sample_rate=48000)  # type: ignore
        torchaudio.save(output_mp3, audio, 48000)
        if fmt.lower() == 'ogg':
            try:
                import subprocess
                subprocess.run(['ffmpeg','-y','-i',output_mp3,'-c:a','libopus',output_ogg], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return JSONResponse(content={"audio_path": "/download/response.ogg", "status": "success"})
            except Exception:
                pass
        return JSONResponse(content={"audio_path": "/download/response.mp3", "status": "success"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {str(e)}")

@app.get("/download/{filename}")
async def download_file(filename: str):
    """Serve generated files like TTS output. Restrict to current working directory."""
    try:
        # Prevent path traversal
        import os
        safe_name = os.path.basename(filename)
        abs_path = os.path.abspath(safe_name)
        if not os.path.exists(abs_path):
            raise HTTPException(status_code=404, detail="File not found")
        return FileResponse(abs_path, filename=safe_name)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download error: {str(e)}")

# Add new endpoint for manual norms update
@app.post("/update-norms")
async def update_norms_endpoint(
    request: Request, 
    categories: Optional[List[str]] = None,
    credentials: dict = Depends(verify_api_token)
):
    """Manually trigger norms update from official sources"""
    try:
        results = await manual_update_norms(categories)
        return {
            "status": "success",
            "message": f"Norms update completed: {results['documents_downloaded']} documents downloaded",
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update norms: {str(e)}")

# Add endpoint to reset databases
@app.post("/reset-databases")
async def reset_databases(request: Request, credentials: dict = Depends(verify_api_token)):
    """Reset all databases (Neo4j, Qdrant, FAISS)"""
    try:
        import shutil
        import os
        from pathlib import Path
        
        # Use BASE_DIR environment variable or default to I:/docs
        base_dir_env = os.getenv("BASE_DIR", "I:/docs")
        
        # Directories to clean
        dirs_to_clean = [
            os.path.join(base_dir_env, 'qdrant_db'),
            os.path.join(base_dir_env, 'faiss_index.index'),
            os.path.join(base_dir_env, 'reports'),
            os.path.join(base_dir_env, 'norms_db')
        ]
        
        # Clean directories
        for d in dirs_to_clean:
            if os.path.exists(d):
                shutil.rmtree(d, ignore_errors=True)
        
        # Reset Qdrant collection if client is available
        if QDRANT_AVAILABLE and trainer and hasattr(trainer, 'qdrant_client'):
            try:
                qdrant_client = getattr(trainer, 'qdrant_client')
                qdrant_client.delete_collection('universal_docs')
            except Exception as e:
                print(f"Warning: Could not delete Qdrant collection: {e}")
        
        # Reset processed files log
        processed_file = Path(base_dir_env) / "reports" / "processed_files.json"
        if processed_file.exists():
            processed_file.unlink()
        
        return {
            "status": "success",
            "message": "All databases have been reset successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset databases: {str(e)}")

# Add endpoint to get norms update status
@app.get("/norms-status")
async def get_norms_status(request: Request, credentials: dict = Depends(verify_api_token)):
    """Get status of norms sources"""
    try:
        status = norms_updater.get_source_status()
        return {
            "status": "success",
            "sources": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get norms status: {str(e)}")

# Add endpoint to toggle cron job
@app.post("/toggle-cron")
async def toggle_cron_endpoint(
    request: Request, 
    enabled: bool,
    credentials: dict = Depends(verify_api_token)
):
    """Enable or disable the daily norms update cron job"""
    try:
        job = scheduler.get_job('daily_norms_update')
        if job:
            if enabled:
                job.resume()
                message = "Cron job enabled"
            else:
                job.pause()
                message = "Cron job disabled"
        else:
            if enabled:
                scheduler.add_job(
                    update_norms_job,
                    'cron',
                    hour=0,
                    minute=0,
                    id='daily_norms_update',
                    name='Daily Norms Update',
                    replace_existing=True
                )
                message = "Cron job enabled and scheduled"
            else:
                message = "Cron job is already disabled"
        
        return {
            "status": "success",
            "message": message
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle cron job: {str(e)}")

# Add endpoint for toggling cron job
@app.post("/cron-job")
async def toggle_cron_job(enabled: bool, credentials: dict = Depends(verify_api_token)):
    """Enable or disable the cron job for daily norms update"""
    try:
        # Import Celery app and task
        from core.celery_app import celery_app
        from core.celery_norms import update_norms_task
        
        # Use Celery's scheduler instead of APScheduler
        if enabled:
            # Schedule the task to run daily at midnight
            from celery.schedules import crontab
            celery_app.conf.beat_schedule = {
                'daily_norms_update': {
                    'task': 'core.celery_norms.update_norms_task',
                    'schedule': crontab(hour='0', minute='0'),
                }
            }
            message = "Cron job enabled and scheduled via Celery Beat"
        else:
            # Remove the scheduled task
            celery_app.conf.beat_schedule = {}
            message = "Cron job disabled"
        
        return {
            "status": "success",
            "message": message
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle cron job: {str(e)}")

@app.get("/queue")
async def get_queue_status(credentials: dict = Depends(verify_api_token)):
    """Get current queue status from Neo4j and Redis"""
    if not NEO4J_AVAILABLE:
        # Возвращаем пустую очередь вместо ошибки
        return {
            "status": "ok",
            "queue_size": 0,
            "active_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "message": "Neo4j not available - using fallback mode"
        }
    
    try:
        # Import Neo4j driver
        from neo4j import GraphDatabase
        
        # Get tasks from Neo4j
        # Check if Neo4j auth is disabled
        neo4j_auth_disabled = os.getenv("NEO4J_AUTH_DISABLED", "false").lower() == "true"
        
        if neo4j_auth_disabled:
            driver = GraphDatabase.driver(NEO4J_URI, auth=None)
        else:
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        
        with driver:
            with driver.session() as session:
                result = session.run("""
                    MATCH (t:Task)
                    RETURN t
                    ORDER BY t.started_at DESC
                    LIMIT 50
                """)
                
                tasks_neo = []
                for record in result:
                    task_data = dict(record["t"])
                    task_id = task_data.get("id")
                    
                    # Get task status from Celery if task exists
                    if task_id:
                        try:
                            # Import Celery app
                            from core.celery_app import celery_app
                            celery_result = celery_app.AsyncResult(task_id)
                            task_data["celery_status"] = celery_result.status
                            if hasattr(celery_result.info, 'get'):
                                task_data["progress"] = celery_result.info.get("progress", task_data.get("progress", 0))
                        except Exception:
                            # If we can't get Celery status, use Neo4j data
                            pass
                    
                    # Convert task data to match frontend QueueTask interface
                    queue_task = {
                        "id": task_data.get("id", ""),
                        "type": task_data.get("type", "unknown"),
                        "status": task_data.get("status", "queued"),
                        "progress": task_data.get("progress", 0),
                        "owner": task_data.get("owner", "system"),
                        "started_at": task_data.get("started_at", datetime.now().isoformat()),
                        "eta": task_data.get("eta", None)
                    }
                    
                    tasks_neo.append(queue_task)
        
        return tasks_neo
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get queue status: {str(e)}")

@app.get("/norms-export")
async def export_norms(
    format: str = "csv",
    category: Optional[str] = None,
    status: Optional[str] = None,
    type: Optional[str] = None,
    search: Optional[str] = None,
    credentials: dict = Depends(verify_api_token)
):
    """Export norms list to CSV or Excel"""
    if not NEO4J_AVAILABLE or not trainer or not hasattr(trainer, 'neo4j_driver'):
        raise HTTPException(status_code=500, detail="Neo4j database not available")
    
    try:
        neo4j_driver = getattr(trainer, 'neo4j_driver')
        with neo4j_driver.session() as session:
            # Build Cypher query with filters
            cypher = """
                MATCH (d:NormDoc)
                WHERE ($category IS NULL OR d.category = $category)
                AND ($status IS NULL OR d.status = $status)
                AND ($type IS NULL OR d.type = $type)
                AND ($search IS NULL OR d.id CONTAINS $search OR d.name CONTAINS $search)
                RETURN d {
                    .id,
                    .name,
                    .category,
                    .type,
                    .status,
                    .issue_date,
                    .check_date,
                    .source,
                    .link,
                    .description
                }
                ORDER BY d.issue_date DESC
            """
            
            # Execute query
            result = session.run(
                cypher,
                category=category,
                status=status,
                type=type,
                search=search
            )
            
            norms = [dict(record["d"]) for record in result]
            
            # Export based on format
            if format.lower() == "csv":
                import csv
                import io
                
                # Create CSV in memory
                output = io.StringIO()
                if norms:
                    writer = csv.DictWriter(output, fieldnames=norms[0].keys())
                    writer.writeheader()
                    writer.writerows(norms)
                
                # Return as CSV response
                from fastapi.responses import Response
                return Response(
                    content=output.getvalue(),
                    media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=ntd_list.csv"}
                )
            elif format.lower() == "excel":
                # Try to import pandas for Excel export
                try:
                    import pandas as pd
                    
                    # Create DataFrame and export to Excel
                    df = pd.DataFrame(norms)
                    
                    # Save to temporary file
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                        df.to_excel(tmp.name, index=False)
                        tmp_path = tmp.name
                    
                    # Return as file response
                    from fastapi.responses import FileResponse
                    return FileResponse(
                        tmp_path,
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        filename="ntd_list.xlsx"
                    )
                except ImportError:
                    raise HTTPException(status_code=500, detail="Pandas not available for Excel export")
            else:
                raise HTTPException(status_code=400, detail="Unsupported format. Use 'csv' or 'excel'")
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export norms: {str(e)}")

@app.get("/norms-summary")
async def get_norms_summary(credentials: dict = Depends(verify_api_token)):
    """Get summary counts for norms"""
    if not NEO4J_AVAILABLE or not trainer or not hasattr(trainer, 'neo4j') or not trainer.neo4j:
        # Возвращаем пустую сводку вместо ошибки
        return {
            "total_norms": 0,
            "categories": {},
            "recent_updates": 0,
            "message": "Neo4j not available - using fallback mode"
        }
    
    try:
        with trainer.neo4j.session() as session:
            # Get summary counts
            result = session.run("""
                MATCH (d:NormDoc)
                RETURN 
                    count(d) as total,
                    count(CASE WHEN d.status = 'actual' THEN 1 END) as actual,
                    count(CASE WHEN d.status = 'outdated' THEN 1 END) as outdated,
                    count(CASE WHEN d.status = 'pending' THEN 1 END) as pending
            """)
            
            summary = result.single()
            
            if summary is None:
                return {
                    "total": 0,
                    "actual": 0,
                    "outdated": 0,
                    "pending": 0
                }
            
            return {
                "total": summary["total"],
                "actual": summary["actual"],
                "outdated": summary["outdated"],
                "pending": summary["pending"]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get norms summary: {str(e)}")

@app.get("/norms-list")
async def get_norms_list(
    category: Optional[str] = None,
    status: Optional[str] = None,
    doc_type: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    credentials: dict = Depends(verify_api_token)
):
    """Get list of trained norms documents with filtering and pagination"""
    if not NEO4J_AVAILABLE or not trainer or not hasattr(trainer, 'neo4j') or not trainer.neo4j:
        # Return empty list instead of error
        return {
            "data": [],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": 0,
                "pages": 0
            }
        }
    
    try:
        with trainer.neo4j.session() as session:
            # Build dynamic query with filters
            query_parts = ["MATCH (d:NormDoc)"]
            params = {}
            
            # Add filters
            where_conditions = []
            if category:
                where_conditions.append("d.category = $category")
                params["category"] = category
            if status:
                where_conditions.append("d.status = $status")
                params["status"] = status
            if doc_type:
                where_conditions.append("d.type = $doc_type")
                params["doc_type"] = doc_type
            if search:
                where_conditions.append("(d.name CONTAINS $search OR d.description CONTAINS $search)")
                params["search"] = search
            
            if where_conditions:
                query_parts.append("WHERE " + " AND ".join(where_conditions))
            
            # Add pagination
            query_parts.append("RETURN d ORDER BY d.issue_date DESC SKIP $skip LIMIT $limit")
            params["skip"] = (page - 1) * limit
            params["limit"] = limit
            
            # Count total for pagination
            count_query = "MATCH (d:NormDoc)" + (" WHERE " + " AND ".join(where_conditions) if where_conditions else "") + " RETURN count(d) as total"
            count_result = session.run(count_query, params)
            total = count_result.single()["total"]
            
            # Execute main query
            query = " ".join(query_parts)
            result = session.run(query, params)
            
            docs = []
            for record in result:
                doc = dict(record["d"])
                # Convert Neo4j DateTime to string if needed
                if "issue_date" in doc and hasattr(doc["issue_date"], 'isoformat'):
                    doc["issue_date"] = doc["issue_date"].isoformat()
                if "check_date" in doc and hasattr(doc["check_date"], 'isoformat'):
                    doc["check_date"] = doc["check_date"].isoformat()
                docs.append(doc)
            
            return {
                "data": docs,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get norms list: {str(e)}")

# Template management endpoints
@app.get("/templates")
async def get_templates(category: Optional[str] = None, credentials: dict = Depends(verify_api_token)):
    """Get all templates or templates by category"""
    try:
        from core.template_manager import template_manager
        templates = template_manager.get_templates(category)
        return templates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get templates: {str(e)}")

@app.post("/templates")
async def create_template(template_data: Dict[str, Any], credentials: dict = Depends(verify_api_token)):
    """Create a new template"""
    try:
        from core.template_manager import template_manager
        template = template_manager.create_template(template_data)
        return template
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create template: {str(e)}")

@app.put("/templates/{template_id}")
async def update_template(template_id: str, template_data: Dict[str, Any], credentials: dict = Depends(verify_api_token)):
    """Update an existing template"""
    try:
        from core.template_manager import template_manager
        template = template_manager.update_template(template_id, template_data)
        return template
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update template: {str(e)}")

@app.delete("/templates/{template_id}")
async def delete_template(template_id: str, credentials: dict = Depends(verify_api_token)):
    """Delete a template"""
    try:
        from core.template_manager import template_manager
        result = template_manager.delete_template(template_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete template: {str(e)}")

# ===============================
# RAG API ENDPOINTS
# ===============================

@app.post("/api/rag/search", response_model=RAGSearchResponse)
async def rag_search(request_data: RAGSearchRequest, credentials: dict = Depends(verify_api_token)):
    """Выполнить семантический поиск в RAG базе данных"""
    if not trainer:
        raise HTTPException(status_code=503, detail="RAG trainer not available")
    
    start_time = time.time()
    
    try:
        # Выполнить поиск через trainer
        if request_data.doc_types:
            # Использовать фильтр по типам документов
            results = await asyncio.to_thread(
                trainer.query_with_filters,
                request_data.query,
                request_data.k,
                doc_types=request_data.doc_types,
                threshold=request_data.threshold
            )
        else:
            # Стандартный поиск
            results = await asyncio.to_thread(
                trainer.query,
                request_data.query,
                request_data.k
            )
        
        # Преобразовать результаты в формат RAGSearchResult
        rag_results = []
        for result in results.get('results', []):
            rag_result = RAGSearchResult(
                content=result.get('chunk', ''),
                score=result.get('score', 0.0),
                metadata=result.get('meta', {}) if request_data.include_metadata else {},
                section_id=result.get('section_id'),
                chunk_type=result.get('chunk_type', 'paragraph')
            )
            rag_results.append(rag_result)
        
        processing_time = time.time() - start_time
        
        response = RAGSearchResponse(
            query=request_data.query,
            results=rag_results,
            total_found=len(rag_results),
            processing_time=processing_time,
            search_method="sbert"
        )
        
        logger.info(f"RAG search completed: query='{request_data.query}', results={len(rag_results)}, time={processing_time:.2f}s")
        
        return response
        
    except Exception as e:
        logger.error(f"RAG search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/api/rag/train", response_model=RAGTrainingResponse)
async def rag_train(request_data: RAGTrainingRequest, background_tasks: BackgroundTasks, credentials: dict = Depends(verify_api_token)):
    """Запустить обучение RAG системы"""
    if not trainer:
        raise HTTPException(status_code=503, detail="RAG trainer not available")
    
    # Проверить, не идет ли уже обучение
    global training_status
    if training_status["is_training"]:
        raise HTTPException(status_code=409, detail="Training already in progress")
    
    try:
        # Сгенерировать уникальный ID задачи
        task_id = f"rag_training_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        # Подготовить параметры обучения
        train_params = {
            'custom_dir': request_data.base_dir,
            'fast_mode': False,  # Полное обучение по умолчанию
            'force_retrain': request_data.force_retrain,
            'doc_types': request_data.doc_types,
            'max_files': request_data.max_files
        }
        
        # Запустить обучение в фоновом режиме
        background_tasks.add_task(run_training_with_updates, request_data.base_dir, False)
        
        response = RAGTrainingResponse(
            task_id=task_id,
            status="started",
            message="RAG training started successfully",
            estimated_time="15-60 minutes"
        )
        
        logger.info(f"RAG training started: task_id={task_id}, params={train_params}")
        
        return response
        
    except Exception as e:
        logger.error(f"RAG training start error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Training start failed: {str(e)}")

@app.get("/api/rag/status", response_model=RAGStatusResponse)
async def rag_status(credentials: dict = Depends(verify_api_token)):
    """Получить статус RAG системы"""
    global training_status
    
    try:
        # Получить статистику из базы данных
        total_documents = 0
        total_chunks = 0
        
        if trainer and QDRANT_AVAILABLE:
            try:
                # Получить количество векторов из Qdrant
                from qdrant_client import QdrantClient
                if hasattr(trainer, 'qdrant_path'):
                    qdrant_path = getattr(trainer, 'qdrant_path')
                    client = QdrantClient(path=qdrant_path)
                else:
                    # Use default path if not available
                    client = QdrantClient(path=QDRANT_PATH)
                collections = client.get_collections()
                for collection in collections.collections:
                    info = client.get_collection(collection.name)
                    total_chunks += info.points_count or 0
            except Exception as e:
                logger.warning(f"Could not get Qdrant stats: {e}")
        
        if trainer and NEO4J_AVAILABLE and hasattr(trainer, 'neo4j') and trainer.neo4j:
            try:
                # Получить количество документов из Neo4j
                with trainer.neo4j.session() as session:
                    result = session.run("MATCH (d:Document) RETURN count(d) as count")
                    record = result.single()
                    total_documents = record["count"] if record else 0
            except Exception as e:
                logger.warning(f"Could not get Neo4j stats: {e}")
        
        response = RAGStatusResponse(
            is_training=training_status["is_training"],
            progress=training_status["progress"],
            current_stage=training_status["current_stage"],
            message=training_status["message"],
            total_documents=total_documents,
            total_chunks=total_chunks,
            last_update=datetime.now()
        )
        
        return response
        
    except Exception as e:
        logger.error(f"RAG status error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@app.post("/api/ai/chat", response_model=AIChatResponse)
async def ai_chat(request_data: AIChatMessage, credentials: dict = Depends(verify_api_token)):
    """AI чат с поддержкой контекста из RAG"""
    if not trainer:
        raise HTTPException(status_code=503, detail="RAG trainer not available")
    
    start_time = time.time()
    
    try:
        context_used = []
        
        # IMPORTANT: Do NOT query RAG here. Coordinator decides tools (including RAG) based on the plan.
        enhanced_message = request_data.message
        
        # Handle multimedia: save voice/image to temp and set request context for coordinator
        request_context = getattr(request_data, 'request_context', {}) or {}
        try:
            import base64 as _b64, tempfile as _tmp, os as _os
            from pathlib import Path as _Path
            if getattr(request_data, 'voice_data', None):
                try:
                    audio_bytes = _b64.b64decode(request_data.voice_data)
                    # Telegram voice is usually OGG/OPUS
                    fd, audio_path = _tmp.mkstemp(suffix='.ogg', prefix='ai_voice_')
                    with _os.fdopen(fd, 'wb') as f:
                        f.write(audio_bytes)
                    request_context['audio_path'] = audio_path
                except Exception as e:
                    logger.warning(f"Voice decode/save failed: {e}")
            if getattr(request_data, 'image_data', None):
                try:
                    image_bytes = _b64.b64decode(request_data.image_data)
                    fd, image_path = _tmp.mkstemp(suffix='.png', prefix='ai_image_')
                    with _os.fdopen(fd, 'wb') as f:
                        f.write(image_bytes)
                    request_context['image_path'] = image_path
                except Exception as e:
                    logger.warning(f"Image decode/save failed: {e}")
            if getattr(request_data, 'document_data', None):
                try:
                    doc_bytes = _b64.b64decode(request_data.document_data)
                    doc_name = getattr(request_data, 'document_name', None) or 'uploaded.bin'
                    ext = _Path(doc_name).suffix or '.bin'
                    fd, doc_path = _tmp.mkstemp(suffix=ext, prefix='ai_doc_')
                    with _os.fdopen(fd, 'wb') as f:
                        f.write(doc_bytes)
                    request_context['document_path'] = doc_path
                    request_context['document_name'] = doc_name
                except Exception as e:
                    logger.warning(f"Document decode/save failed: {e}")
        except Exception as e:
            logger.warning(f"Multimedia handling error: {e}")
        
        # Default prompt enrichment if message is generic/empty and media present
        if not enhanced_message or enhanced_message.strip() == '' or enhanced_message in ('Image message','Voice message','Document message'):
            try:
                if request_context.get('image_path') and not getattr(request_data, 'request_context', {}).get('caption'):
                    enhanced_message = 'Проанализируй это изображение. Выполни OCR для извлечения текста и проанализируй содержание. Если есть строительные чертежи, схемы или документы - опиши их детально и найди соответствующие нормы.'
                elif request_context.get('document_path'):
                    dn = request_context.get('document_name', 'файл')
                    ext = _Path(dn).suffix.lower().lstrip('.') if dn else 'unknown'
                    enhanced_message = f'Проанализируй файл "{dn}" (формат: {ext}). Определи содержимое, извлеки полезную информацию, особенно связанную со строительством и нормами. Если это таблица — выдели ключевые показатели и несоответствия.'
                elif request_context.get('audio_path'):
                    enhanced_message = 'Транскрибируй голосовое сообщение и проанализируй его содержание. Если есть вопросы о строительных нормах, найди подходящие ответы в базе знаний.'
            except Exception:
                pass
        
        # Apply request context to coordinator
        if coordinator_agent and request_context:
            coordinator_agent.set_request_context(request_context)
        
        # НОВАЯ ПРАВИЛЬНАЯ ЦЕПОЧКА ОБРАБОТКИ - БЕЗ МОКОВ И ЗАГЛУШЕК
        try:
            # Использовать координатор если доступен
            if coordinator_agent:
                logger.info(f"🚀 Starting full processing chain for: {request_data.message[:50]}...")
                
                # Set request context for file delivery if provided
                request_context = getattr(request_data, 'request_context', None)
                if request_context:
                    coordinator_agent.set_request_context(request_context)
                
                # Get Master Tools System через адаптер
                master_tools_adapter = None
                if trainer and hasattr(trainer, 'tools_system'):
                    master_tools_adapter = getattr(trainer, 'tools_system')
                    logger.info("📡 Master Tools System adapter available")
                
                # STEP 1: Coordinator анализирует запрос и генерирует план
                logger.info("🧠 STEP 1: Coordinator analyzing query and generating execution plan...")
                try:
                    plan = coordinator_agent.generate_plan(enhanced_message)  # With context
                    logger.info(f"📋 Plan generated successfully: {type(plan)} - {str(plan)[:100]}...")
                except Exception as e:
                    logger.error(f"❌ Plan generation failed: {e}")
                    plan = {"complexity": "low", "tasks": [], "roles": []}
                
                # STEP 2: Если план содержит задачи с инструментами - выполняем их
                execution_results = []
                prev_outputs: Dict[str, Any] = {}
                if plan and isinstance(plan, dict) and plan.get('tasks') and master_tools_adapter:
                    logger.info("🔧 STEP 2: Executing plan tasks with Master Tools System...")
                    
                    for task in plan.get('tasks', []):
                        if isinstance(task, dict) and task.get('tool'):
                            tool_name = task.get('tool')
                            tool_input = task.get('input', {}) or {}
                            
                            # Inject previous outputs if requested
                            if isinstance(tool_input, dict) and tool_input.get('from_prev') == 'transcription' and 'transcription' in prev_outputs:
                                if tool_name == 'search_rag_database':
                                    tool_input = {"query": prev_outputs['transcription'], "k": 3}
                                elif tool_name in ('comprehensive_analysis', 'analyze_text'):
                                    tool_input = {"text": prev_outputs['transcription']}
                            
                            try:
                                logger.info(f"⚙️ Executing tool: {tool_name} with input: {tool_input}")
                                
                                # Normalize tool input to mapping where necessary
                                if not isinstance(tool_input, dict):
                                    if tool_name == 'search_rag_database':
                                        tool_input = {"query": str(tool_input), "k": 3}
                                    elif tool_name in ('comprehensive_analysis','analyze_text','analyze_document'):
                                        tool_input = {"text": str(tool_input)}
                                    else:
                                        tool_input = {"input": str(tool_input)}
                                
                                # Inject paths from request context if missing
                                try:
                                    if tool_name == 'transcribe_audio' and request_context and isinstance(tool_input, dict):
                                        if 'audio_path' not in tool_input and request_context.get('audio_path'):
                                            tool_input['audio_path'] = request_context['audio_path']
                                    if tool_name in ('analyze_image', 'ocr_text') and request_context and isinstance(tool_input, dict):
                                        if 'image_path' not in tool_input and request_context.get('image_path'):
                                            tool_input['image_path'] = request_context['image_path']
                                    if tool_name in ('analyze_document',) and request_context and isinstance(tool_input, dict):
                                        if 'document_path' not in tool_input and request_context.get('document_path'):
                                            tool_input['document_path'] = request_context['document_path']
                                except Exception:
                                    pass
                                
                                # Special handling for audio transcription via coordinator
                                if tool_name == 'transcribe_audio' and coordinator_agent:
                                    import json as _json, os as _os
                                    # Ensure audio_path provided
                                    ap = tool_input.get('audio_path') if isinstance(tool_input, dict) else None
                                    if not ap or not _os.path.exists(ap):
                                        tool_result = {"status": "error", "error": "audio_path missing or file not found"}
                                    else:
                                        tr_result = coordinator_agent._transcribe_audio(_json.dumps(tool_input))
                                        if isinstance(tr_result, dict):
                                            status_ok = (tr_result.get('status') or 'success').lower() == 'success'
                                            trans = (tr_result.get('transcription') or '').strip()
                                            if status_ok and trans:
                                                prev_outputs['transcription'] = trans
                                                tool_result = {"status": "success", "data": tr_result}
                                            else:
                                                tool_result = {"status": "error", "error": tr_result.get('error') or 'transcription empty'}
                                        else:
                                            # Treat plain string as transcription only if not an error phrase
                                            trans = str(tr_result).strip()
                                            if not trans.lower().startswith('ошибка'):
                                                prev_outputs['transcription'] = trans
                                                tool_result = {"status": "success", "data": {"transcription": trans}}
                                            else:
                                                tool_result = {"status": "error", "error": trans}
                                else:
                                    # Выполняем инструмент через адаптер
                                    if hasattr(master_tools_adapter, 'execute_tool'):
                                        tool_result = master_tools_adapter.execute_tool(tool_name, **tool_input)
                                    else:
                                        raise RuntimeError("Tools adapter missing execute_tool")
                                
                                execution_results.append({
                                    "tool": tool_name,
                                    "result": tool_result,
                                    "status": (tool_result.get('status') if isinstance(tool_result, dict) else 'completed') or 'completed'
                                })
                                logger.info(f"✅ Tool {tool_name} executed successfully")
                                
                            except Exception as e:
                                logger.error(f"❌ Tool {tool_name} execution failed: {e}")
                                execution_results.append({
                                    "tool": tool_name,
                                    "error": str(e),
                                    "status": "error"
                                })
                    
                    logger.info(f"🏁 Plan execution completed. {len(execution_results)} tasks processed")
                else:
                    logger.info("ℹ️ No tasks to execute or tools system not available")
                
                # STEP 3: Coordinator генерирует финальный ответ на основе плана и результатов
                logger.info("📝 STEP 3: Coordinator generating final response...")
                try:
                    # Fallback: если исполнение пустое или контекст не использован — быстрый RAG-поиск
                    try:
                        if (not execution_results or all((er.get('status') == 'error') for er in execution_results)) and master_tools_adapter:
                            sr = master_tools_adapter.execute_tool('search_rag_database', query=enhanced_message, k=3)
                            execution_results.append({'tool': 'search_rag_database', 'result': sr, 'status': (sr.get('status') if isinstance(sr, dict) else 'completed')})
                    except Exception as _e:
                        logger.warning(f"Fallback RAG failed: {_e}")

                    # Генерируем итоговый ответ (actionable) с источниками
                    ai_response = coordinator_agent.generate_final_response(
                        enhanced_message,
                        plan or {},
                        execution_results or [],
                        len(context_used)
                    )
                    logger.info(f"📄 Final response generated: {len(ai_response)} characters")
                except Exception as e:
                    logger.error(f"❌ Response generation failed: {e}")
                    ai_response = f"Извините, произошла ошибка при генерации ответа: {str(e)}"
                
                # Clear request context after processing
                if request_context:
                    coordinator_agent.clear_request_context()
                
                agent_used = "coordinator_with_tools"
                
            else:
                logger.warning("⚠️ Coordinator agent not available, using fallback")
                # Fallback к базовому AI (быстрая компактная модель)
                import requests
                lm_studio_url = os.getenv("LLM_BASE_URL", "http://localhost:1234")
                fallback_model = os.getenv("LLM_FALLBACK_MODEL", "Qwen/Qwen2.5-3B-Instruct-GGUF")
                response = requests.post(
                    f"{lm_studio_url}/v1/chat/completions",
                    json={
                        "model": fallback_model,
                        "messages": [
                            {"role": "system", "content": "Ты Координатор системы Bldr Empire v2. Отвечай кратко и по делу."},
                            {"role": "user", "content": enhanced_message}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 512
                    },
                    timeout=60
                )
                if response.status_code == 200:
                    try:
                        resp_json = response.json()
                        choices = resp_json.get("choices")
                        if isinstance(choices, list) and choices and "message" in choices[0] and "content" in choices[0]["message"]:
                            ai_response = choices[0]["message"]["content"]
                        elif isinstance(choices, list) and choices and "text" in choices[0]:
                            ai_response = choices[0]["text"]
                        else:
                            ai_response = resp_json.get("content") or resp_json.get("message") or "Сервис LLM вернул неожиданный ответ."
                    except Exception:
                        ai_response = "Сервис LLM вернул неожиданный ответ."
                    if "<think>" in ai_response and "</think>" in ai_response:
                        ai_response = re.sub(r'<think>.*?</think>', '', ai_response, flags=re.DOTALL).strip()
                else:
                    ai_response = "Сервис LLM недоступен. Попробуйте позже."
                agent_used = "fallback_llm_fast"
                
        except Exception as e:
            logger.error(f"AI processing error: {e}")
            ai_response = f"Error processing request: {str(e)}"
            agent_used = "error"
        
        processing_time = time.time() - start_time
        
        response = AIChatResponse(
            response=ai_response,
            context_used=context_used,
            agent_used=agent_used,
            processing_time=processing_time
        )
        
        logger.info(f"AI chat completed: context_count={len(context_used)}, agent={agent_used}, time={processing_time:.2f}s")
        
        return response
        
    except Exception as e:
        logger.error(f"AI chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI chat failed: {str(e)}")

@app.post("/api/document/analyze", response_model=DocumentAnalysisResponse)
async def analyze_document(request_data: DocumentAnalysisRequest, credentials: dict = Depends(verify_api_token)):
    """Анализ документа с помощью RAG системы"""
    if not trainer:
        raise HTTPException(status_code=503, detail="RAG trainer not available")
    
    if not os.path.exists(request_data.file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    start_time = time.time()
    
    try:
        # Использовать анализатор документов из trainer
        if hasattr(trainer, 'analyze_single_document'):
            analysis_result = await asyncio.to_thread(
                trainer.analyze_single_document,
                request_data.file_path,
                request_data.analysis_type,
                request_data.extract_works
            )
        else:
            raise HTTPException(status_code=503, detail="Document analysis not available")
        
        processing_time = time.time() - start_time
        
        response = DocumentAnalysisResponse(
            file_path=request_data.file_path,
            doc_type=analysis_result.get('doc_type', 'unknown'),
            confidence=analysis_result.get('confidence', 0.0),
            sections_count=analysis_result.get('sections_count', 0),
            works_found=analysis_result.get('works_found', 0),
            metadata=analysis_result.get('metadata', {}),
            quality_score=analysis_result.get('quality_score', 0.0),
            processing_time=processing_time
        )
        
        logger.info(f"Document analysis completed: file={request_data.file_path}, type={response.doc_type}, time={processing_time:.2f}s")
        
        return response
        
    except Exception as e:
        logger.error(f"Document analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Document analysis failed: {str(e)}")

# Add main section at the end of the file for proper execution

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("core.bldr_api:app", host="0.0.0.0", port=8000, reload=True)