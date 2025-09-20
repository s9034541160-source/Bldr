@echo off
title Bldr Backend Only
color 0A

echo ==================================================
echo    Bldr Backend Only - для RAG обучения
echo ==================================================

cd /d "%~dp0"

REM Set environment variables
set NEO4J_URI=neo4j://localhost:7687
set NEO4J_USER=neo4j
set NEO4J_PASSWORD=neopassword
set BASE_DIR=I:/docs
set SKIP_NEO4J=false

echo [INFO] Starting Backend API...
echo [INFO] Neo4j URI: %NEO4J_URI%
echo [INFO] Base DIR: %BASE_DIR%

REM Kill existing python processes on port 8000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %%a >nul 2>&1

REM Start backend
python -m uvicorn core.bldr_api:app --host 127.0.0.1 --port 8000 --timeout-keep-alive 7200

pause