@echo off
REM Bldr Empire v2 - Stop All Services Script
REM This script stops all services used for testing

echo 🛑 Stopping Bldr Empire v2 Services...

REM Stop Celery processes
echo 🔄 Stopping Celery worker...
taskkill /f /im celery.exe >nul 2>&1

echo 🔄 Stopping Celery beat...
taskkill /f /im celery.exe >nul 2>&1

REM Stop FastAPI server
echo 🔄 Stopping FastAPI server...
taskkill /f /im uvicorn.exe >nul 2>&1

echo 🔄 Stopping Redis container...
docker stop redis-bldr >nul 2>&1
docker rm redis-bldr >nul 2>&1

echo ✅ All services stopped successfully!