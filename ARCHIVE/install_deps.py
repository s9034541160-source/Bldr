#!/usr/bin/env python3
"""
Автоматическая установка зависимостей для SuperBuilder Tools
"""

import subprocess
import sys
import os

def install_package(package):
    """Установить пакет через pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки {package}: {e}")
        return False

def main():
    print("🔧 Установка зависимостей для SuperBuilder Tools...")
    
    # Список необходимых пакетов
    packages = [
        "python-multipart",
        "pillow", 
        "PyPDF2",
        "openpyxl",
        "fastapi",
        "uvicorn[standard]",
        "websockets",
        "aiofiles"
    ]
    
    success_count = 0
    
    for package in packages:
        print(f"📦 Устанавливаю {package}...")
        if install_package(package):
            print(f"✅ {package} установлен успешно")
            success_count += 1
        else:
            print(f"❌ Не удалось установить {package}")
    
    print(f"\n📊 Результат: {success_count}/{len(packages)} пакетов установлено")
    
    if success_count == len(packages):
        print("🎉 Все зависимости установлены успешно!")
    else:
        print("⚠️ Некоторые пакеты не установились. Попробуйте установить их вручную.")
    
    return success_count == len(packages)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)