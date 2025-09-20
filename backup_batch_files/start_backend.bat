@echo off
setlocal enabledelayedexpansion

title Bldr Empire v2 - Backend Services
echo ====================================================
echo   Bldr Empire v2 - Backend Services Launcher
echo ====================================================
echo.

REM Change to the project directory
cd /d "c:\Bldr"

REM Kill any existing processes on port 8000
echo Stopping any existing API processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo Killing process %%a on port 8000
    taskkill /f /pid %%a 2>nul
)

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Check if Redis container is already running
echo Checking Redis...
docker ps | findstr "redis-bldr" >nul 2>&1
if %errorlevel% equ 0 (
    echo SUCCESS: Redis container is already running
) else (
    echo WARNING: Redis container not found. Please ensure Redis is running.
)

REM Start Celery worker
echo Starting Celery worker...
start "Celery Worker" /min cmd /c "cd /d c:\Bldr && start_celery.bat"
timeout /t 5 /nobreak >nul

REM Start Celery beat
echo Starting Celery beat...
start "Celery Beat" /min cmd /c "cd /d c:\Bldr && start_celery_beat.bat"
timeout /t 5 /nobreak >nul

REM Start the FastAPI server with proper configuration
echo Starting uvicorn server on http://localhost:8000
echo This window will show API logs. Do not close it.
echo.

REM Use the working command with proper path setup
venv\Scripts\python.exe -c "import sys; sys.path.append('.'); from core.bldr_api import app; import uvicorn; uvicorn.run('core.bldr_api:app', host='0.0.0.0', port=8000, log_level='info')"