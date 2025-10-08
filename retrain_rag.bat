@echo off
echo ========================================
echo    ПЕРЕОБРАБОТКА RAG - ПРИНУДИТЕЛЬНАЯ
echo ========================================
echo.

echo [1/3] Очистка данных RAG...
python clear_rag_data.py
if %errorlevel% neq 0 (
    echo ОШИБКА: Не удалось очистить данные RAG!
    pause
    exit /b 1
)

echo.
echo [2/3] Запуск RAG-тренера...
python enterprise_rag_trainer_full.py
if %errorlevel% neq 0 (
    echo ОШИБКА: Не удалось запустить RAG-тренер!
    pause
    exit /b 1
)

echo.
echo [3/3] Завершено!
echo ========================================
echo    ПЕРЕОБРАБОТКА RAG ЗАВЕРШЕНА УСПЕШНО!
echo ========================================
pause
