@echo off
title Bldr Empire v2 - Debug Startup
color 0C

echo ==================================================
echo    Bldr Empire v2 - Debug Startup
echo ==================================================
echo.

echo [INFO] This script will start services in separate visible windows for debugging
echo [INFO] Please check each window for error messages
echo.

pause

REM Change to project directory
cd /d "%~dp0"

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

REM 1. Start Redis in a visible window
echo [INFO] Starting Redis server in visible window...
if exist "redis" (
    cd /d "%~dp0redis"
    if exist "redis-server.exe" (
        start "Redis Server" cmd /k "redis-server.exe redis.windows.conf"
        echo [INFO] Redis server window opened
    ) else (
        echo [ERROR] Redis server executable not found
    )
    cd /d "%~dp0"
) else (
    echo [ERROR] Redis directory not found
)

timeout /t 3 /nobreak >nul

REM 2. Start FastAPI backend in a visible window
echo [INFO] Starting FastAPI backend in visible window...
cd /d "%~dp0"
if exist "core\bldr_api.py" (
    start "FastAPI Backend" cmd /k "python -m uvicorn core.bldr_api:app --host 127.0.0.1 --port 8000 --reload"
    echo [INFO] FastAPI backend window opened
) else (
    echo [ERROR] bldr_api.py not found
)

timeout /t 3 /nobreak >nul

REM 3. Start Frontend in a visible window
echo [INFO] Starting Frontend Dashboard in visible window...
cd /d "%~dp0web\bldr_dashboard"
if exist "package.json" (
    start "Frontend Dashboard" cmd /k "npm run dev"
    echo [INFO] Frontend dashboard window opened
) else (
    echo [ERROR] Frontend dashboard not found
)
cd /d "%~dp0"

echo.
echo ==================================================
echo    Debug Startup Complete
echo ==================================================
echo.
echo [INFO] Check each window for error messages
echo [INFO] The FastAPI backend window should show startup logs
echo [INFO] The Frontend window should show Vite development server logs
echo [INFO] The Redis window should show Redis server logs
echo.
echo To stop all services, close the windows or run one_click_stop.bat
echo.
pause