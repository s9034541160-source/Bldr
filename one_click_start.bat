@echo off
title Bldr Empire v2 - One-Click Startup
color 0A

echo ==================================================
echo    Bldr Empire v2 - One-Click Startup
echo ==================================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [INFO] Running with administrator privileges
) else (
    echo [WARN] Not running as administrator. Some features may not work correctly.
)

REM Kill any existing processes on our ports with more thorough approach
echo [INFO] Cleaning up existing processes...
taskkill /F /IM redis-server.exe >nul 2>&1
taskkill /F /IM java.exe >nul 2>&1
taskkill /F /IM docker.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
taskkill /F /IM uvicorn.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM celery.exe >nul 2>&1

REM Additional cleanup for Neo4j processes - wait a bit more and try again
echo [INFO] Performing additional process cleanup...
timeout /t 3 /nobreak >nul
taskkill /F /IM java.exe >nul 2>&1
taskkill /F /IM redis-server.exe >nul 2>&1

timeout /t 5 /nobreak >nul

REM Check and restore NTD base if needed
echo [INFO] Checking NTD base...
if not exist "I:\docs\clean_base\construction" (
    echo [INFO] NTD base not found. Starting restoration process...
    start /MIN "NTD Restore" cmd /c "python restore_ntd.py ^& pause"
    timeout /t 10 /nobreak >nul
) else (
    echo [INFO] NTD base already exists
)

REM Change to project directory
cd /d "%~dp0"

REM Check if Java is installed and is the correct version
echo [INFO] Checking Java installation...
java -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Java is not installed or not in PATH. Neo4j requires Java to run.
    echo.
    echo [INFO] Please install Java 21 or later:
    echo [INFO] 1. Go to https://adoptium.net/
    echo [INFO] 2. Download "OpenJDK 21 ^(LTS^) JDK"
    echo [INFO] 3. Run the installer and follow the instructions
    echo [INFO] 4. After installation, restart your computer
    echo [INFO] 5. Run this script again
    echo.
    echo [INFO] Note: Make sure to install the JDK ^(not JRE^) version.
    echo.
    pause
    exit /b 1
)
echo [INFO] Java is installed and accessible.

REM Check Neo4j status
echo [INFO] Checking Neo4j status...
python check_neo4j_status.py > neo4j_status.tmp
findstr /C:"[WARN] Neo4j Desktop is running but no database instance is active" neo4j_status.tmp >nul
if %errorlevel% == 0 (
    echo.
    echo [WARN] Neo4j Desktop is running but no database instance is active!
    echo [INFO] Please start a database instance in Neo4j Desktop with these settings:
    echo [INFO]   - Credentials: neo4j/neo4j (default)
    echo [INFO]   - Bolt port: 7687
    echo [INFO]   - HTTP port: 7474
    echo.
    echo [INFO] Press any key after starting the database instance, or Ctrl+C to exit...
    pause >nul
)
del /q neo4j_status.tmp >nul 2>&1

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

REM 2. Start Redis
echo [INFO] Starting Redis server...
if exist "redis" (
    cd /d "%~dp0redis"
    if exist "redis-server.exe" (
        start /MIN "Redis Server" cmd /c "redis-server.exe redis.windows.conf ^& pause"
        echo [INFO] Redis server started
    ) else (
        echo [ERROR] Redis server executable not found
    )
    cd /d "%~dp0"
) else (
    echo [ERROR] Redis directory not found
)
timeout /t 5 /nobreak >nul

REM 3. Start Qdrant - Check if Docker is available and working
echo [INFO] Starting Qdrant vector database...
docker version >nul 2>&1
if %errorlevel% equ 0 (
    REM Try to start existing container
    docker start qdrant-bldr >nul 2>&1
    if %errorlevel% neq 0 (
        REM Try to create new container
        docker run -d -p 6333:6333 -p 6334:6334 --name qdrant-bldr qdrant/qdrant:v1.7.0 >nul 2>&1
        if %errorlevel% neq 0 (
            echo [WARN] Failed to start Qdrant container. Docker may not be properly configured.
            echo [INFO] System will use in-memory storage as fallback.
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
timeout /t 5 /nobreak >nul

REM 4. Start Celery worker and beat
echo [INFO] Starting Celery services...
cd /d "%~dp0"
if exist "core" (
    start /MIN "Celery Worker" cmd /c "celery -A core.celery_app worker --loglevel=info --concurrency=2 ^& pause"
    timeout /t 2 /nobreak >nul
    start /MIN "Celery Beat" cmd /c "celery -A core.celery_app beat --loglevel=info ^& pause"
    echo [INFO] Celery services started
) else (
    echo [ERROR] Core directory not found
)
timeout /t 3 /nobreak >nul

REM 5. Start FastAPI backend with better error handling
echo [INFO] Starting FastAPI backend...
cd /d "%~dp0"
if exist "core\bldr_api.py" (
    start /MIN "FastAPI Backend" cmd /c "python -m uvicorn core.bldr_api:app --host 127.0.0.1 --port 8000 --reload ^& pause"
    echo [INFO] FastAPI backend started
) else (
    echo [ERROR] bldr_api.py not found
)
timeout /t 30 /nobreak >nul

REM 6. Start Telegram Bot
echo [INFO] Starting Telegram Bot...
cd /d "%~dp0"
if exist "integrations\telegram_bot.py" (
    start /MIN "Telegram Bot" cmd /c "python integrations/telegram_bot.py ^& pause"
    echo [INFO] Telegram Bot started
) else (
    echo [ERROR] Telegram bot script not found
)
timeout /t 2 /nobreak >nul

REM 7. Start Frontend
echo [INFO] Starting Frontend Dashboard...
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
    start /MIN "Frontend Dashboard" cmd /c "npm run dev ^& pause"
    echo [INFO] Frontend Dashboard started
) else (
    echo [ERROR] Frontend dashboard not found
)
cd /d "%~dp0"
timeout /t 15 /nobreak >nul

REM Wait for services to fully start
echo [INFO] Waiting for services to initialize...
timeout /t 30 /nobreak >nul

REM Check if backend is responding with improved health check
echo [INFO] Checking backend status...
powershell -Command "& {try { $response = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' -Method GET -TimeoutSec 30; if ($response.StatusCode -eq 200) { $content = $response.Content | ConvertFrom-Json; Write-Host '[INFO] Backend status:' $content.status; Write-Host '[INFO] Database:' $content.components.db; Write-Host '[INFO] Celery:' $content.components.celery; if ($content.status -eq 'ok') { Write-Host '[INFO] Backend is fully healthy' } else { Write-Host '[WARN] Backend is running but some components are not healthy' } } else { Write-Host '[WARN] Backend responded with status:' $response.StatusCode } } catch { Write-Host '[ERROR] Backend not responding -' $_.Exception.Message }}"

echo.
echo ==================================================
echo    Bldr Empire v2 Started Successfully!
echo ==================================================
echo Services:
echo   - Redis: localhost:6379
echo   - Neo4j: http://localhost:7474 (if database instance is running)
echo   - Qdrant: http://localhost:6333 (if Docker is working)
echo   - FastAPI Backend: http://localhost:8000
echo   - Frontend Dashboard: http://localhost:3001
echo.
echo Credentials:
echo   - Neo4j: neo4j/neo4j (default)
echo.
echo For troubleshooting, see TROUBLESHOOTING.md
echo.
echo Opening frontend in your browser...
start http://localhost:3001
echo.
echo To stop all services, run one_click_stop.bat
echo.
echo Press any key to continue...
pause >nul