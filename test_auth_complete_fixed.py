#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
КОМПЛЕКСНЫЙ ТЕСТ АВТОРИЗАЦИИ
============================

Полный тест всей цепочки авторизации:
1. Backend API endpoints
2. JWT токены
3. CORS настройки  
4. Frontend логика
5. localStorage работа
6. Различные сценарии
"""

import os
import sys
import requests
import json
import jwt
import time
from datetime import datetime, timedelta

class AuthTestSuite:
    """Комплексный набор тестов авторизации"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        
    def log_test(self, test_name, success, message=""):
        """Логирование результата теста"""
        if success:
            print(f"✅ {test_name}")
            self.results['passed'] += 1
        else:
            print(f"❌ {test_name}: {message}")
            self.results['failed'] += 1
            self.results['errors'].append(f"{test_name}: {message}")
    
    def test_health_endpoint(self):
        """Тест базового health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            self.log_test("Health endpoint", response.status_code == 200)
            return response.status_code == 200
        except Exception as e:
            self.log_test("Health endpoint", False, str(e))
            return False
    
    def test_auth_debug_endpoint(self):
        """Тест debug endpoint для авторизации"""
        try:
            response = requests.get(f"{self.base_url}/auth/debug", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"   Auth config: {data}")
                self.log_test("Auth debug endpoint", True)
                return True, data
            else:
                self.log_test("Auth debug endpoint", False, f"Status {response.status_code}")
                return False, None
        except Exception as e:
            self.log_test("Auth debug endpoint", False, str(e))
            return False, None
    
    def test_token_endpoint_valid_credentials(self):
        """Тест получения токена с валидными данными"""
        try:
            form_data = {
                'username': 'admin',
                'password': 'admin',
                'grant_type': 'password'
            }
            
            response = requests.post(
                f"{self.base_url}/token",
                data=form_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'access_token' in data:
                    token = data['access_token']
                    print(f"   Token received: {token[:20]}...")
                    self.log_test("Token endpoint (valid credentials)", True)
                    return True, token
                else:
                    self.log_test("Token endpoint (valid credentials)", False, "No access_token in response")
                    return False, None
            else:
                self.log_test("Token endpoint (valid credentials)", False, f"Status {response.status_code}")
                return False, None
                
        except Exception as e:
            self.log_test("Token endpoint (valid credentials)", False, str(e))
            return False, None
    
    def test_token_endpoint_invalid_credentials(self):
        """Тест получения токена с невалидными данными"""
        try:
            form_data = {
                'username': 'admin',
                'password': 'wrong_password',
                'grant_type': 'password'
            }
            
            response = requests.post(
                f"{self.base_url}/token",
                data=form_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=10
            )
            
            # Should return 401
            expected = response.status_code == 401
            self.log_test("Token endpoint (invalid credentials)", expected)
            return expected
            
        except Exception as e:
            self.log_test("Token endpoint (invalid credentials)", False, str(e))
            return False
    
    def test_jwt_token_validation(self, token):
        """Тест валидации JWT токена"""
        try:
            # Декодируем токен
            secret = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
            payload = jwt.decode(token, secret, algorithms=["HS256"])
            
            # Проверяем обязательные поля
            has_sub = 'sub' in payload
            has_exp = 'exp' in payload
            has_role = 'role' in payload
            
            valid = has_sub and has_exp
            details = f"sub: {payload.get('sub')}, role: {payload.get('role')}, exp: {payload.get('exp')}"
            print(f"   Token payload: {details}")
            
            self.log_test("JWT token validation", valid)
            return valid, payload
            
        except jwt.ExpiredSignatureError:
            self.log_test("JWT token validation", False, "Token expired")
            return False, None
        except Exception as e:
            self.log_test("JWT token validation", False, str(e))
            return False, None
    
    def test_token_usage(self, token):
        """Тест использования токена для авторизованных запросов"""
        try:
            # Тестируем auth/validate endpoint
            response = requests.get(
                f"{self.base_url}/auth/validate",
                headers={'Authorization': f'Bearer {token}'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                valid = data.get('valid', False)
                print(f"   Validation response: {data}")
                self.log_test("Token usage (auth/validate)", valid)
                return valid, data
            else:
                self.log_test("Token usage (auth/validate)", False, f"Status {response.status_code}")
                return False, None
                
        except Exception as e:
            self.log_test("Token usage (auth/validate)", False, str(e))
            return False, None
    
    def test_expired_token(self):
        """Тест с истёкшим токеном"""
        try:
            # Создаем токен с истекшим временем
            secret = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
            expired_payload = {
                "sub": "test_user",
                "role": "user",
                "exp": datetime.utcnow() - timedelta(minutes=1)  # Истёк 1 минуту назад
            }
            
            expired_token = jwt.encode(expired_payload, secret, algorithm="HS256")
            
            # Пытаемся использовать истёкший токен
            response = requests.get(
                f"{self.base_url}/auth/validate",
                headers={'Authorization': f'Bearer {expired_token}'},
                timeout=10
            )
            
            # Должен вернуть 401
            expected = response.status_code == 401
            self.log_test("Expired token handling", expected)
            return expected
            
        except Exception as e:
            self.log_test("Expired token handling", False, str(e))
            return False
    
    def test_cors_preflight(self):
        """Тест CORS preflight запроса"""
        try:
            response = requests.options(
                f"{self.base_url}/token",
                headers={
                    'Origin': 'http://localhost:3001',
                    'Access-Control-Request-Method': 'POST',
                    'Access-Control-Request-Headers': 'Content-Type, Authorization'
                },
                timeout=10
            )
            
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
            }
            
            has_origin = cors_headers['Access-Control-Allow-Origin'] is not None
            has_methods = cors_headers['Access-Control-Allow-Methods'] is not None
            has_headers = cors_headers['Access-Control-Allow-Headers'] is not None
            
            valid = has_origin and has_methods and has_headers
            print(f"   CORS headers: {cors_headers}")
            
            self.log_test("CORS preflight", valid)
            return valid
            
        except Exception as e:
            self.log_test("CORS preflight", False, str(e))
            return False
    
    def test_frontend_compatibility(self):
        """Тест совместимости с фронтендом"""
        try:
            # Симуляция запроса как от фронтенда
            form_data = {
                'username': 'admin',
                'password': 'admin',
                'grant_type': 'password'
            }
            
            # Добавляем заголовки как от фронтенда
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'http://localhost:3001',
                'Referer': 'http://localhost:3001/',
                'User-Agent': 'Mozilla/5.0 (Test Frontend)'
            }
            
            response = requests.post(
                f"{self.base_url}/token",
                data=form_data,
                headers=headers,
                timeout=10
            )
            
            success = response.status_code == 200
            if success:
                # Проверяем наличие CORS заголовков в ответе
                cors_origin = response.headers.get('Access-Control-Allow-Origin')
                cors_credentials = response.headers.get('Access-Control-Allow-Credentials')
                
                print(f"   CORS Origin: {cors_origin}")
                print(f"   CORS Credentials: {cors_credentials}")
                
                data = response.json()
                has_token = 'access_token' in data
                success = success and has_token
            
            self.log_test("Frontend compatibility", success)
            return success
            
        except Exception as e:
            self.log_test("Frontend compatibility", False, str(e))
            return False
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🧪 КОМПЛЕКСНЫЙ ТЕСТ АВТОРИЗАЦИИ")
        print("="*50)
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Base URL: {self.base_url}")
        print()
        
        # Предварительные тесты
        print("🔍 Предварительные тесты:")
        server_ok = self.test_health_endpoint()
        debug_ok, debug_data = self.test_auth_debug_endpoint()
        
        if not server_ok:
            print("\n❌ Сервер недоступен, прекращаем тестирование")
            return False
        
        print("\n🔐 Тесты авторизации:")
        
        # Основные тесты токенов
        token_ok, token = self.test_token_endpoint_valid_credentials()
        self.test_token_endpoint_invalid_credentials()
        
        # Тесты JWT
        if token:
            jwt_ok, payload = self.test_jwt_token_validation(token)
            if jwt_ok:
                self.test_token_usage(token)
        
        # Дополнительные тесты
        self.test_expired_token()
        
        print("\n🌐 Тесты CORS и совместимости:")
        self.test_cors_preflight()
        self.test_frontend_compatibility()
        
        # Итоговый отчет
        self.print_summary()
        
        return self.results['failed'] == 0
    
    def print_summary(self):
        """Печать итогового отчета"""
        total = self.results['passed'] + self.results['failed']
        success_rate = (self.results['passed'] / total * 100) if total > 0 else 0
        
        print(f"\n{'='*50}")
        print("📊 ИТОГОВЫЙ ОТЧЕТ")
        print("="*50)
        print(f"✅ Успешно: {self.results['passed']}/{total}")
        print(f"❌ Неудачно: {self.results['failed']}/{total}")
        print(f"📈 Успешность: {success_rate:.1f}%")
        
        if self.results['errors']:
            print("\n🔥 ОШИБКИ:")
            for i, error in enumerate(self.results['errors'], 1):
                print(f"   {i}. {error}")
        
        print(f"\n🎯 РЕКОМЕНДАЦИИ:")
        
        if self.results['failed'] == 0:
            print("   🎉 Все тесты прошли успешно!")
            print("   ✅ Система авторизации работает корректно")
            print("   🚀 Можно включать авторизацию в продакшене")
        elif success_rate >= 80:
            print("   ✅ Большинство тестов прошло успешно")
            print("   🔧 Исправьте указанные ошибки")
            print("   ⚠️  Система готова к использованию с осторожностью")
        else:
            print("   ❌ Много критических ошибок")
            print("   🔧 Необходимо исправить систему авторизации")
            print("   🚫 НЕ рекомендуется использовать в продакшене")
        
        print(f"\n📋 ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ:")
        print(f"   SKIP_AUTH: {os.getenv('SKIP_AUTH', 'false')}")
        print(f"   DEV_MODE: {os.getenv('DEV_MODE', 'false')}")
        print(f"   SECRET_KEY: {'установлен' if os.getenv('SECRET_KEY') else 'по умолчанию'}")
        print(f"   CORS_ALLOW_ALL: {os.getenv('CORS_ALLOW_ALL', 'false')}")

def main():
    """Главная функция"""
    test_suite = AuthTestSuite()
    success = test_suite.run_all_tests()
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)