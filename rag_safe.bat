@echo off
setlocal
cd /d %~dp0
echo [INFO] Using Python (global): %PYTHON%
py --version

REM Устанавливаем переменные для безопасной работы с CUDA
set CUDA_LAUNCH_BLOCKING=1
set TORCH_USE_CUDA_DSA=1
set PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512

echo [INFO] CUDA debugging enabled
py enterprise_rag_trainer_full.py
endlocal
