#!/usr/bin/env python3
"""
Быстрый запуск API сервера для тестирования
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

def start_server():
    """Запуск FastAPI сервера"""
    print("🚀 Запускаем FastAPI сервер...")
    
    # Устанавливаем переменные окружения
    env = os.environ.copy()
    env['SKIP_NEO4J'] = 'true'  # Пропускаем Neo4j для быстрого запуска
    
    # Команда для запуска uvicorn
    cmd = [
        sys.executable, '-m', 'uvicorn', 
        'app.main:app', 
        '--host', '0.0.0.0', 
        '--port', '8001',
        '--reload'
    ]
    
    try:
        # Запускаем в текущей директории
        process = subprocess.Popen(
            cmd, 
            cwd=r'C:\Bldr',
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        print(f"✅ Сервер запущен с PID: {process.pid}")
        print("🌐 Сервер доступен по адресу: http://localhost:8001")
        print("📚 API документация: http://localhost:8001/docs")
        print("\n📋 Логи сервера:")
        print("-" * 50)
        
        # Читаем и выводим логи
        try:
            for line in iter(process.stdout.readline, ''):
                if line:
                    print(line.rstrip())
                    
                    # Проверяем, что сервер запустился
                    if "Uvicorn running on" in line:
                        print("\n✅ Сервер успешно запущен!")
                        print("🔍 Можно запускать тестирование: python test_fixes.py")
                        
        except KeyboardInterrupt:
            print("\n\n⏹️ Остановка сервера...")
            process.terminate()
            time.sleep(2)
            if process.poll() is None:
                process.kill()
            print("✅ Сервер остановлен")
            
    except Exception as e:
        print(f"❌ Ошибка запуска сервера: {e}")
        return False
        
    return True

def check_port():
    """Проверить, свободен ли порт 8001"""
    import socket
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        result = s.connect_ex(('localhost', 8001))
        if result == 0:
            print("⚠️ Порт 8001 уже используется")
            return False
        else:
            print("✅ Порт 8001 свободен")
            return True

if __name__ == "__main__":
    print("🔧 Подготовка к запуску API сервера")
    print("=" * 50)
    
    # Проверяем порт
    if not check_port():
        print("💡 Возможно, сервер уже запущен. Попробуйте:")
        print("   python test_fixes.py")
        sys.exit(1)
    
    # Проверяем директорию
    if not os.path.exists(r'C:\Bldr\app\main.py'):
        print("❌ Файл app/main.py не найден в C:\\Bldr")
        print("💡 Убедитесь, что находитесь в правильной директории")
        sys.exit(1)
    
    print("📂 Рабочая директория: C:\\Bldr")
    print("🔧 Переменные: SKIP_NEO4J=true")
    print()
    
    # Запускаем сервер
    start_server()