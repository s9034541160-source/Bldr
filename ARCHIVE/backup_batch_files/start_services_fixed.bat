@echo off
title Bldr Empire v2 - Fixed Startup
color 0A

echo ==================================================
echo    Bldr Empire v2 - Fixed Startup
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

REM 1. Start Redis
echo [INFO] Starting Redis server...
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

REM 2. Start Qdrant
echo [INFO] Starting Qdrant vector database...
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

REM 3. Start Celery worker and beat
echo [INFO] Starting Celery services...
set CELERY_STARTED=0
if exist "core" (
    start /MIN "Celery Worker" cmd /c "celery -A core.celery_app worker --loglevel=info --concurrency=2"
    timeout /t 2 /nobreak >nul
    start /MIN "Celery Beat" cmd /c "celery -A core.celery_app beat --loglevel=info"
    timeout /t 2 /nobreak >nul
    echo [INFO] Celery services started
    set CELERY_STARTED=1
) else (
    echo [ERROR] Core directory not found
)
timeout /t 2 /nobreak >nul

REM 4. Start FastAPI backend with verification
echo [INFO] Starting FastAPI backend...
set BACKEND_STARTED=0
cd /d "%~dp0"
if exist "core\bldr_api.py" (
    start /MIN "FastAPI Backend" cmd /c "python -m uvicorn core.bldr_api:app --host 127.0.0.1 --port 8000 --reload"
    echo [INFO] Waiting for FastAPI backend to start...
    timeout /t 10 /nobreak >nul
    
    REM Check if backend is responding
    powershell -Command "& {try { $response = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' -Method GET -TimeoutSec 5; if ($response.StatusCode -eq 200) { Write-Output 'SUCCESS' } else { Write-Output 'FAILED' } } catch { Write-Output 'FAILED' }}" > backend_check.tmp
    findstr /C:"SUCCESS" backend_check.tmp >nul
    if %errorlevel% == 0 (
        echo [INFO] FastAPI backend started successfully
        set BACKEND_STARTED=1
    ) else (
        echo [ERROR] FastAPI backend failed to start
        echo [INFO] Check the FastAPI terminal window for errors
    )
    del /q backend_check.tmp >nul 2>&1
) else (
    echo [ERROR] bldr_api.py not found
)
timeout /t 2 /nobreak >nul

REM 5. Start Telegram Bot
echo [INFO] Starting Telegram Bot...
set TELEGRAM_STARTED=0
cd /d "%~dp0"
if exist "integrations\telegram_bot.py" (
    start /MIN "Telegram Bot" cmd /c "python integrations/telegram_bot.py"
    echo [INFO] Telegram Bot started
    set TELEGRAM_STARTED=1
) else (
    echo [ERROR] Telegram bot script not found
)
timeout /t 2 /nobreak >nul

REM 6. Start Frontend with port check
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
    
    start /MIN "Frontend Dashboard" cmd /c "npm run dev"
    echo [INFO] Frontend Dashboard started
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
echo Celery:        %CELERY_STARTED%
echo FastAPI:       %BACKEND_STARTED%
echo Telegram Bot:  %TELEGRAM_STARTED%
echo Frontend:      %FRONTEND_STARTED%
echo.

REM Check overall status
set ALL_STARTED=1
if %REDIS_STARTED% equ 0 set ALL_STARTED=0
if %CELERY_STARTED% equ 0 set ALL_STARTED=0
if %BACKEND_STARTED% equ 0 set ALL_STARTED=0
if %FRONTEND_STARTED% equ 0 set ALL_STARTED=0

if %ALL_STARTED% equ 1 (
    echo [SUCCESS] All services started successfully!
    echo [INFO] Opening frontend in your browser...
    start http://localhost:3001
) else (
    echo [WARN] Some services failed to start. Check the individual service status above.
    echo [INFO] Please check the terminal windows for error messages.
)

echo.
echo Services:
echo   - Redis: localhost:6379
echo   - Qdrant: http://localhost:6333 (if Docker is working)
echo   - FastAPI Backend: http://localhost:8000
echo   - Frontend Dashboard: http://localhost:3001
echo.
echo To stop all services, run one_click_stop.bat
echo.
echo Press any key to continue...
pause >nul