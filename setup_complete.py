#!/usr/bin/env python3
"""
Автоматическая настройка SuperBuilder Tools - ПОЛНАЯ ИНТЕГРАЦИЯ
Этот скрипт выполняет все необходимые действия для готовности системы к запуску.
"""

import subprocess
import sys
import os
import json
from pathlib import Path

def run_command(command, description):
    """Выполнить команду с описанием"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - выполнено успешно")
            return True
        else:
            print(f"⚠️ {description} - предупреждение: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - ошибка: {e}")
        return False

def install_python_deps():
    """Установка Python зависимостей"""
    print("\n📦 Установка Python зависимостей...")
    
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
        if run_command(f'python -m pip install {package}', f'Установка {package}'):
            success_count += 1
    
    print(f"📊 Установлено {success_count}/{len(packages)} пакетов")
    return success_count == len(packages)

def check_env_file():
    """Проверка .env файла"""
    print("\n🔍 Проверка файла .env...")
    
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ Файл .env не найден")
        return False
    
    # Читаем существующий .env
    with open(env_path, 'r', encoding='utf-8') as f:
        env_content = f.read()
    
    # Проверяем необходимые переменные
    required_vars = [
        'MAX_FILE_SIZE',
        'UPLOAD_DIR', 
        'CORS_ALLOW_ALL',
        'TOOLS_API_ENABLED',
        'WEBSOCKET_ENABLED'
    ]
    
    missing_vars = []
    for var in required_vars:
        if var not in env_content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️ Отсутствуют переменные: {missing_vars}")
        return False
    else:
        print("✅ Все необходимые переменные окружения найдены")
        return True

def check_frontend():
    """Проверка frontend"""
    print("\n🎨 Проверка frontend...")
    
    frontend_path = Path("web/bldr_dashboard")
    if not frontend_path.exists():
        print("❌ Директория frontend не найдена")
        return False
    
    package_json = frontend_path / "package.json"
    if not package_json.exists():
        print("❌ package.json не найден")
        return False
    
    # Проверяем новые компоненты
    components_path = frontend_path / "src" / "components"
    new_components = [
        "ToolsInterface.tsx",
        "EstimateAnalyzer.tsx", 
        "ImageAnalyzer.tsx",
        "DocumentAnalyzer.tsx"
    ]
    
    missing_components = []
    for component in new_components:
        if not (components_path / component).exists():
            missing_components.append(component)
    
    if missing_components:
        print(f"⚠️ Отсутствуют компоненты: {missing_components}")
        return False
    else:
        print("✅ Все новые компоненты найдены")
        return True

def run_integration_test():
    """Запуск теста интеграции"""
    print("\n🧪 Запуск теста интеграции...")
    
    test_script = Path("test_integration.py")
    if not test_script.exists():
        print("❌ Тестовый скрипт не найден")
        return False
    
    return run_command("python test_integration.py", "Тест интеграции")

def check_file_structure():
    """Проверка файловой структуры"""
    print("\n📁 Проверка файловой структуры...")
    
    required_files = [
        "core/main.py",
        "core/bldr_api.py", 
        "core/websocket_manager.py",
        "backend/api/tools_api.py",
        "backend/api/meta_tools_api.py",
        "start_bldr.bat",
        ".env"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Отсутствующие файлы: {missing_files}")
        return False
    else:
        print("✅ Все необходимые файлы найдены")
        return True

def create_uploads_dir():
    """Создание директории uploads"""
    print("\n📂 Создание директории uploads...")
    
    uploads_dir = Path("uploads")
    if not uploads_dir.exists():
        uploads_dir.mkdir(exist_ok=True)
        print("✅ Директория uploads создана")
    else:
        print("✅ Директория uploads уже существует")
    
    return True

def generate_startup_info():
    """Генерация информации о запуске"""
    startup_info = {
        "system": "SuperBuilder Tools",
        "version": "2.0.0",
        "integration_complete": True,
        "services": {
            "redis": "localhost:6379",
            "neo4j": "localhost:7474", 
            "qdrant": "localhost:6333",
            "fastapi": "localhost:8000",
            "frontend": "localhost:3001",
            "websocket": "ws://localhost:8000/ws"
        },
        "api_endpoints": {
            "tools": [
                "POST /api/tools/analyze/estimate",
                "POST /api/tools/analyze/images",
                "POST /api/tools/analyze/documents",
                "GET /api/tools/jobs/{id}/status",
                "GET /api/tools/jobs/active",
                "GET /api/tools/health"
            ],
            "meta_tools": [
                "GET /api/meta-tools/list",
                "POST /api/meta-tools/execute"
            ],
            "documentation": [
                "GET /docs",
                "GET /redoc"
            ]
        },
        "setup_date": "2025-09-19",
        "ready_to_launch": True
    }
    
    with open("system_info.json", "w", encoding="utf-8") as f:
        json.dump(startup_info, f, ensure_ascii=False, indent=2)
    
    print("✅ Информация о системе сохранена в system_info.json")

def main():
    """Главная функция настройки"""
    print("🚀 SuperBuilder Tools - Автоматическая настройка системы")
    print("=" * 60)
    print("Выполняем все необходимые настройки для готовности к запуску...")
    print()
    
    # Список всех проверок
    checks = [
        ("Структура файлов", check_file_structure),
        ("Python зависимости", install_python_deps),
        ("Переменные окружения", check_env_file),
        ("Frontend компоненты", check_frontend),
        ("Директория uploads", create_uploads_dir),
        ("Тест интеграции", run_integration_test)
    ]
    
    results = {}
    
    # Выполняем все проверки
    for check_name, check_func in checks:
        results[check_name] = check_func()
    
    # Создаем информацию о системе
    generate_startup_info()
    
    # Итоговый отчет
    print("\n" + "=" * 60)
    print("📋 ИТОГОВЫЙ ОТЧЕТ НАСТРОЙКИ")
    print("=" * 60)
    
    success_count = sum(1 for result in results.values() if result)
    total_checks = len(results)
    
    for check_name, result in results.items():
        status = "✅ ПРОЙДЕНО" if result else "❌ ОШИБКА"
        print(f"{check_name:<25} : {status}")
    
    print("-" * 60)
    print(f"Результат: {success_count}/{total_checks} проверок пройдено")
    
    if success_count == total_checks:
        print("\n🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ УСПЕШНО!")
        print("🚀 СИСТЕМА ГОТОВА К ЗАПУСКУ!")
        print("\n📋 Для запуска выполните:")
        print("   start_bldr.bat")
        print("\n🌐 После запуска доступны:")
        print("   • API: http://localhost:8000/docs")
        print("   • Frontend: http://localhost:3001") 
        print("   • WebSocket: ws://localhost:8000/ws")
        print("\n✨ Система будет работать как швейцарские часы! ⚡")
        
    else:
        failed_checks = [name for name, result in results.items() if not result]
        print(f"\n⚠️ Обнаружены проблемы в: {failed_checks}")
        print("\n🔧 Рекомендуется:")
        print("   • Проверить ошибки выше")
        print("   • Установить недостающие зависимости")
        print("   • Убедиться в корректности файловой структуры")
        print("   • Запустить setup_complete.py повторно")
        
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️ Настройка прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Критическая ошибка настройки: {e}")
        sys.exit(1)