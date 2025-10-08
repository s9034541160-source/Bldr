@echo off
echo ========================================
echo 🔧 MCP Server for Yandex Browser
echo ========================================
echo.

echo 📦 Проверка зависимостей...
if not exist "node_modules" (
    echo ❌ Зависимости не установлены
    echo 📥 Установка зависимостей...
    npm install
    if errorlevel 1 (
        echo ❌ Ошибка установки зависимостей
        pause
        exit /b 1
    )
)

echo ✅ Зависимости установлены

echo.
echo 🚀 Запуск MCP сервера...
echo 📡 Порт: 3000
echo 🌐 Браузер: Yandex
echo 🔗 Cursor интеграция: Включена
echo.

node mcp-yandex-browser-server.js

if errorlevel 1 (
    echo.
    echo ❌ Ошибка запуска сервера
    echo 🔧 Проверьте логи: logs/mcp-server.log
    pause
)

echo.
echo 🛑 Сервер остановлен
pause
