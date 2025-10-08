@echo off
setlocal enabledelayedexpansion

title Bldr Empire v2 - Celery Beat
echo Starting Celery Beat for Bldr Empire v2...
echo ========================================

REM Change to the project directory
cd /d "c:\Bldr"

REM Set Python path to include the project root
set PYTHONPATH=c:\Bldr;%PYTHONPATH%

REM Start Celery beat
echo Starting Celery beat...
python -m celery -A core.celery_app beat --loglevel=info