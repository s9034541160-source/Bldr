"""
BLDR.EMPIRE v3.0 - Main FastAPI Application
Система управления строительными проектами с ИИ
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import sys

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Создание приложения FastAPI
app = FastAPI(
    title="BLDR.EMPIRE API",
    description="API для системы управления строительными проектами с ИИ",
    version="3.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
from backend.api.endpoints import auth, health, llm, rag, tools
app.include_router(auth.router, prefix="/api")
app.include_router(health.router, prefix="/api")
app.include_router(llm.router, prefix="/api")
app.include_router(rag.router, prefix="/api")
app.include_router(tools.router, prefix="/api")


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "BLDR.EMPIRE v3.0 API",
        "version": "3.0.0",
        "status": "running"
    }


@app.get("/api/health")
async def health_check():
    """Health check эндпоинт"""
    return {
        "status": "healthy",
        "service": "BLDR.EMPIRE API"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Глобальный обработчик исключений"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

