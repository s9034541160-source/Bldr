@echo off
REM Bldr Empire v2 - Start All Services Script
REM This script starts all required services for testing the real Celery implementation

echo 🚀 Starting Bldr Empire v2 Services for Testing...

REM Start Redis if not already running
echo 🔄 Checking Redis...
docker ps | findstr redis-bldr >nul
if %errorlevel% neq 0 (
    echo 🔄 Starting Redis container...
    docker run -d -p 6379:6379 --name redis-bldr redis:alpine
    timeout /t 5 /nobreak >nul
)

REM Start FastAPI server
echo 🔄 Starting FastAPI server on port 8001...
start /b uvicorn core.bldr_api:app --host 0.0.0.0 --port 8001
timeout /t 5 /nobreak >nul

REM Start Celery worker
echo 🔄 Starting Celery worker...
start /b celery -A core.celery_app worker --loglevel=info --concurrency=2
timeout /t 5 /nobreak >nul

REM Start Celery beat
echo 🔄 Starting Celery beat...
start /b celery -A core.celery_app beat --loglevel=info
timeout /t 3 /nobreak >nul

echo ✅ All services started successfully!
echo    Redis: localhost:6379
echo    FastAPI Server: http://localhost:8001
echo    Celery Worker: running in background
echo    Celery Beat: running in background
echo.
echo 💡 To stop services, run stop_services.bat or manually kill the processes
echo 💡 To test the implementation, run: python test_celery.py