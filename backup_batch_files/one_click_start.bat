@echo off
setlocal enabledelayedexpansion

title Bldr Empire v2 - One Click Launcher
echo ====================================================
echo   Bldr Empire v2 - One Click Launcher
echo ====================================================
echo.

REM Check if we're running in automated mode (no pause)
set AUTOMATED_MODE=0
if "%1"=="--automated" set AUTOMATED_MODE=1

REM Define default ports
set API_PORT=8000
set DASHBOARD_PORT=3000

REM Check if we're in the right directory
if not exist "core\bldr_api.py" (
    echo Error: Could not find core\bldr_api.py
    echo Please run this script from the Bldr root directory
    if !AUTOMATED_MODE! equ 0 pause
    exit /b 1
)

REM Check if required directories exist, create if not
if not exist "data" mkdir data
if not exist "data\documents" mkdir data\documents
if not exist "data\norms_db" mkdir data\norms_db
if not exist "data\qdrant_db" mkdir data\qdrant_db
if not exist "data\reports" mkdir data\reports

echo Checking system requirements...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher and add it to your PATH
    if !AUTOMATED_MODE! equ 0 pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Node.js is not installed or not in PATH
    echo Please install Node.js and add it to your PATH
    if !AUTOMATED_MODE! equ 0 pause
    exit /b 1
)

REM Check if required Python packages are installed
echo Checking Python dependencies...
pip show fastapi >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing Python dependencies...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo Error: Failed to install Python dependencies
        if !AUTOMATED_MODE! equ 0 pause
        exit /b 1
    )
)

REM Check if required Node packages are installed (simplified check)
echo Checking Node.js dependencies...
if not exist "web\bldr_dashboard\node_modules" (
    echo Installing Node.js dependencies...
    cd web\bldr_dashboard
    npm install
    if %errorlevel% neq 0 (
        echo Error: Failed to install Node.js dependencies
        cd ..\..
        if !AUTOMATED_MODE! equ 0 pause
        exit /b 1
    )
    cd ..\..
)

echo.
echo Stopping any existing Bldr services...
echo.

REM Kill existing processes on our ports
echo Checking for existing processes on port %API_PORT%...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :%API_PORT% ^| findstr LISTENING') do (
    echo Killing process %%a on port %API_PORT%
    taskkill /f /pid %%a 2>nul
)

echo Checking for existing processes on port %DASHBOARD_PORT%...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :%DASHBOARD_PORT% ^| findstr LISTENING') do (
    echo Killing process %%a on port %DASHBOARD_PORT%
    taskkill /f /pid %%a 2>nul
)

echo.
echo Starting Bldr Empire v2 services...
echo.

REM Start the backend services using the dedicated script
echo Starting Bldr Backend Services...
start "Bldr Backend" /min cmd /c "cd /d %cd% && start_backend.bat"

REM Wait a moment for the backend to start
timeout /t 5 /nobreak >nul

REM Start Celery worker and beat services
echo Starting Celery Worker...
start "Bldr Celery Worker" /min cmd /c "cd /d %cd% && start_celery.bat"

echo Starting Celery Beat...
start "Bldr Celery Beat" /min cmd /c "cd /d %cd% && start_celery_beat.bat"

REM Wait a moment for Celery services to start
timeout /t 5 /nobreak >nul

REM Start the React dashboard
echo Starting Bldr Dashboard on port %DASHBOARD_PORT%...
start "Bldr Dashboard" /min cmd /c "cd /d %cd%\web\bldr_dashboard && npm run dev -- --port %DASHBOARD_PORT% --strictPort true"

REM Start the Telegram bot
echo Starting Bldr Telegram Bot...
start "Bldr Bot" /min cmd /c "cd /d %cd% && python integrations\telegram_bot.py"

echo.
echo ====================================================
echo   Bldr Empire v2 Services Started Successfully!
echo ====================================================
echo API Server:      http://localhost:%API_PORT%
echo Dashboard:       http://localhost:%DASHBOARD_PORT%
echo.
echo Services are running in the background.
echo.

REM Open the dashboard in the default browser
echo Opening Bldr Dashboard in your browser...
start http://localhost:%DASHBOARD_PORT%

echo To stop all services, run one_click_stop.bat
echo.

if !AUTOMATED_MODE! equ 0 (
    echo Press any key to continue...
    pause >nul
)