@echo off
title Bldr Empire v2 - Final Startup
color 0A

echo ==================================================
echo    Bldr Empire v2 - Final Startup
echo ==================================================
echo.

REM Kill any existing processes on our ports
echo [INFO] Cleaning up existing processes...
taskkill /F /IM redis-server.exe >nul 2>&1
taskkill /F /IM java.exe >nul 2>&1
taskkill /F /IM docker.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
taskkill /F /IM uvicorn.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM celery.exe >nul 2>&1

timeout /t 3 /nobreak >nul

REM Change to project directory
cd /d "%~dp0"

REM Check if Java is installed
echo [INFO] Checking Java installation...
java -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Java is not installed or not in PATH.
    echo [INFO] Please install Java 21 or later from https://adoptium.net/
    pause
    exit /b 1
)
echo [INFO] Java is installed and accessible.

REM Load environment variables
if exist ".env" (
    for /f "tokens=*" %%i in (.env) do set %%i
    echo [INFO] Environment variables loaded from .env
) else (
    echo [WARN] .env file not found, using default values
    set NEO4J_USER=neo4j
    set NEO4J_PASSWORD=neopassword
    set REDIS_URL=redis://localhost:6379
    set NEO4J_URI=neo4j://localhost:7687
)

echo [INFO] Environment variables:
echo   - NEO4J_USER: %NEO4J_USER%
echo   - NEO4J_PASSWORD: %NEO4J_PASSWORD%
echo   - NEO4J_URI: %NEO4J_URI%
echo.

REM 1. Start Redis
echo [INFO] Starting Redis server...
if exist "redis" (
    cd /d "%~dp0redis"
    if exist "redis-server.exe" (
        start /MIN "Redis Server" cmd /c "redis-server.exe redis.windows.conf"
        echo [INFO] Redis server started
    ) else (
        echo [ERROR] Redis server executable not found
    )
    cd /d "%~dp0"
) else (
    echo [ERROR] Redis directory not found
)
timeout /t 3 /nobreak >nul

REM 2. Start Celery worker and beat
echo [INFO] Starting Celery services...
if exist "core" (
    start /MIN "Celery Worker" cmd /c "celery -A core.celery_app worker --loglevel=info --concurrency=2"
    timeout /t 2 /nobreak >nul
    start /MIN "Celery Beat" cmd /c "celery -A core.celery_app beat --loglevel=info"
    echo [INFO] Celery services started
) else (
    echo [ERROR] Core directory not found
)
timeout /t 3 /nobreak >nul

echo.
echo ==================================================
echo    Services Started
echo ==================================================
echo [INFO] Redis: Started (if no error above)
echo [INFO] Celery: Started (if no error above)
echo.
echo [INFO] To start the backend, run this in a new terminal:
echo        cd c:\Bldr
echo        python -m uvicorn core.bldr_api:app --host 127.0.0.1 --port 8000 --reload
echo.
echo [INFO] To start the frontend, run this in a new terminal:
echo        cd c:\Bldr\web\bldr_dashboard
echo        npm run dev
echo.
echo [INFO] Both commands will show detailed logs and keep running
echo.
echo [INFO] After both are running, open http://localhost:3001 in your browser
echo.
echo To stop all services, run one_click_stop.bat
echo.
pause