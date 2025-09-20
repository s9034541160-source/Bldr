@echo off
setlocal enabledelayedexpansion

title Bldr Empire v2 - Celery Worker
echo Starting Celery Worker for Bldr Empire v2...
echo ==========================================

REM Change to the project directory
cd /d "c:\Bldr"

REM Set Python path to include the project root
set PYTHONPATH=c:\Bldr;%PYTHONPATH%

REM Start Celery worker
echo Starting Celery worker...
python -m celery -A core.celery_app worker --loglevel=info