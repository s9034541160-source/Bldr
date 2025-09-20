# ЭТОТ ФАЙЛ УДАЛЕН - используйте C:\Bldr\core\main.py
SuperBuilder Tools - FastAPI Application
Главное приложение с REST API и WebSocket поддержкой для инструментов SuperBuilder.
"""

import asyncio
import logging
import uvicorn
from datetime import datetime
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware

# Import API routers
from api.tools_api import router as tools_router
from api.websocket_server import websocket_endpoint, periodic_system_updates

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global background tasks
background_tasks = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    logger.info("Starting SuperBuilder Tools API server...")
    
    # Start background tasks
    periodic_task = asyncio.create_task(periodic_system_updates())
    background_tasks.append(periodic_task)
    
    logger.info("Server started successfully")
    yield
    
    # Shutdown
    logger.info("Shutting down SuperBuilder Tools API server...")
    
    # Cancel background tasks
    for task in background_tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    
    logger.info("Server shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="SuperBuilder Tools API",
    description="REST API для инструментов анализа строительных проектов",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware для логирования запросов"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = datetime.now()
        
        # Log request
        logger.info(
            f"{request.method} {request.url.path} - "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )
        
        response = await call_next(request)
        
        # Log response
        process_time = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.3f}s"
        )
        
        return response

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Include API routers
app.include_router(tools_router)

# WebSocket endpoint
@app.websocket("/ws/{path:path}")
async def websocket_handler(websocket, path: str = ""):
    """WebSocket endpoint для real-time уведомлений"""
    await websocket_endpoint(websocket, path)

# Serve static files (если есть frontend)
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root():
    """Главная страница API"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SuperBuilder Tools API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .header { text-align: center; color: #2c3e50; }
            .section { margin: 30px 0; padding: 20px; border-left: 4px solid #3498db; }
            .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .method { color: #27ae60; font-weight: bold; }
            a { color: #3498db; text-decoration: none; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏗️ SuperBuilder Tools API</h1>
                <p>REST API для инструментов анализа строительных проектов</p>
            </div>
            
            <div class="section">
                <h2>📚 Документация</h2>
                <p>
                    <a href="/docs" target="_blank">Swagger UI</a> | 
                    <a href="/redoc" target="_blank">ReDoc</a>
                </p>
            </div>
            
            <div class="section">
                <h2>🔧 Основные endpoints</h2>
                
                <div class="endpoint">
                    <div><span class="method">POST</span> /api/tools/analyze/estimate</div>
                    <p>Анализ сметной документации</p>
                </div>
                
                <div class="endpoint">
                    <div><span class="method">POST</span> /api/tools/analyze/images</div>
                    <p>Анализ изображений и чертежей</p>
                </div>
                
                <div class="endpoint">
                    <div><span class="method">POST</span> /api/tools/analyze/documents</div>
                    <p>Анализ проектных документов</p>
                </div>
                
                <div class="endpoint">
                    <div><span class="method">GET</span> /api/tools/jobs/{job_id}/status</div>
                    <p>Получить статус задачи</p>
                </div>
                
                <div class="endpoint">
                    <div><span class="method">GET</span> /api/tools/jobs/active</div>
                    <p>Список активных задач</p>
                </div>
            </div>
            
            <div class="section">
                <h2>🔗 WebSocket</h2>
                <p>
                    <strong>URL:</strong> ws://localhost:8000/ws/<br>
                    <strong>Использование:</strong> Real-time уведомления о статусе задач
                </p>
            </div>
            
            <div class="section">
                <h2>💡 Статус системы</h2>
                <div class="endpoint">
                    <div><span class="method">GET</span> /api/tools/health</div>
                    <p>Проверка работоспособности системы</p>
                </div>
                
                <div class="endpoint">
                    <div><span class="method">GET</span> /api/tools/info</div>
                    <p>Информация о доступных инструментах</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

# Health check endpoint
@app.get("/health")
async def health_check():
    """Общая проверка работоспособности сервера"""
    return {
        "status": "healthy",
        "service": "SuperBuilder Tools API",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# API information endpoint
@app.get("/info")
async def api_info():
    """Информация об API"""
    return {
        "name": "SuperBuilder Tools API",
        "version": "1.0.0",
        "description": "REST API для инструментов анализа строительных проектов",
        "endpoints": {
            "tools": "/api/tools/*",
            "websocket": "/ws/*", 
            "documentation": ["/docs", "/redoc"],
            "health": "/health"
        },
        "features": [
            "Анализ сметной документации",
            "Анализ изображений и чертежей", 
            "Анализ проектных документов",
            "Real-time WebSocket уведомления",
            "Асинхронная обработка задач",
            "Мониторинг статуса задач"
        ]
    }

# Custom route to show all available endpoints
@app.get("/routes")
async def list_routes():
    """Список всех доступных маршрутов"""
    routes = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            routes.append({
                "path": route.path,
                "methods": list(route.methods),
                "name": route.name,
                "summary": getattr(route.endpoint, '__doc__', '').split('\n')[0] if route.endpoint.__doc__ else None
            })
    
    return {
        "total_routes": len(routes),
        "routes": routes
    }

def run_server(host: str = "0.0.0.0", port: int = 8000, debug: bool = False):
    """Запуск сервера"""
    logger.info(f"Starting server on {host}:{port} (debug={debug})")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug",
        access_log=True
    )

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SuperBuilder Tools API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to") 
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    run_server(host=args.host, port=args.port, debug=args.debug)