@echo off
setlocal enabledelayedexpansion

title Bldr Empire v2 - All Services
echo ====================================================
echo   Bldr Empire v2 - Complete Services Launcher
echo ====================================================
echo.

REM Change to the project directory
cd /d "c:\Bldr"

echo Stopping any existing Bldr processes...
echo.

REM Kill existing processes on our ports
echo Checking for existing processes on port 8000 (API)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo Killing process %%a on port 8000
    taskkill /f /pid %%a 2>nul
)

echo Checking for existing processes on port 6379 (Redis)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :6379 ^| findstr LISTENING') do (
    echo Killing process %%a on port 6379
    taskkill /f /pid %%a 2>nul
)

timeout /t 3 /nobreak >nul

REM Start Redis server if not already running
echo Starting Redis server...
start "Redis Server" /min redis-server
timeout /t 5 /nobreak >nul

REM Start Celery worker
echo Starting Celery worker...
start "Celery Worker" /min cmd /c "cd /d c:\Bldr && start_celery.bat"
timeout /t 5 /nobreak >nul

REM Start Celery beat
echo Starting Celery beat...
start "Celery Beat" /min cmd /c "cd /d c:\Bldr && start_celery_beat.bat"
timeout /t 5 /nobreak >nul

REM Start the main API server (this window will show logs)
echo Starting Bldr API server...
echo.
echo The API server is now running on http://localhost:8000
echo Press Ctrl+C to stop the server
echo.
cd /d c:\Bldr
uvicorn core.bldr_api:app --host 0.0.0.0 --port 8000 --reload --log-level info