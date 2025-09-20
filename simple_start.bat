@echo off
title Bldr Empire v2 - Simple Startup
color 0A

echo ==================================================
echo    Bldr Empire v2 - Simple Startup
echo ==================================================
echo.

REM Change to project directory
cd /d "%~dp0"

REM 1. Start Redis
echo [INFO] Starting Redis server...
if exist "redis" (
    cd /d "%~dp0redis"
    if exist "redis-server.exe" (
        start /MIN "Redis Server" redis-server.exe redis.windows.conf
        echo [INFO] Redis server started
    ) else (
        echo [ERROR] Redis server executable not found
    )
    cd /d "%~dp0"
) else (
    echo [ERROR] Redis directory not found
)
timeout /t 5 /nobreak >nul

REM 2. Start FastAPI backend
echo [INFO] Starting FastAPI backend...
cd /d "%~dp0"
if exist "core\bldr_api.py" (
    start /MIN "FastAPI Backend" cmd /c "uvicorn core.bldr_api:app --host 0.0.0.0 --port 8000 --reload"
    echo [INFO] FastAPI backend started
) else (
    echo [ERROR] bldr_api.py not found
)
timeout /t 10 /nobreak >nul

REM 3. Start Frontend
echo [INFO] Starting Frontend Dashboard...
cd /d "%~dp0web\bldr_dashboard"
if exist "package.json" (
    start /MIN "Frontend Dashboard" cmd /c "npm run dev"
    echo [INFO] Frontend Dashboard started
) else (
    echo [ERROR] Frontend dashboard not found
)
cd /d "%~dp0"
timeout /t 15 /nobreak >nul

REM Wait for services to fully start
echo [INFO] Waiting for services to initialize...
timeout /t 20 /nobreak >nul

REM Check if backend is responding
echo [INFO] Checking backend status...
powershell -Command "& {try { $response = Invoke-WebRequest -Uri 'http://localhost:8000/health' -Method GET -TimeoutSec 15; if ($response.StatusCode -eq 200) { Write-Host '[INFO] Backend is responding' } else { Write-Host '[WARN] Backend may not be ready (Status: '$response.StatusCode')' } } catch { Write-Host '[ERROR] Backend not responding -' $_.Exception.Message }}"

echo.
echo ==================================================
echo    Bldr Empire v2 Started Successfully!
echo ==================================================
echo Services:
echo   - Redis: localhost:6379
echo   - FastAPI Backend: http://localhost:8000
echo   - Frontend Dashboard: http://localhost:3001
echo.
echo Opening frontend in your browser...
start http://localhost:3001
echo.
echo To stop all services, close the command windows or run taskkill commands
echo.
echo Press any key to continue...
pause >nul