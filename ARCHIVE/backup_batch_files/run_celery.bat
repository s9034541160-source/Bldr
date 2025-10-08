@echo off
REM Bldr Empire v2 - Celery Services Startup Script (Windows)
REM This script starts all required services for the Bldr Empire system

echo 🚀 Starting Bldr Empire v2 Services...

REM Check if Redis is installed
redis-server --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  Redis not found. Please install Redis first:
    echo    Download from: https://redis.io/download/
    echo    Or use Docker: docker run -p 6379:6379 redis
    exit /b 1
)

REM Start Redis server in background
echo 🔄 Starting Redis server...
start /b redis-server --daemonize yes
timeout /t 2 /nobreak >nul

REM Check if Redis is running
redis-cli ping >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Failed to start Redis server
    exit /b 1
) else (
    echo ✅ Redis server is running
)

REM Start Celery worker in background
echo 🔄 Starting Celery worker...
start /b celery -A core.celery_app worker --loglevel=info --concurrency=4
timeout /t 3 /nobreak >nul

REM Start Celery beat in background
echo 🔄 Starting Celery beat...
start /b celery -A core.celery_app beat --loglevel=info
timeout /t 2 /nobreak >nul

REM Start FastAPI server
echo 🔄 Starting FastAPI server...
start /b python -m core.main
timeout /t 3 /nobreak >nul

echo ✅ All services started successfully!
echo    Redis: localhost:6379
echo    Celery Worker: running in background
echo    Celery Beat: running in background
echo    FastAPI Server: http://localhost:8000
echo.
echo 💡 To stop services, close this window or run:
echo    taskkill /f /im celery.exe
echo    taskkill /f /im uvicorn.exe
echo    redis-cli shutdown

REM Keep window open
pause