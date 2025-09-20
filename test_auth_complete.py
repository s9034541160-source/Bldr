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
            
            # Should return 401\n            expected = response.status_code == 401\n            self.log_test("Token endpoint (invalid credentials)", expected)\n            return expected\n            \n        except Exception as e:\n            self.log_test("Token endpoint (invalid credentials)", False, str(e))\n            return False\n    \n    def test_jwt_token_validation(self, token):\n        \"\"\"Тест валидации JWT токена\"\"\"\n        try:\n            # Декодируем токен\n            secret = os.getenv(\"SECRET_KEY\", \"your-secret-key-change-in-production\")\n            payload = jwt.decode(token, secret, algorithms=[\"HS256\"])\n            \n            # Проверяем обязательные поля\n            has_sub = 'sub' in payload\n            has_exp = 'exp' in payload\n            has_role = 'role' in payload\n            \n            valid = has_sub and has_exp\n            details = f\"sub: {payload.get('sub')}, role: {payload.get('role')}, exp: {payload.get('exp')}\"\n            print(f\"   Token payload: {details}\")\n            \n            self.log_test("JWT token validation", valid)\n            return valid, payload\n            \n        except jwt.ExpiredSignatureError:\n            self.log_test("JWT token validation", False, "Token expired")\n            return False, None\n        except Exception as e:\n            self.log_test("JWT token validation", False, str(e))\n            return False, None\n    \n    def test_token_usage(self, token):\n        \"\"\"Тест использования токена для авторизованных запросов\"\"\"\n        try:\n            # Тестируем auth/validate endpoint\n            response = requests.get(\n                f"{self.base_url}/auth/validate",\n                headers={'Authorization': f'Bearer {token}'},\n                timeout=10\n            )\n            \n            if response.status_code == 200:\n                data = response.json()\n                valid = data.get('valid', False)\n                print(f\"   Validation response: {data}\")\n                self.log_test("Token usage (auth/validate)", valid)\n                return valid, data\n            else:\n                self.log_test("Token usage (auth/validate)", False, f"Status {response.status_code}")\n                return False, None\n                \n        except Exception as e:\n            self.log_test("Token usage (auth/validate)", False, str(e))\n            return False, None\n    \n    def test_expired_token(self):\n        \"\"\"Тест с истёкшим токеном\"\"\"\n        try:\n            # Создаем токен с истекшим временем\n            secret = os.getenv(\"SECRET_KEY\", \"your-secret-key-change-in-production\")\n            expired_payload = {\n                \"sub\": \"test_user\",\n                \"role\": \"user\",\n                \"exp\": datetime.utcnow() - timedelta(minutes=1)  # Истёк 1 минуту назад\n            }\n            \n            expired_token = jwt.encode(expired_payload, secret, algorithm=\"HS256\")\n            \n            # Пытаемся использовать истёкший токен\n            response = requests.get(\n                f"{self.base_url}/auth/validate",\n                headers={'Authorization': f'Bearer {expired_token}'},\n                timeout=10\n            )\n            \n            # Должен вернуть 401\n            expected = response.status_code == 401\n            self.log_test("Expired token handling", expected)\n            return expected\n            \n        except Exception as e:\n            self.log_test("Expired token handling", False, str(e))\n            return False\n    \n    def test_cors_preflight(self):\n        \"\"\"Тест CORS preflight запроса\"\"\"\n        try:\n            response = requests.options(\n                f"{self.base_url}/token",\n                headers={\n                    'Origin': 'http://localhost:3001',\n                    'Access-Control-Request-Method': 'POST',\n                    'Access-Control-Request-Headers': 'Content-Type, Authorization'\n                },\n                timeout=10\n            )\n            \n            cors_headers = {\n                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),\n                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),\n                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),\n                'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')\n            }\n            \n            has_origin = cors_headers['Access-Control-Allow-Origin'] is not None\n            has_methods = cors_headers['Access-Control-Allow-Methods'] is not None\n            has_headers = cors_headers['Access-Control-Allow-Headers'] is not None\n            \n            valid = has_origin and has_methods and has_headers\n            print(f\"   CORS headers: {cors_headers}\")\n            \n            self.log_test("CORS preflight", valid)\n            return valid\n            \n        except Exception as e:\n            self.log_test("CORS preflight", False, str(e))\n            return False\n    \n    def test_dev_mode_credentials(self):\n        \"\"\"Тест режима разработки с любыми credentials\"\"\"\n        try:\n            # Проверяем настройку DEV_MODE\n            dev_mode = os.getenv(\"DEV_MODE\", \"false\").lower() == \"true\"\n            \n            if not dev_mode:\n                print(\"   DEV_MODE disabled, skipping test\")\n                self.log_test("Dev mode credentials", True, \"Skipped (DEV_MODE disabled)\")\n                return True\n            \n            # Тестируем произвольные credentials\n            form_data = {\n                'username': 'any_user',\n                'password': 'any_password',\n                'grant_type': 'password'\n            }\n            \n            response = requests.post(\n                f"{self.base_url}/token",\n                data=form_data,\n                headers={'Content-Type': 'application/x-www-form-urlencoded'},\n                timeout=10\n            )\n            \n            success = response.status_code == 200\n            if success:\n                data = response.json()\n                print(f\"   Dev mode token: {data.get('access_token', 'No token')[:20]}...\")\n            \n            self.log_test("Dev mode credentials", success)\n            return success\n            \n        except Exception as e:\n            self.log_test("Dev mode credentials", False, str(e))\n            return False\n    \n    def test_skip_auth_mode(self):\n        \"\"\"Тест режима пропуска авторизации\"\"\"\n        try:\n            skip_auth = os.getenv(\"SKIP_AUTH\", \"false\").lower() == \"true\"\n            \n            if not skip_auth:\n                print(\"   SKIP_AUTH disabled, testing normal auth mode\")\n                \n                # В обычном режиме запрос без токена должен вернуть 401 или 422\n                response = requests.get(f\"{self.base_url}/auth/validate\", timeout=10)\n                expected = response.status_code in [401, 422]\n                self.log_test("Skip auth mode (normal)", expected)\n                return expected\n            else:\n                print(\"   SKIP_AUTH enabled, testing bypassed auth\")\n                \n                # В режиме skip auth запрос без токена должен пройти\n                response = requests.get(f\"{self.base_url}/auth/validate\", timeout=10)\n                success = response.status_code == 200\n                if success:\n                    data = response.json()\n                    print(f\"   Skip auth response: {data}\")\n                \n                self.log_test("Skip auth mode (bypassed)", success)\n                return success\n                \n        except Exception as e:\n            self.log_test("Skip auth mode", False, str(e))\n            return False\n    \n    def test_frontend_compatibility(self):\n        \"\"\"Тест совместимости с фронтендом\"\"\"\n        try:\n            # Симуляция запроса как от фронтенда\n            form_data = {\n                'username': 'admin',\n                'password': 'admin',\n                'grant_type': 'password'\n            }\n            \n            # Добавляем заголовки как от фронтенда\n            headers = {\n                'Content-Type': 'application/x-www-form-urlencoded',\n                'Origin': 'http://localhost:3001',\n                'Referer': 'http://localhost:3001/',\n                'User-Agent': 'Mozilla/5.0 (Test Frontend)'\n            }\n            \n            response = requests.post(\n                f\"{self.base_url}/token\",\n                data=form_data,\n                headers=headers,\n                timeout=10\n            )\n            \n            success = response.status_code == 200\n            if success:\n                # Проверяем наличие CORS заголовков в ответе\n                cors_origin = response.headers.get('Access-Control-Allow-Origin')\n                cors_credentials = response.headers.get('Access-Control-Allow-Credentials')\n                \n                print(f\"   CORS Origin: {cors_origin}\")\n                print(f\"   CORS Credentials: {cors_credentials}\")\n                \n                data = response.json()\n                has_token = 'access_token' in data\n                success = success and has_token\n            \n            self.log_test("Frontend compatibility", success)\n            return success\n            \n        except Exception as e:\n            self.log_test("Frontend compatibility", False, str(e))\n            return False\n    \n    def run_all_tests(self):\n        \"\"\"Запуск всех тестов\"\"\"\n        print(\"🧪 КОМПЛЕКСНЫЙ ТЕСТ АВТОРИЗАЦИИ\")\n        print(\"=\"*50)\n        print(f\"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\")\n        print(f\"🌐 Base URL: {self.base_url}\")\n        print()\n        \n        # Предварительные тесты\n        print(\"🔍 Предварительные тесты:\")\n        server_ok = self.test_health_endpoint()\n        debug_ok, debug_data = self.test_auth_debug_endpoint()\n        \n        if not server_ok:\n            print(\"\\n❌ Сервер недоступен, прекращаем тестирование\")\n            return False\n        \n        print(\"\\n🔐 Тесты авторизации:\")\n        \n        # Основные тесты токенов\n        token_ok, token = self.test_token_endpoint_valid_credentials()\n        self.test_token_endpoint_invalid_credentials()\n        \n        # Тесты JWT\n        if token:\n            jwt_ok, payload = self.test_jwt_token_validation(token)\n            if jwt_ok:\n                self.test_token_usage(token)\n        \n        # Дополнительные тесты\n        self.test_expired_token()\n        \n        print(\"\\n🌐 Тесты CORS и совместимости:\")\n        self.test_cors_preflight()\n        self.test_frontend_compatibility()\n        \n        print(\"\\n🧪 Тесты специальных режимов:\")\n        self.test_dev_mode_credentials()\n        self.test_skip_auth_mode()\n        \n        # Итоговый отчет\n        self.print_summary()\n        \n        return self.results['failed'] == 0\n    \n    def print_summary(self):\n        \"\"\"Печать итогового отчета\"\"\"\n        total = self.results['passed'] + self.results['failed']\n        success_rate = (self.results['passed'] / total * 100) if total > 0 else 0\n        \n        print(f\"\\n{'='*50}\")\n        print(\"📊 ИТОГОВЫЙ ОТЧЕТ\")\n        print(\"=\"*50)\n        print(f\"✅ Успешно: {self.results['passed']}/{total}\")\n        print(f\"❌ Неудачно: {self.results['failed']}/{total}\")\n        print(f\"📈 Успешность: {success_rate:.1f}%\")\n        \n        if self.results['errors']:\n            print(\"\\n🔥 ОШИБКИ:\")\n            for i, error in enumerate(self.results['errors'], 1):\n                print(f\"   {i}. {error}\")\n        \n        print(f\"\\n🎯 РЕКОМЕНДАЦИИ:\")\n        \n        if self.results['failed'] == 0:\n            print(\"   🎉 Все тесты прошли успешно!\")\n            print(\"   ✅ Система авторизации работает корректно\")\n            print(\"   🚀 Можно включать авторизацию в продакшене\")\n        elif success_rate >= 80:\n            print(\"   ✅ Большинство тестов прошло успешно\")\n            print(\"   🔧 Исправьте указанные ошибки\")\n            print(\"   ⚠️  Система готова к использованию с осторожностью\")\n        else:\n            print(\"   ❌ Много критических ошибок\")\n            print(\"   🔧 Необходимо исправить систему авторизации\")\n            print(\"   🚫 НЕ рекомендуется использовать в продакшене\")\n        \n        print(f\"\\n📋 ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ:\")\n        print(f\"   SKIP_AUTH: {os.getenv('SKIP_AUTH', 'false')}\")\n        print(f\"   DEV_MODE: {os.getenv('DEV_MODE', 'false')}\")\n        print(f\"   SECRET_KEY: {'установлен' if os.getenv('SECRET_KEY') else 'по умолчанию'}\")\n        print(f\"   CORS_ALLOW_ALL: {os.getenv('CORS_ALLOW_ALL', 'false')}\")\n\ndef main():\n    \"\"\"Главная функция\"\"\"\n    test_suite = AuthTestSuite()\n    success = test_suite.run_all_tests()\n    return success\n\nif __name__ == \"__main__\":\n    success = main()\n    exit(0 if success else 1)