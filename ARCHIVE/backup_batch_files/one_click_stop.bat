@echo off
title Bldr Empire v2 - Stop Services
color 0C

echo ==================================================
echo    Bldr Empire v2 - Stopping All Services
echo ==================================================
echo.

REM Kill processes on our ports (EXCEPT Neo4j)
echo [INFO] Stopping Redis server...
taskkill /F /IM redis-server.exe >nul 2>&1

echo [INFO] Stopping Docker containers...
docker stop qdrant-bldr >nul 2>&1

echo [INFO] Stopping Celery services...
taskkill /F /IM celery.exe >nul 2>&1

echo [INFO] Stopping FastAPI backend...
taskkill /F /IM uvicorn.exe >nul 2>&1

echo [INFO] Stopping Telegram Bot...
taskkill /F /IM python.exe >nul 2>&1

echo [INFO] Stopping Frontend Dashboard...
taskkill /F /IM node.exe >nul 2>&1

echo [INFO] Cleaning up any remaining processes (excluding Neo4j)...
timeout /t 3 /nobreak >nul
taskkill /F /IM redis-server.exe >nul 2>&1
taskkill /F /IM celery.exe >nul 2>&1
taskkill /F /IM uvicorn.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM docker.exe >nul 2>&1

REM Additional cleanup - wait and try again (excluding Neo4j)
echo [INFO] Performing additional cleanup (excluding Neo4j)...
timeout /t 3 /nobreak >nul
taskkill /F /FI "WINDOWTITLE eq Redis" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Celery" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq FastAPI" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Telegram" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Frontend" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Vite" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Dashboard" >nul 2>&1

echo [INFO] All services stopped (except Neo4j which is managed manually).
echo.
echo ==================================================
echo    Bldr Empire v2 Services Stopped
echo ==================================================
echo.
echo [IMPORTANT] Neo4j is NOT stopped by this script - please manage it manually
echo.
echo Press any key to continue...
pause >nul