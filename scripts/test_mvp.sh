#!/bin/bash
# Скрипт тестирования MVP

set -e

echo "🧪 Тестирование BLDR.EMPIRE v3.0 MVP..."

BASE_URL="http://localhost:8000/api"

# Проверка health check
echo "1. Проверка health check..."
HEALTH=$(curl -s "$BASE_URL/health" || echo "FAILED")
if [[ "$HEALTH" == *"healthy"* ]]; then
    echo "✅ Health check пройден"
else
    echo "❌ Health check не пройден"
    exit 1
fi

# Проверка аутентификации
echo "2. Проверка регистрации пользователя..."
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d '{"username":"testuser","email":"test@example.com","password":"testpass123"}' || echo "FAILED")

if [[ "$REGISTER_RESPONSE" == *"username"* ]] || [[ "$REGISTER_RESPONSE" == *"already"* ]]; then
    echo "✅ Регистрация работает"
else
    echo "⚠️  Регистрация: $REGISTER_RESPONSE"
fi

# Проверка логина
echo "3. Проверка логина..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=testuser&password=testpass123" || echo "FAILED")

if [[ "$LOGIN_RESPONSE" == *"access_token"* ]]; then
    echo "✅ Логин работает"
    TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
else
    echo "⚠️  Логин: $LOGIN_RESPONSE"
    TOKEN=""
fi

# Проверка защищенных эндпоинтов
if [ -n "$TOKEN" ]; then
    echo "4. Проверка защищенных эндпоинтов..."
    ME_RESPONSE=$(curl -s -X GET "$BASE_URL/auth/me" \
        -H "Authorization: Bearer $TOKEN" || echo "FAILED")
    
    if [[ "$ME_RESPONSE" == *"username"* ]]; then
        echo "✅ Защищенные эндпоинты работают"
    else
        echo "⚠️  Защищенные эндпоинты: $ME_RESPONSE"
    fi
fi

# Проверка LLM эндпоинта
echo "5. Проверка LLM эндпоинта..."
LLM_RESPONSE=$(curl -s -X GET "$BASE_URL/llm/models" \
    -H "Authorization: Bearer $TOKEN" || echo "FAILED")

if [[ "$LLM_RESPONSE" == *"models"* ]] || [[ "$LLM_RESPONSE" == *"[]"* ]]; then
    echo "✅ LLM эндпоинт доступен"
else
    echo "⚠️  LLM эндпоинт: $LLM_RESPONSE"
fi

echo ""
echo "✅ Базовые тесты завершены!"

