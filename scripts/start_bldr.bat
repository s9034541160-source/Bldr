@echo off
title Bldr Empire v2 - Unified Startup
color 0A
setlocal enabledelayedexpansion

echo ==================================================
echo    Bldr Empire v2 - Unified Startup
echo ==================================================
echo.

REM Change to project directory
cd /d "%~dp0"

REM Kill any existing processes on our ports (EXCEPT Java/Neo4j)
echo [INFO] Cleaning up existing processes (excluding Neo4j and other Python apps)...
taskkill /F /IM redis-server.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
taskkill /F /IM uvicorn.exe >nul 2>&1
REM Don't kill all Python processes - only kill specific Bldr processes by port
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3001') do taskkill /F /PID %%a >nul 2>&1
taskkill /F /IM celery.exe >nul 2>&1

timeout /t 3 /nobreak >nul

REM Load environment variables
if exist ".env" (
    REM Load .env ignoring comment lines starting with # and preserving full lines
    for /f "usebackq eol=# delims= tokens=*" %%i in (".env") do (
        set "%%i"
    )
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

REM Check if Neo4j is running
echo [INFO] Checking Neo4j status...
python check_neo4j_status.py
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
timeout /t 5 /nobreak >nul

REM 2. Start Qdrant (if Docker is available)
echo [INFO] Starting Qdrant vector database...
REM If Qdrant already listening on 6333, skip Docker start and just report OK
netstat -ano | findstr ":6333" >nul
if %errorlevel% equ 0 (
    echo [INFO] Qdrant is already running on port 6333.
) else (
    set "DOCKER_BIN=docker"
    where docker >nul 2>&1
    if not %errorlevel%==0 (
        if exist "%ProgramFiles%\Docker\Docker\resources\bin\docker.exe" set "DOCKER_BIN=%ProgramFiles%\Docker\Docker\resources\bin\docker.exe"
        if exist "%ProgramFiles%\Docker\Docker\resources\bin\com.docker.cli.exe" set "DOCKER_BIN=%ProgramFiles%\Docker\Docker\resources\bin\com.docker.cli.exe"
    )
    "%DOCKER_BIN%" version >nul 2>&1
    if %errorlevel% equ 0 (
        echo [INFO] Docker detected: %DOCKER_BIN%
        "%DOCKER_BIN%" ps >nul 2>&1
        if %errorlevel% neq 0 (
            echo [WARN] Docker CLI available but daemon not reachable. Will try to start container anyway.
        )
        "%DOCKER_BIN%" start qdrant-bldr >nul 2>&1
        if %errorlevel% neq 0 (
            "%DOCKER_BIN%" run -d -p 6333:6333 -p 6334:6334 --name qdrant-bldr qdrant/qdrant:v1.7.0 >nul 2>&1
            if %errorlevel% neq 0 (
                echo [WARN] Failed to start Qdrant container. System will use in-memory storage as fallback.
            ) else (
                echo [INFO] Qdrant container created and started
            )
        ) else (
            echo [INFO] Qdrant container already running
        )
    ) else (
        echo [WARN] Docker not available. Qdrant will not be started.
        echo [INFO] System will use in-memory storage as fallback.
    )
)
timeout /t 5 /nobreak >nul

REM 3. Start Celery worker and beat
echo [INFO] Starting Celery services...
cd /d "%~dp0"
if exist "core" (
    start /MIN "Celery Worker" cmd /c "celery -A core.celery_app worker --loglevel=info --concurrency=2"
    timeout /t 2 /nobreak >nul
    start /MIN "Celery Beat" cmd /c "celery -A core.celery_app beat --loglevel=info"
    echo [INFO] Celery services started
) else (
    echo [ERROR] Core directory not found
)
timeout /t 3 /nobreak >nul

REM 4. Start FastAPI backend
echo [INFO] Starting FastAPI backend...
cd /d "%~dp0"
if exist "backend\main.py" (
    start "FastAPI Backend" cmd /k "python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"
    echo [INFO] FastAPI backend started in visible window
) else (
    echo [ERROR] main.py not found
)
echo [INFO] Waiting for backend to initialize...
set backend_ready=false
for /l %%i in (1, 1, 60) do (
    curl -s http://localhost:8000/health >nul 2>&1
    if !errorlevel! equ 0 (
        set backend_ready=true
        goto backend_ready
    )
    timeout /t 1 /nobreak >nul
)
:backend_ready
if "%backend_ready%"=="false" (
    echo [ERROR] Backend failed to start in time
) else (
    echo [INFO] Backend is ready
)

REM 5. Start Frontend
echo [INFO] Starting Frontend Dashboard...
set "FRONTEND_DIR=%~dp0web\bldr_dashboard"
if exist "%FRONTEND_DIR%\package.json" (
    echo [INFO] Preparing Frontend dependencies...
    pushd "%FRONTEND_DIR%"
    if not exist "node_modules" (
        echo [INFO] node_modules not found -> npm ci
        call npm ci
        if %errorlevel% neq 0 (
            echo [WARN] npm ci failed. If you see EPERM unlink for esbuild.exe:
            echo        1) Close all Node processes and antivirus real-time scan for this folder
            echo        2) Manually delete node_modules\@esbuild
            echo        3) Re-run this script
        ) else (
            echo [INFO] Dependencies installed
        )
    ) else (
        if not exist "node_modules\.bin\vite.cmd" (
            echo [WARN] vite not found -> npm ci
            call npm ci
            if %errorlevel% neq 0 (
                echo [WARN] npm ci failed. See hints above (EPERM / antivirus / close node)
            ) else (
                echo [INFO] Dependencies repaired
            )
        ) else (
            echo [INFO] node_modules OK (vite present)
        )
    )

    REM Check if port 3001 is already in use
    netstat -ano | findstr :3001 >nul
    if %errorlevel% equ 0 (
        echo [WARN] Port 3001 is already in use. Attempting to kill existing process...
        for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3001') do (
            taskkill /F /PID %%a >nul 2>&1
        )
    )
    echo [INFO] Launching Frontend Dashboard...
    start "Frontend Dashboard" cmd /k "cd /d ""%FRONTEND_DIR%"" && npm run dev"
    popd
    timeout /t 15 /nobreak >nul
    echo [INFO] Opening browser to http://localhost:3001
    start "" "http://localhost:3001"

) else (
    echo [ERROR] Frontend dashboard not found
)

echo [INFO] Continuing startup...
timeout /t 5 /nobreak >nul

REM 6. Start Telegram Bot
echo [INFO] Starting Telegram Bot...
cd /d "%~dp0"
if exist "integrations\telegram_bot.py" (
    if "%TELEGRAM_BOT_TOKEN%"=="" (
        echo [WARN] TELEGRAM_BOT_TOKEN not set. Skipping Telegram Bot startup.
    ) else (
        echo [INFO] Launching Telegram Bot in a separate window...
        start /MIN "Telegram Bot" cmd /k "python integrations/telegram_bot.py"
    )
) else (
    echo [WARN] Telegram bot script not found. Skipping.
)
cd /d "%~dp0"

echo.
echo ==================================================
echo    Startup Complete
echo ==================================================
echo Services:
echo   - Redis: localhost:6379
echo   - Neo4j: http://localhost:7474 (make sure it's running with neo4j/neopassword)
echo   - Qdrant: http://localhost:6333 (if Docker is working)
echo   - FastAPI Backend: http://localhost:8000
echo   - Frontend Dashboard: http://localhost:3001
echo   - Telegram Bot: Running in background (check for token in .env)
echo.
echo [IMPORTANT] Check the FastAPI and Frontend windows for initialization logs
echo [IMPORTANT] The system will be ready when both windows show successful startup messages
echo.
echo To stop all services, run stop_bldr.bat
echo.
echo Startup script completed. Services are running in background windows.