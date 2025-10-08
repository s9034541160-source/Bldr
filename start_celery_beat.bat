@echo off
echo Starting Celery Beat...
cd /d "%~dp0"
set PYTHONPATH=%~dp0
python -m celery -A core.celery_app:celery_app beat --loglevel=info
pause
