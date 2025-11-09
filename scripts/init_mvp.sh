#!/bin/bash
# Скрипт инициализации MVP

set -e

echo "🚀 Инициализация BLDR.EMPIRE v3.0 MVP..."

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker и попробуйте снова."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Установите Docker Compose и попробуйте снова."
    exit 1
fi

# Создание .env файла если его нет
if [ ! -f .env ]; then
    echo "📝 Создание .env файла..."
    cp env.example .env
    echo "✅ .env файл создан. Проверьте настройки перед запуском."
fi

# Запуск Docker Compose
echo "🐳 Запуск Docker Compose..."
docker-compose -f docker-compose.mvp.yml up -d

# Ожидание готовности PostgreSQL
echo "⏳ Ожидание готовности PostgreSQL..."
sleep 10

# Инициализация базы данных
echo "🗄️  Инициализация базы данных..."
docker-compose -f docker-compose.mvp.yml exec -T backend python -m alembic upgrade head

# Создание начальных ролей и пользователей
echo "👤 Создание начальных ролей..."
docker-compose -f docker-compose.mvp.yml exec -T backend python backend/scripts/init_roles.py

echo "✅ MVP инициализирован!"
echo ""
echo "📋 Доступные сервисы:"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/api/docs"
echo "  - Frontend: http://localhost:3000"
echo "  - MinIO Console: http://localhost:9001 (minioadmin/minioadmin123)"
echo ""
echo "🔑 Для входа создайте пользователя через API:"
echo "  POST http://localhost:8000/api/auth/register"

