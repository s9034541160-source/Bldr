#!/usr/bin/env python3
"""
Скрипт для перезапуска сервера и быстрого тестирования
"""

import subprocess
import time
import requests
import os
import signal
from dotenv import load_dotenv

load_dotenv()

def kill_python_servers():
    """Убить все процессы Python сервера"""
    print("🔄 Останавливаем старые процессы Python...")
    try:
        # Для Windows
        subprocess.run(["taskkill", "/f", "/im", "python.exe"], 
                      capture_output=True, text=True)
        time.sleep(2)
        print("✅ Старые процессы остановлены")
    except Exception as e:
        print(f"⚠️ Ошибка остановки процессов: {e}")

def start_server():
    """Запустить FastAPI сервер"""
    print("🚀 Запускаем FastAPI сервер...")
    try:
        # Устанавливаем переменные окружения
        env = os.environ.copy()
        env['SKIP_NEO4J'] = 'true'
        
        # Запускаем uvicorn
        process = subprocess.Popen([
            "python", "-m", "uvicorn", 
            "core.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--reload",
            "--access-log"
        ], 
        cwd="C:\\Bldr",
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
        )
        
        print(f"✅ Сервер запущен с PID: {process.pid}")
        
        # Ждем запуска сервера
        print("⏳ Ожидаем запуска сервера...")
        for i in range(30):  # Ждем максимум 30 секунд
            try:
                response = requests.get("http://localhost:8000/health", timeout=2)
                if response.status_code == 200:
                    print(f"✅ Сервер готов! (попытка {i+1})")
                    return process
            except:
                pass
            time.sleep(1)
            print(f"   Попытка {i+1}/30...")
        
        print("❌ Сервер не запустился за 30 секунд")
        return None
        
    except Exception as e:
        print(f"❌ Ошибка запуска сервера: {e}")
        return None

def quick_test():
    """Быстрое тестирование основных функций"""
    print("\n🧪 Быстрое тестирование...")
    
    api_token = os.getenv('API_TOKEN')
    if not api_token:
        print("❌ API_TOKEN не найден!")
        return
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    tests = [
        ("Health Check", "GET", "/health", {}, {}),
        ("Training Status", "GET", "/api/training/status", headers, {}),
        ("RAG Search", "POST", "/query", headers, {"query": "тест", "k": 1}),
        ("AI Request", "POST", "/ai", headers, {"prompt": "Привет", "model": "deepseek/deepseek-r1-0528-qwen3-8b"}),
    ]
    
    results = []
    
    for test_name, method, endpoint, test_headers, data in tests:
        print(f"   🔄 {test_name}...", end=" ", flush=True)
        try:
            url = f"http://localhost:8000{endpoint}"
            start_time = time.time()
            
            if method == "GET":
                response = requests.get(url, headers=test_headers, timeout=10)
            else:
                response = requests.post(url, headers=test_headers, json=data, timeout=10)
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                print(f"✅ {duration:.2f}s")
                results.append(True)
            else:
                print(f"❌ HTTP {response.status_code} ({duration:.2f}s)")
                results.append(False)
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results.append(False)
    
    success_rate = sum(results) / len(results) * 100
    print(f"\n📊 Успешность: {sum(results)}/{len(results)} ({success_rate:.1f}%)")
    
    if success_rate >= 75:
        print("🎉 Система работает стабильно!")
    elif success_rate >= 50:
        print("⚠️ Система частично работает")
    else:
        print("🚨 Много проблем, нужна диагностика")
    
    return success_rate

def main():
    """Главная функция"""
    print("🔧 ПЕРЕЗАПУСК СЕРВЕРА И БЫСТРОЕ ТЕСТИРОВАНИЕ")
    print("=" * 60)
    
    # Останавливаем старые процессы
    kill_python_servers()
    
    # Запускаем сервер
    server_process = start_server()
    
    if server_process:
        try:
            # Быстрое тестирование
            success_rate = quick_test()
            
            print(f"\n🎯 ИТОГ:")
            if success_rate >= 75:
                print("   ✅ Сервер работает корректно, можно запускать полные E2E тесты")
                print("   🔄 Команда: python final_e2e_test.py")
            else:
                print("   ⚠️ Есть проблемы, но основные функции доступны")
                print("   🔄 Команда: python test_auth_fixed.py")
            
            print(f"\\n📡 Сервер работает на: http://localhost:8000")
            print(f"📚 API документация: http://localhost:8000/docs")
            print(f"🔧 Логи сервера в консоли")
            
            # Оставляем сервер работать
            print(f"\\n⚠️ Сервер оставлен работающим (PID: {server_process.pid})")
            print("   Для остановки: Ctrl+C или taskkill /f /im python.exe")
            
        except KeyboardInterrupt:
            print("\\n⏹️ Остановка сервера...")
            server_process.terminate()
            time.sleep(2)
            if server_process.poll() is None:
                server_process.kill()
            print("✅ Сервер остановлен")
    else:
        print("❌ Не удалось запустить сервер")

if __name__ == "__main__":
    main()