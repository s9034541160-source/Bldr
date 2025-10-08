@echo off
title Bldr Empire v2 - Unified Stop
color 0C

echo ==================================================
echo    Bldr Empire v2 - Unified Stop
echo ==================================================
echo.

echo [INFO] Stopping all Bldr Empire services (excluding Neo4j)...

REM Kill processes by name (EXCEPT Java/Neo4j)
echo [INFO] Killing processes...
taskkill /F /IM redis-server.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
taskkill /F /IM uvicorn.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM celery.exe >nul 2>&1
taskkill /F /IM npm.exe >nul 2>&1
taskkill /F /IM docker.exe >nul 2>&1

REM Kill processes by port (EXCEPT Neo4j ports 7474 and 7687)
echo [INFO] Killing processes by port...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :6379') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :6333') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3001') do taskkill /F /PID %%a >nul 2>&1

REM Stop Docker containers
echo [INFO] Stopping Docker containers...
docker stop qdrant-bldr >nul 2>&1
docker stop redis-bldr >nul 2>&1

echo [INFO] Cleanup complete.
echo.
echo All Bldr Empire services have been stopped (Neo4j was left running).
echo.
pause