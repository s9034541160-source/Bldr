@echo off
echo ========================================
echo 🔧 Установка MCP Server for Yandex Browser
echo ========================================
echo.

echo 📋 Проверка системы...
echo.

REM Проверка Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js не найден
    echo 📥 Скачайте и установите Node.js с https://nodejs.org/
    echo 💡 Рекомендуется версия 16.0.0 или выше
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
    echo ✅ Node.js: %NODE_VERSION%
)

REM Проверка npm
npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ npm не найден
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('npm --version') do set NPM_VERSION=%%i
    echo ✅ npm: %NPM_VERSION%
)

echo.
echo 📦 Установка зависимостей...
echo.

REM Копирование package.json
if not exist "package.json" (
    if exist "package-mcp-yandex.json" (
        copy "package-mcp-yandex.json" "package.json" >nul
        echo ✅ package.json создан
    ) else (
        echo ❌ package-mcp-yandex.json не найден
        pause
        exit /b 1
    )
)

REM Установка зависимостей
echo 📥 Установка npm пакетов...
npm install
if errorlevel 1 (
    echo ❌ Ошибка установки зависимостей
    pause
    exit /b 1
)

echo ✅ Зависимости установлены

echo.
echo 📁 Создание директорий...
mkdir logs 2>nul
mkdir config 2>nul
mkdir reports 2>nul
echo ✅ Директории созданы

echo.
echo ⚙️ Настройка конфигурации...
if not exist "config\mcp-config.json" (
    echo ❌ config\mcp-config.json не найден
    echo 💡 Скопируйте файл из config\mcp-config.json
    pause
    exit /b 1
)
echo ✅ Конфигурация найдена

echo.
echo 🧪 Проверка файлов...
if not exist "mcp-yandex-browser-server.js" (
    echo ❌ mcp-yandex-browser-server.js не найден
    pause
    exit /b 1
)
echo ✅ Сервер найден

if not exist "yandex-browser-client.js" (
    echo ❌ yandex-browser-client.js не найден
    pause
    exit /b 1
)
echo ✅ Клиент найден

if not exist "test-yandex-browser.html" (
    echo ❌ test-yandex-browser.html не найден
    pause
    exit /b 1
)
echo ✅ Тестовая страница найдена

echo.
echo 🎉 УСТАНОВКА ЗАВЕРШЕНА!
echo ========================================
echo.
echo 🚀 Для запуска используйте:
echo    start-mcp-yandex.bat
echo.
echo 🌐 Для тестирования откройте:
echo    test-yandex-browser.html
echo.
echo 📚 Документация:
echo    README-MCP-YANDEX.md
echo.
echo ========================================
echo.

REM Создание ярлыка для быстрого запуска
echo 📝 Создание ярлыка для быстрого запуска...
echo @echo off > "Запуск MCP Yandex.bat"
echo cd /d "%~dp0" >> "Запуск MCP Yandex.bat"
echo start-mcp-yandex.bat >> "Запуск MCP Yandex.bat"
echo ✅ Ярлык создан: "Запуск MCP Yandex.bat"

echo.
echo 🎯 Готово! Теперь можно запускать MCP сервер
echo.
pause
