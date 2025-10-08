@echo off
setlocal
cd /d %~dp0
echo [INFO] Using Python (global): %PYTHON%
py --version

REM Отключаем VLM для стабильной работы
set VLM_DISABLED=1
set CUDA_VISIBLE_DEVICES=

echo [INFO] VLM disabled for stable operation
py enterprise_rag_trainer_full.py
endlocal
