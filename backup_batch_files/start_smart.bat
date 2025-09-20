@echo off
title Bldr Empire v2 - Smart Startup
color 0A

echo ==================================================
echo    Bldr Empire v2 - Smart Startup
echo ==================================================
echo.

REM Kill any existing processes on our ports (EXCEPT Neo4j)
echo [INFO] Cleaning up existing processes (excluding Neo4j)...
taskkill /F /IM redis-server.exe >nul 2>&1
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

REM 1. Start Redis (needed by FastAPI backend)
echo [INFO] Starting Redis server (required by FastAPI)...
set REDIS_STARTED=0
if exist "redis" (
    cd /d "%~dp0redis"
    if exist "redis-server.exe" (
        start /MIN "Redis Server" cmd /c "redis-server.exe redis.windows.conf"
        timeout /t 3 /nobreak >nul
        REM Check if Redis started
        netstat -an | findstr ":6379 " >nul
        if %errorlevel% equ 0 (
            echo [INFO] Redis server started successfully
            set REDIS_STARTED=1
        ) else (
            echo [WARN] Redis server may not have started correctly
        )
    ) else (
        echo [ERROR] Redis server executable not found
    )
    cd /d "%~dp0"
) else (
    echo [ERROR] Redis directory not found
)
timeout /t 2 /nobreak >nul

REM 2. Start Qdrant (needed by FastAPI backend)
echo [INFO] Starting Qdrant vector database (required by FastAPI)...
set QDRANT_STARTED=0
docker version >nul 2>&1
if %errorlevel% equ 0 (
    docker start qdrant-bldr >nul 2>&1
    if %errorlevel% neq 0 (
        docker run -d -p 6333:6333 -p 6334:6334 --name qdrant-bldr qdrant/qdrant:v1.7.0 >nul 2>&1
    )
    timeout /t 3 /nobreak >nul
    docker ps | findstr qdrant-bldr >nul
    if %errorlevel% equ 0 (
        echo [INFO] Qdrant container started successfully
        set QDRANT_STARTED=1
    ) else (
        echo [WARN] Qdrant container may not have started correctly
    )
) else (
    echo [WARN] Docker not available. Qdrant will not be started.
)
timeout /t 2 /nobreak >nul

REM 3. Start FastAPI backend (this will start its own Celery workers)
echo [INFO] Starting FastAPI backend (this will start Celery internally)...
set BACKEND_STARTED=0
cd /d C:\Bldr
if exist "core\bldr_api.py" (
    start "FastAPI Backend" cmd /k "cd /d C:\Bldr && python -m uvicorn core.bldr_api:app --host 127.0.0.1 --port 8000 --reload"
    echo [INFO] FastAPI backend started in visible window
    echo [INFO] Please wait for it to fully initialize (watch the window)
    set BACKEND_STARTED=1
) else (
    echo [ERROR] bldr_api.py not found in C:\Bldr
    echo [INFO] Current directory: %CD%
    dir core\bldr_api.py >nul 2>&1
    if %errorlevel% equ 0 (
        echo [INFO] File exists in core directory
    ) else (
        echo [ERROR] File not found in core directory
    )
)
timeout /t 5 /nobreak >nul

REM 4. Start Frontend
echo [INFO] Starting Frontend Dashboard...
set FRONTEND_STARTED=0
cd /d "%~dp0web\bldr_dashboard"
if exist "package.json" (
    REM Check if port 3001 is already in use
    netstat -ano | findstr :3001 >nul
    if %errorlevel% equ 0 (
        echo [WARN] Port 3001 is already in use. Attempting to kill existing process...
        for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3001') do (
            taskkill /F /PID %%a >nul 2>&1
        )
        timeout /t 5 /nobreak >nul
    )
    
    start "Frontend Dashboard" cmd /k "npm run dev"
    echo [INFO] Frontend Dashboard started in visible window
    set FRONTEND_STARTED=1
) else (
    echo [ERROR] Frontend dashboard not found
)
cd /d "%~dp0"
timeout /t 5 /nobreak >nul

echo.
echo ==================================================
echo    Service Status Summary
echo ==================================================
echo Redis:         %REDIS_STARTED%
echo Qdrant:        %QDRANT_STARTED%
echo FastAPI:       %BACKEND_STARTED%
echo Frontend:      %FRONTEND_STARTED%
echo.

REM Check overall status
set ESSENTIAL_STARTED=1
if %REDIS_STARTED% equ 0 set ESSENTIAL_STARTED=0
if %BACKEND_STARTED% equ 0 set ESSENTIAL_STARTED=0
if %FRONTEND_STARTED% equ 0 set ESSENTIAL_STARTED=0

if %ESSENTIAL_STARTED% equ 1 (
    echo [SUCCESS] Essential services started successfully!
    echo [INFO] Please check the FastAPI and Frontend windows for initialization logs
    echo [INFO] The system will be ready when both windows show successful startup messages
) else (
    echo [ERROR] Some essential services failed to start.
    echo [INFO] Please check the error messages above.
)

echo.
echo Services:
echo   - Redis: localhost:6379
echo   - Qdrant: http://localhost:6333 (if Docker is working)
echo   - FastAPI Backend: http://localhost:8000
echo   - Frontend Dashboard: http://localhost:3001
echo.
echo [IMPORTANT] The FastAPI backend handles Celery internally - no need to start it separately!
echo [IMPORTANT] Neo4j is NOT managed by this script - please start/stop it manually as needed
echo.
echo To stop all services, run one_click_stop.bat
echo.
echo Press any key to continue...
pause >nul