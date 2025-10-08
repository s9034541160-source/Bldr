@echo off
title Bldr Empire v2 - One-Click Launcher
echo ====================================================
echo   Bldr Empire v2 - One-Click Launcher
echo ====================================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Docker is not installed or not in PATH
    echo Please install Docker Desktop before running this script
    echo Download from: https://www.docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
)

REM Check if docker-compose is available
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: docker-compose is not available
    echo Please ensure Docker Desktop is properly installed
    echo.
    pause
    exit /b 1
)

echo Starting Bldr Empire v2 using Docker Compose...
echo This may take a few minutes on first run as containers are built and started
echo.

REM Start all services using docker-compose
echo Starting services...
docker-compose up -d

if %errorlevel% neq 0 (
    echo Error: Failed to start services
    echo Check the error messages above
    echo.
    pause
    exit /b 1
)

echo.
echo Waiting for services to initialize...
timeout /t 15 /nobreak >nul

echo.
echo Bldr Empire v2 started successfully!
echo.
echo Services:
echo   - Neo4j Database: http://localhost:7474 (username: neo4j, password: neopassword)
echo   - Qdrant Vector DB: http://localhost:6333
echo   - Backend API: http://localhost:8000
echo   - Frontend Dashboard: http://localhost:3000
echo.
echo To stop the system, run the stop_empire.bat file
echo.
echo Press any key to exit this window (services will continue running)
pause >nul