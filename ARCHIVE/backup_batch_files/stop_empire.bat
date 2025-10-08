@echo off
title Bldr Empire v2 - Stop Services
echo ====================================================
echo   Bldr Empire v2 - Stop Services
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

echo Stopping Bldr Empire v2 services...
echo.

REM Stop all services using docker-compose
docker-compose down

if %errorlevel% neq 0 (
    echo Warning: Some services may not have stopped cleanly
    echo Check the error messages above
    echo.
)

echo.
echo Bldr Empire v2 services stopped successfully!
echo.
echo Press any key to exit
pause >nul