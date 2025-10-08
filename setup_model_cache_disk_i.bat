@echo off
echo 🚀 Настройка загрузки моделей на диск I:\
echo.

REM Создаем папки на диске I:\
echo Создание папок для кэша моделей...
if not exist "I:\huggingface_cache" mkdir "I:\huggingface_cache"
if not exist "I:\models_cache" mkdir "I:\models_cache"

echo ✅ Папки созданы:
echo    I:\huggingface_cache
echo    I:\models_cache
echo.

REM Устанавливаем переменные окружения
echo Установка переменных окружения для Hugging Face...
setx HF_HOME "I:\huggingface_cache"
setx TRANSFORMERS_CACHE "I:\huggingface_cache"
setx HF_DATASETS_CACHE "I:\huggingface_cache"

echo ✅ Переменные окружения установлены:
echo    HF_HOME=I:\huggingface_cache
echo    TRANSFORMERS_CACHE=I:\huggingface_cache
echo    HF_DATASETS_CACHE=I:\huggingface_cache
echo.

REM Устанавливаем переменные для RAG-тренера
echo Установка переменных для RAG-тренера...
setx LLM_CACHE_DIR "I:\models_cache"

echo ✅ Переменные RAG-тренера установлены:
echo    LLM_CACHE_DIR=I:\models_cache
echo.

echo 🎉 Настройка завершена!
echo.
echo 📝 ВАЖНО: Перезапустите терминал для применения переменных окружения
echo 📝 Все модели будут загружаться на диск I:\ вместо C:\
echo.
pause
