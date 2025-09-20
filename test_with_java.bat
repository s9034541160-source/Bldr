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
    echo [INFO] 2. Download "OpenJDK 21 (LTS) JDK"
    echo [INFO] 3. Run the installer and follow the instructions
    echo [INFO] 4. After installation, restart your computer
    echo [INFO] 5. Run this script again
    echo.
    echo [INFO] Note: Make sure to install the JDK (not JRE) version.
    echo.
    pause
    exit /b 1
)
echo [INFO] Java is installed and accessible.

echo Script completed successfully.
pause