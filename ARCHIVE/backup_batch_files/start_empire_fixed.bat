@echo off
title Bldr Empire v2 - Startup Script
color 0A

echo ==================================================
echo    Bldr Empire v2 - Enhanced Startup Script
echo ==================================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [INFO] Running with administrator privileges
) else (
    echo [WARN] Not running as administrator. Some features may not work correctly.
)

REM Kill any existing processes on our ports
echo [INFO] Cleaning up existing processes...
taskkill /F /PID 1234 >nul 2>&1
taskkill /F /PID 6379 >nul 2>&1
taskkill /F /PID 7474 >nul 2>&1
taskkill /F /PID 6333 >nul 2>&1
taskkill /F /PID 8000 >nul 2>&1
taskkill /F /PID 3000 >nul 2>&1

timeout /t 3 /nobreak >nul

REM 1. Start Redis
echo [INFO] Starting Redis server...
cd /d "%~dp0redis"
start /MIN "Redis Server" redis-server.exe redis.windows.conf
cd /d "%~dp0"
timeout /t 5 /nobreak >nul

REM 2. Start Neo4j
echo [INFO] Starting Neo4j database...
cd /d "C:\Program Files\Neo4j\neo4j-community-5.20.0\bin"
start /MIN "Neo4j" neo4j.bat start
cd /d "%~dp0"
timeout /t 10 /nobreak >nul

REM 3. Start Qdrant
echo [INFO] Starting Qdrant vector database...
docker start qdrant-bldr >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Creating new Qdrant container...
    docker run -d -p 6333:6333 -p 6334:6334 --name qdrant-bldr qdrant/qdrant:v1.7.0
) else (
    echo [INFO] Qdrant container already running
)
timeout /t 5 /nobreak >nul

REM 4. Start Celery worker and beat
echo [INFO] Starting Celery services...
cd /d "%~dp0"
start /MIN "Celery Worker" cmd /c "celery -A core.celery_app worker --loglevel=info --concurrency=4"
timeout /t 3 /nobreak >nul
start /MIN "Celery Beat" cmd /c "celery -A core.celery_app beat --loglevel=info"
timeout /t 2 /nobreak >nul

REM 5. Start FastAPI backend
echo [INFO] Starting FastAPI backend...
start /MIN "FastAPI Backend" cmd /c "uvicorn core.bldr_api:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 5 /nobreak >nul

REM 6. Start Telegram Bot
echo [INFO] Starting Telegram Bot...
start /MIN "Telegram Bot" cmd /c "python integrations/telegram_bot.py"
timeout /t 2 /nobreak >nul

REM 7. Restore NTD base if needed
echo [INFO] Checking NTD base...
if not exist "I:\docs\clean_base\construction" (
    echo [INFO] Restoring NTD base...
    python restore_ntd.py
)

REM 8. Start Frontend
echo [INFO] Starting Frontend Dashboard...
cd /d "%~dp0web\bldr_dashboard"
start /MIN "Frontend Dashboard" cmd /c "npm run dev"
cd /d "%~dp0"
timeout /t 10 /nobreak >nul

echo.
echo ==================================================
echo    Bldr Empire v2 Services Started Successfully!
echo ==================================================
echo Services:
echo   - Redis: localhost:6379
echo   - Neo4j: http://localhost:7474
echo   - Qdrant: http://localhost:6333
echo   - FastAPI Backend: http://localhost:8000
echo   - Frontend Dashboard: http://localhost:3000
echo.
echo Credentials:
echo   - Neo4j: neo4j/neo4j
echo.
echo To stop all services, run stop_empire.bat
echo.
echo Press any key to continue...
pause >nul