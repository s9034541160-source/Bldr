@echo off
echo Starting Celery Worker...
cd /d "%~dp0"
set PYTHONPATH=%~dp0
python -m celery -A core.celery_app:celery_app worker --loglevel=info --pool=solo --concurrency=1
pause
