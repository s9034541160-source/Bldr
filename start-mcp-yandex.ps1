#!/usr/bin/env pwsh
# MCP Server for Yandex Browser - PowerShell Launcher

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🔧 MCP Server for Yandex Browser" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Проверка Node.js
try {
    $nodeVersion = node --version
    Write-Host "✅ Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js не найден. Установите Node.js с https://nodejs.org/" -ForegroundColor Red
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

# Проверка зависимостей
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Зависимости не установлены" -ForegroundColor Yellow
    Write-Host "📥 Установка зависимостей..." -ForegroundColor Cyan
    
    try {
        npm install
        Write-Host "✅ Зависимости установлены" -ForegroundColor Green
    } catch {
        Write-Host "❌ Ошибка установки зависимостей" -ForegroundColor Red
        Read-Host "Нажмите Enter для выхода"
        exit 1
    }
} else {
    Write-Host "✅ Зависимости найдены" -ForegroundColor Green
}

# Создание директорий
$directories = @("logs", "config", "reports")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "📁 Создана директория: $dir" -ForegroundColor Cyan
    }
}

# Проверка конфигурации
if (-not (Test-Path "config/mcp-config.json")) {
    Write-Host "⚙️ Создание конфигурации по умолчанию..." -ForegroundColor Yellow
    # Конфигурация будет создана автоматически сервером
}

Write-Host ""
Write-Host "🚀 Запуск MCP сервера..." -ForegroundColor Green
Write-Host "📡 Порт: 3000" -ForegroundColor Cyan
Write-Host "🌐 Браузер: Yandex" -ForegroundColor Cyan
Write-Host "🔗 Cursor интеграция: Включена" -ForegroundColor Cyan
Write-Host ""

# Обработка Ctrl+C
$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action {
    Write-Host ""
    Write-Host "🛑 Получен сигнал завершения..." -ForegroundColor Yellow
    Write-Host "🔌 Остановка MCP сервера..." -ForegroundColor Cyan
}

try {
    # Запуск сервера
    node mcp-yandex-browser-server.js
} catch {
    Write-Host ""
    Write-Host "❌ Ошибка запуска сервера" -ForegroundColor Red
    Write-Host "🔧 Проверьте логи: logs/mcp-server.log" -ForegroundColor Yellow
    
    if (Test-Path "logs/mcp-server.log") {
        Write-Host "📄 Последние строки лога:" -ForegroundColor Cyan
        Get-Content "logs/mcp-server.log" -Tail 10 | ForEach-Object {
            Write-Host "   $_" -ForegroundColor Gray
        }
    }
    
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Write-Host ""
Write-Host "🛑 Сервер остановлен" -ForegroundColor Yellow
Read-Host "Нажмите Enter для выхода"
