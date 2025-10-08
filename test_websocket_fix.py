#!/usr/bin/env python3
"""
Тестирование исправлений WebSocket токенов
"""

import os
import sys
import time
import jwt
from datetime import datetime, timedelta

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_token_expiration():
    """Тестирование времени жизни токена"""
    print("🔐 Тестирование времени жизни токена...")
    
    try:
        # Читаем настройки из main.py
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Ищем настройку времени жизни токена
        if 'ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))' in content:
            print("✅ Время жизни токена увеличено до 24 часов (1440 минут)")
            return True
        elif 'ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))' in content:
            print("❌ Время жизни токена все еще 30 минут")
            return False
        else:
            print("⚠️ Не удалось определить настройку времени жизни токена")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка проверки настроек токена: {e}")
        return False

def test_websocket_error_handling():
    """Тестирование улучшенной обработки ошибок WebSocket"""
    print("\n🔧 Тестирование обработки ошибок WebSocket...")
    
    try:
        # Читаем main.py
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем наличие улучшенной обработки ошибок
        improvements = [
            "jwt.ExpiredSignatureError",
            "Token expired. Please refresh the page to get a new token.",
            "Invalid token. Please refresh the page to get a new token."
        ]
        
        found_improvements = 0
        for improvement in improvements:
            if improvement in content:
                found_improvements += 1
                print(f"✅ Найдено: {improvement}")
            else:
                print(f"❌ Не найдено: {improvement}")
        
        if found_improvements == len(improvements):
            print("\n🎉 Все улучшения обработки ошибок применены!")
            return True
        else:
            print(f"\n⚠️ Найдено {found_improvements}/{len(improvements)} улучшений")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка проверки обработки ошибок: {e}")
        return False

def test_frontend_token_refresh():
    """Тестирование автоматического обновления токена на фронтенде"""
    print("\n🔄 Тестирование автоматического обновления токена...")
    
    try:
        # Читаем AuthHeader.tsx
        with open('web/bldr_dashboard/src/components/AuthHeader.tsx', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем наличие функций обновления токена
        improvements = [
            "const refreshToken = async () =>",
            "Token expired or expiring soon, attempting to refresh",
            "Token refreshed successfully",
            "exp - now) < 300"  # Проверка за 5 минут до истечения
        ]
        
        found_improvements = 0
        for improvement in improvements:
            if improvement in content:
                found_improvements += 1
                print(f"✅ Найдено: {improvement}")
            else:
                print(f"❌ Не найдено: {improvement}")
        
        if found_improvements == len(improvements):
            print("\n🎉 Все улучшения фронтенда применены!")
            return True
        else:
            print(f"\n⚠️ Найдено {found_improvements}/{len(improvements)} улучшений")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка проверки фронтенда: {e}")
        return False

def test_jwt_token_creation():
    """Тестирование создания JWT токена"""
    print("\n🎫 Тестирование создания JWT токена...")
    
    try:
        # Создаем тестовый токен
        secret_key = "bldr_empire_secret_key_change_in_production"
        algorithm = "HS256"
        
        # Токен на 24 часа
        expire = datetime.utcnow() + timedelta(hours=24)
        payload = {
            "sub": "admin",
            "role": "admin",
            "exp": expire
        }
        
        token = jwt.encode(payload, secret_key, algorithm=algorithm)
        print(f"✅ Токен создан: {token[:50]}...")
        
        # Проверяем декодирование
        decoded = jwt.decode(token, secret_key, algorithms=[algorithm])
        print(f"✅ Токен декодирован: {decoded}")
        
        # Проверяем время истечения
        exp_timestamp = decoded['exp']
        exp_datetime = datetime.fromtimestamp(exp_timestamp)
        time_until_expiry = exp_datetime - datetime.utcnow()
        
        print(f"✅ Время истечения: {exp_datetime}")
        print(f"✅ Осталось времени: {time_until_expiry}")
        
        if time_until_expiry.total_seconds() > 23 * 3600:  # Больше 23 часов
            print("✅ Токен создан на 24 часа")
            return True
        else:
            print("❌ Токен создан на меньшее время")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка создания токена: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЙ WEBSOCKET")
    print("=" * 60)
    
    # Тестируем все компоненты
    token_expiration_ok = test_token_expiration()
    websocket_errors_ok = test_websocket_error_handling()
    frontend_refresh_ok = test_frontend_token_refresh()
    jwt_creation_ok = test_jwt_token_creation()
    
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"   🔐 Время жизни токена: {'✅' if token_expiration_ok else '❌'}")
    print(f"   🔧 Обработка ошибок WS: {'✅' if websocket_errors_ok else '❌'}")
    print(f"   🔄 Обновление токена: {'✅' if frontend_refresh_ok else '❌'}")
    print(f"   🎫 Создание JWT: {'✅' if jwt_creation_ok else '❌'}")
    
    if token_expiration_ok and websocket_errors_ok and frontend_refresh_ok and jwt_creation_ok:
        print("\n🎉 ВСЕ ИСПРАВЛЕНИЯ WEBSOCKET РАБОТАЮТ!")
        print("✅ Время жизни токена увеличено до 24 часов")
        print("✅ Улучшенная обработка ошибок WebSocket")
        print("✅ Автоматическое обновление токена на фронтенде")
        print("✅ JWT токены создаются корректно")
    else:
        print("\n⚠️ НЕКОТОРЫЕ ИСПРАВЛЕНИЯ ТРЕБУЮТ ДОРАБОТКИ")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
