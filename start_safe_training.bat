@echo off
echo 🛡️ БЕЗОПАСНЫЙ ЗАПУСК RAG ОБУЧЕНИЯ
echo ===================================
echo.
echo ⚠️ Эта версия защищена от одновременного запуска!
echo 🔒 Автоматическая блокировка активна
echo.

python enterprise_rag_trainer_safe.py --custom_dir "I:/docs/downloaded" --fast_mode

echo.
echo ✅ Обучение завершено!
pause