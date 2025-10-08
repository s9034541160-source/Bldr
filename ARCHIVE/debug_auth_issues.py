#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ДИАГНОСТИКА ПРОБЛЕМ С АВТОРИЗАЦИЕЙ
==================================

Анализирует проблемы в системе авторизации:
1. Проверка работы /token endpoint
2. Проверка JWT генерации и валидации
3. Проверка CORS настроек
4. Анализ проблем с фронтендом
"""

import os
import sys
import requests
import json
import jwt
from datetime import datetime, timedelta

def analyze_backend_auth():
    """Анализ проблем в бэкенде"""
    print("🔍 Анализ авторизации бэкенда...")
    
    issues = []
    
    # 1. Проверка /token endpoint
    try:
        # Тест с правильными данными
        form_data = {
            'username': 'admin',
            'password': 'admin',
            'grant_type': 'password'
        }
        
        response = requests.post(
            'http://localhost:8000/token',
            data=form_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=10
        )
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"✅ Token endpoint работает: {token_data}")
            
            # Проверка структуры токена
            if 'access_token' in token_data:
                token = token_data['access_token']
                try:
                    # Декодируем токен для проверки
                    secret = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
                    payload = jwt.decode(token, secret, algorithms=["HS256"])
                    print(f"✅ JWT токен валидный: {payload}")
                except Exception as e:
                    print(f"❌ Проблема с JWT токеном: {e}")
                    issues.append(f"JWT validation error: {e}")
            else:
                print("❌ Нет access_token в ответе")
                issues.append("Missing access_token in response")
        else:
            print(f"❌ Token endpoint ошибка: {response.status_code} - {response.text}")
            issues.append(f"Token endpoint error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка подключения к token endpoint: {e}")
        issues.append(f"Token endpoint connection error: {e}")
    
    # 2. Проверка CORS заголовков
    try:
        # Preflight request
        response = requests.options(
            'http://localhost:8000/token',
            headers={
                'Origin': 'http://localhost:3001',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            }
        )
        
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
        }
        
        print(f"📋 CORS заголовки: {cors_headers}")
        
        if not cors_headers['Access-Control-Allow-Origin']:
            issues.append("Missing CORS Allow-Origin header")
        if not cors_headers['Access-Control-Allow-Methods']:
            issues.append("Missing CORS Allow-Methods header")
        if not cors_headers['Access-Control-Allow-Headers']:
            issues.append("Missing CORS Allow-Headers header")
            
    except Exception as e:
        print(f"❌ Ошибка проверки CORS: {e}")
        issues.append(f"CORS check error: {e}")
    
    # 3. Проверка SKIP_AUTH режима
    skip_auth = os.getenv("SKIP_AUTH", "false").lower() == "true"
    print(f"🔐 SKIP_AUTH режим: {skip_auth}")
    
    if skip_auth:
        # Тест protected endpoint без токена
        try:
            response = requests.get('http://localhost:8000/health', timeout=5)
            if response.status_code == 200:
                print("✅ Health endpoint доступен без токена (SKIP_AUTH=true)")
            else:
                print(f"❌ Health endpoint недоступен: {response.status_code}")
                issues.append("Health endpoint not accessible with SKIP_AUTH=true")
        except Exception as e:
            print(f"❌ Ошибка проверки SKIP_AUTH: {e}")
            issues.append(f"SKIP_AUTH test error: {e}")
    
    return issues

def analyze_frontend_auth_flow():
    """Анализ проблем во фронтенде (симуляция)"""
    print("\n🖥️ Анализ логики авторизации фронтенда...")
    
    issues = []
    
    # Симуляция getToken запроса
    try:
        # Тестируем как фронтенд делает запрос
        form_data = {
            'username': 'admin',
            'password': 'admin',
            'grant_type': 'password'
        }
        
        response = requests.post(
            'http://localhost:8000/token',
            data=form_data,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'http://localhost:3001'  # Фронтенд origin
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Фронтенд может получить токен")
            token_data = response.json()
            access_token = token_data.get('access_token')
            
            if access_token:
                # Тест использования токена
                auth_response = requests.get(
                    'http://localhost:8000/health',
                    headers={
                        'Authorization': f'Bearer {access_token}',
                        'Origin': 'http://localhost:3001'
                    }
                )
                
                if auth_response.status_code == 200:
                    print("✅ Токен работает для авторизации")
                else:
                    print(f"❌ Токен не работает: {auth_response.status_code}")
                    issues.append("Token doesn't work for authorization")
            else:
                print("❌ Нет access_token в ответе")
                issues.append("No access_token in response")
        else:
            print(f"❌ Фронтенд не может получить токен: {response.status_code}")
            issues.append(f"Frontend can't get token: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка симуляции фронтенда: {e}")
        issues.append(f"Frontend simulation error: {e}")
    
    return issues

def check_jwt_configuration():
    """Проверка конфигурации JWT"""
    print("\n🔑 Проверка JWT конфигурации...")
    
    issues = []
    
    # Проверка переменных окружения
    secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    algorithm = os.getenv("ALGORITHM", "HS256")
    expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    
    print(f"🔐 SECRET_KEY: {'***' if secret_key != 'your-secret-key-change-in-production' else 'DEFAULT (небезопасно!)'}")
    print(f"🔐 ALGORITHM: {algorithm}")
    print(f"🔐 EXPIRE_MINUTES: {expire_minutes}")
    
    if secret_key == "your-secret-key-change-in-production":
        issues.append("Using default SECRET_KEY (security risk)")
    
    # Тест генерации токена
    try:
        test_payload = {
            "sub": "test_user",
            "exp": datetime.utcnow() + timedelta(minutes=expire_minutes)
        }
        
        test_token = jwt.encode(test_payload, secret_key, algorithm=algorithm)
        decoded_payload = jwt.decode(test_token, secret_key, algorithms=[algorithm])
        
        print(f"✅ JWT генерация/декодирование работает")
        
    except Exception as e:
        print(f"❌ Проблема с JWT: {e}")
        issues.append(f"JWT generation/decoding error: {e}")
    
    return issues

def test_specific_auth_scenarios():
    """Тестирование специфических сценариев авторизации"""
    print("\n🧪 Тестирование специфических сценариев...")
    
    issues = []
    
    # Сценарий 1: Неправильный пароль
    try:
        form_data = {
            'username': 'admin',
            'password': 'wrong_password',
            'grant_type': 'password'
        }
        
        response = requests.post(
            'http://localhost:8000/token',
            data=form_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        if response.status_code == 401:
            print("✅ Неправильный пароль правильно отклоняется")
        else:
            print(f"❌ Неправильная обработка неправильного пароля: {response.status_code}")
            issues.append("Wrong password not handled correctly")
            
    except Exception as e:
        print(f"❌ Ошибка теста неправильного пароля: {e}")
        issues.append(f"Wrong password test error: {e}")
    
    # Сценарий 2: Отсутствующие поля
    try:
        response = requests.post(
            'http://localhost:8000/token',
            data={'username': 'admin'},  # Нет пароля
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        if response.status_code == 422:  # Validation error
            print("✅ Отсутствующие поля правильно обрабатываются")
        else:
            print(f"❌ Отсутствующие поля обработаны неправильно: {response.status_code}")
            issues.append("Missing fields not handled correctly")
            
    except Exception as e:
        print(f"❌ Ошибка теста отсутствующих полей: {e}")
        issues.append(f"Missing fields test error: {e}")
    
    # Сценарий 3: Проверка истечения токена
    try:
        # Создаем токен с истекшим временем
        secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
        expired_payload = {
            "sub": "test_user",
            "exp": datetime.utcnow() - timedelta(minutes=1)  # Истёк 1 минуту назад
        }
        
        expired_token = jwt.encode(expired_payload, secret_key, algorithm="HS256")
        
        # Пытаемся использовать истёкший токен
        response = requests.get(
            'http://localhost:8000/health',
            headers={'Authorization': f'Bearer {expired_token}'}
        )
        
        if response.status_code == 401:
            print("✅ Истёкший токен правильно отклоняется")
        else:
            print(f"❌ Истёкший токен обработан неправильно: {response.status_code}")
            issues.append("Expired token not handled correctly")
            
    except Exception as e:
        print(f"❌ Ошибка теста истёкшего токена: {e}")
        issues.append(f"Expired token test error: {e}")
    
    return issues

def main():
    """Основная функция диагностики"""
    print("🔍 ДИАГНОСТИКА ПРОБЛЕМ С АВТОРИЗАЦИЕЙ")
    print("="*50)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    all_issues = []
    
    # Анализируем различные аспекты
    all_issues.extend(analyze_backend_auth())
    all_issues.extend(analyze_frontend_auth_flow())
    all_issues.extend(check_jwt_configuration())
    all_issues.extend(test_specific_auth_scenarios())
    
    # Итоговый отчет
    print(f"\n{'='*50}")
    print("📊 ИТОГОВЫЙ ОТЧЕТ ПО ПРОБЛЕМАМ")
    print("="*50)
    
    if all_issues:
        print(f"❌ Найдено {len(all_issues)} проблем:")
        for i, issue in enumerate(all_issues, 1):
            print(f"   {i}. {issue}")
        
        print(f"\n🔧 РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ:")
        
        if any("CORS" in issue for issue in all_issues):
            print("   • Добавить правильные CORS заголовки в FastAPI")
            
        if any("SECRET_KEY" in issue for issue in all_issues):
            print("   • Установить безопасный SECRET_KEY")
            
        if any("Token endpoint" in issue for issue in all_issues):
            print("   • Проверить endpoint /token и его зависимости")
            
        if any("JWT" in issue for issue in all_issues):
            print("   • Проверить библиотеки JWT и их версии")
            
        if any("Frontend" in issue for issue in all_issues):
            print("   • Исправить логику авторизации во фронтенде")
    else:
        print("🎉 Проблем с авторизацией не найдено!")
        print("✅ Система авторизации работает корректно")
    
    print(f"\n📋 ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ:")
    print(f"   SKIP_AUTH: {os.getenv('SKIP_AUTH', 'false')}")
    print(f"   SECRET_KEY: {'установлен' if os.getenv('SECRET_KEY') else 'не установлен'}")
    print(f"   ALGORITHM: {os.getenv('ALGORITHM', 'HS256')}")
    print(f"   ACCESS_TOKEN_EXPIRE_MINUTES: {os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30')}")
    
    return len(all_issues) == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)