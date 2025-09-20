@echo off
title Bldr Empire v2 - Shutdown Script
color 0C

echo ==================================================
echo    Bldr Empire v2 - Enhanced Shutdown Script
echo ==================================================
echo.

REM Kill all Bldr Empire processes
echo [INFO] Stopping all Bldr Empire services...
taskkill /F /IM redis-server.exe >nul 2>&1
taskkill /F /IM neo4j.bat >nul 2>&1
taskkill /F /IM uvicorn.exe >nul 2>&1
taskkill /F /IM celery.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1

REM Stop Docker containers
echo [INFO] Stopping Docker containers...
docker stop qdrant-bldr >nul 2>&1

REM Kill processes by port
echo [INFO] Killing processes on service ports...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :1234') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :6379') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :7474') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :6333') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do taskkill /F /PID %%a >nul 2>&1

echo.
echo ==================================================
echo    Bldr Empire v2 Services Stopped Successfully!
echo ==================================================
echo All services have been terminated.
echo.
echo Press any key to continue...
pause >nul