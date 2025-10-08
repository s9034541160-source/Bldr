@echo off
setlocal
cd /d %~dp0

REM Загружаем переменные окружения из реестра
call :LoadEnvVars

echo [INFO] Using Python (global): %PYTHON%
echo [INFO] Model cache directory: %LLM_CACHE_DIR%
echo [INFO] Hugging Face cache: %HF_HOME%
py --version
py enterprise_rag_trainer_full.py
endlocal
goto :eof

:LoadEnvVars
REM Загружаем переменные окружения для использования диска I:\
set HF_HOME=I:\huggingface_cache
set TRANSFORMERS_CACHE=I:\huggingface_cache
set HF_DATASETS_CACHE=I:\huggingface_cache
set LLM_CACHE_DIR=I:\models_cache

REM Настройки папок для RAG-тренера
set BASE_DIR=I:\docs\perekos
set PROCESSED_DIR=I:\docs\processed_perekos

REM Оптимизация CUDA памяти для RTX 4060 (8GB)
set PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,max_split_size_mb:512
set CUDA_VISIBLE_DEVICES=0
set PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
goto :eof