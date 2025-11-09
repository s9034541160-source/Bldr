# Скрипт инициализации MVP для Windows PowerShell

Write-Host "🚀 Инициализация BLDR.EMPIRE v3.0 MVP..." -ForegroundColor Green

# Проверка Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker не установлен. Установите Docker Desktop и попробуйте снова." -ForegroundColor Red
    exit 1
}

if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker Compose не установлен. Установите Docker Desktop и попробуйте снова." -ForegroundColor Red
    exit 1
}

# Создание .env файла если его нет
if (-not (Test-Path .env)) {
    Write-Host "📝 Создание .env файла..." -ForegroundColor Yellow
    Copy-Item env.example .env
    Write-Host "✅ .env файл создан. Проверьте настройки перед запуском." -ForegroundColor Green
}

# Запуск Docker Compose
Write-Host "🐳 Запуск Docker Compose..." -ForegroundColor Yellow
docker-compose -f docker-compose.mvp.yml up -d

# Ожидание готовности PostgreSQL
Write-Host "⏳ Ожидание готовности PostgreSQL..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Инициализация базы данных
Write-Host "🗄️  Инициализация базы данных..." -ForegroundColor Yellow
docker-compose -f docker-compose.mvp.yml exec -T backend python -m alembic upgrade head

# Создание начальных ролей и пользователей
Write-Host "👤 Создание начальных ролей..." -ForegroundColor Yellow
docker-compose -f docker-compose.mvp.yml exec -T backend python backend/scripts/init_roles.py

Write-Host "✅ MVP инициализирован!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Доступные сервисы:" -ForegroundColor Cyan
Write-Host "  - Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "  - API Docs: http://localhost:8000/api/docs" -ForegroundColor White
Write-Host "  - Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "  - MinIO Console: http://localhost:9001 (minioadmin/minioadmin123)" -ForegroundColor White
Write-Host ""
Write-Host "🔑 Для входа создайте пользователя через API:" -ForegroundColor Yellow
Write-Host "  POST http://localhost:8000/api/auth/register" -ForegroundColor White

