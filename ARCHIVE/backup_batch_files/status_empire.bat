@echo off
title Bldr Empire v2 - Service Status
echo ====================================================
echo   Bldr Empire v2 - Service Status
echo ====================================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Docker is not installed or not in PATH
    echo.
    pause
    exit /b 1
)

echo Checking Bldr Empire v2 service status...
echo.

REM Show status of all services using docker-compose
docker-compose ps

echo.
echo Press any key to exit
pause >nul