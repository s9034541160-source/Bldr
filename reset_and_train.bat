@echo off
echo 🔥 ПОЛНЫЙ СБРОС И ПЕРЕЗАПУСК ОБУЧЕНИЯ RAG
echo ==========================================

echo.
echo ⚠️ ВНИМАНИЕ: Это удалит ВСЕ обученные данные!
echo Вы уверены что хотите продолжить?
pause

echo.
echo 🗑️ Сброс всех баз данных...
python reset_all_databases.py

echo.
echo ⏳ Ожидание 10 секунд для стабилизации системы...
timeout /t 10 /nobreak

echo.
echo 🚀 Запуск безопасного обучения...
python safe_rag_training.py

echo.
echo ✅ Процесс завершен!
pause
