#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ ИСПРАВЛЕННОЙ АРХИТЕКТУРЫ
=============================================

Этот скрипт:
1. Проверяет что сервер запущен
2. Запускает комплексное тестирование исправленной архитектуры
3. Показывает итоговый отчет
"""

import os
import sys
import subprocess
import requests
import time
from datetime import datetime

def check_server_status():
    """Проверка что сервер запущен и отвечает"""
    print("🔍 Checking server status...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and healthy")
            return True
        else:
            print(f"⚠️ Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error checking server: {e}")
        return False

def run_architecture_test():
    """Запуск теста исправленной архитектуры"""
    print("\n🚀 Running fixed architecture test...")
    
    test_script = "C:/Bldr/test_fixed_architecture.py"
    
    if not os.path.exists(test_script):
        print(f"❌ Test script not found: {test_script}")
        return False
    
    try:
        # Запускаем тест
        result = subprocess.run([
            sys.executable, test_script
        ], capture_output=True, text=True, timeout=300)
        
        print("📄 Test output:")
        print("-" * 40)
        print(result.stdout)
        
        if result.stderr:
            print("\n🔥 Test errors:")
            print("-" * 40) 
            print(result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Test timed out (5 minutes)")
        return False
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False

def show_final_report(architecture_test_passed, server_running):
    """Показать итоговый отчет"""
    print("\n" + "="*60)
    print("📊 FINAL ARCHITECTURE FIX REPORT")
    print("="*60)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n🖥️ Server Status: {'✅ RUNNING' if server_running else '❌ NOT RUNNING'}")
    print(f"🔧 Architecture Test: {'✅ PASSED' if architecture_test_passed else '❌ FAILED'}")
    
    if server_running and architecture_test_passed:
        print(f"\n🎉 SUCCESS! Your system is now properly configured:")
        print("   ✅ No more routing through RAG trainer 'жопа'")
        print("   ✅ ТГ-бот requests go directly to coordinator")
        print("   ✅ All agents use Master Tools System")
        print("   ✅ Specialist agents properly integrated")
        print("   ✅ Tools execution unified through adapter")
        print("\n🚀 Your system is ready for production use!")
        
    elif server_running and not architecture_test_passed:
        print(f"\n⚠️ Server is running but architecture tests failed")
        print("   📝 Review the test output above for specific issues")
        print("   🔧 Some components may need additional fixes")
        
    elif not server_running and architecture_test_passed:
        print(f"\n⚠️ Tests passed but server is not running")
        print("   🔌 Start the server with: python app.py or uvicorn main:app")
        print("   🧪 Then run tests again to verify full functionality")
        
    else:
        print(f"\n❌ Both server and tests have issues")
        print("   🔌 First start the server")
        print("   🔧 Then investigate test failures")
    
    print("\n📋 NEXT STEPS:")
    if server_running and architecture_test_passed:
        print("   1. ✅ System is ready - try sending real requests")
        print("   2. 📱 Test with actual Telegram bot")
        print("   3. 🌐 Test with web frontend")
        print("   4. 📊 Monitor logs for any issues")
    else:
        print("   1. 🔌 Ensure server is running")
        print("   2. 🧪 Re-run tests to identify specific issues")
        print("   3. 🔧 Fix any failing components")
        print("   4. 🔄 Repeat until all tests pass")

def main():
    """Главная функция"""
    print("🧪 FINAL ARCHITECTURE TEST RUNNER")
    print("="*60)
    
    # Проверяем сервер
    server_running = check_server_status()
    
    if server_running:
        # Запускаем тесты архитектуры
        architecture_test_passed = run_architecture_test()
    else:
        print("\n⚠️ Skipping architecture tests - server not running")
        architecture_test_passed = False
    
    # Показываем итоговый отчет
    show_final_report(architecture_test_passed, server_running)
    
    # Возвращаем код выхода
    if server_running and architecture_test_passed:
        print("\n🎯 EXIT: SUCCESS (0)")
        return 0
    else:
        print("\n🎯 EXIT: FAILURE (1)")
        return 1

if __name__ == "__main__":
    sys.exit(main())