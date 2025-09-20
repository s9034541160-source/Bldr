#!/usr/bin/env python3
"""
Тестовый скрипт для проверки интеграции SuperBuilder Tools
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Тестируем импорты"""
    print("🧪 Тестирование импортов...")
    
    errors = []
    
    # Test coordinator agent
    try:
        from core.agents.coordinator_agent import CoordinatorAgent
        print("✅ CoordinatorAgent импортирован успешно")
    except Exception as e:
        errors.append(f"❌ CoordinatorAgent: {e}")
    
    # Test tools API
    try:
        from backend.api.tools_api import router as tools_router
        print("✅ Tools API импортирован успешно")
    except Exception as e:
        errors.append(f"❌ Tools API: {e}")
    
    # Test meta-tools API
    try:
        from backend.api.meta_tools_api import router as meta_tools_router
        print("✅ Meta-Tools API импортирован успешно")
    except Exception as e:
        errors.append(f"❌ Meta-Tools API: {e}")
    
    # Test WebSocket manager
    try:
        from core.websocket_manager import manager as websocket_manager
        print("✅ WebSocket Manager импортирован успешно")
    except Exception as e:
        errors.append(f"❌ WebSocket Manager: {e}")
    
    # Test main API
    try:
        from core.bldr_api import app
        print("✅ Main API (bldr_api) импортирован успешно")
    except Exception as e:
        errors.append(f"❌ Main API: {e}")
    
    return errors

def test_api_routes():
    """Тестируем API роуты"""
    print("\n🔗 Тестирование API роутов...")
    
    try:
        from core.bldr_api import app
        routes = [route.path for route in app.routes]
        
        # Check for our new tools routes
        tools_routes = [r for r in routes if r.startswith('/api/tools')]
        if tools_routes:
            print(f"✅ Найдено {len(tools_routes)} Tools API роутов:")
            for route in tools_routes[:5]:  # Show first 5
                print(f"   - {route}")
        else:
            print("⚠️ Tools API роуты не найдены")
        
        # Check for meta-tools routes
        meta_routes = [r for r in routes if r.startswith('/api/meta-tools')]
        if meta_routes:
            print(f"✅ Найдено {len(meta_routes)} Meta-Tools API роутов:")
            for route in meta_routes[:5]:  # Show first 5
                print(f"   - {route}")
        else:
            print("⚠️ Meta-Tools API роуты не найдены")
        
        # Check WebSocket
        ws_routes = [r for r in routes if '/ws' in r]
        if ws_routes:
            print(f"✅ WebSocket роуты найдены: {ws_routes}")
        else:
            print("⚠️ WebSocket роуты не найдены")
            
        print(f"📊 Всего роутов в приложении: {len(routes)}")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования роутов: {e}")

def main():
    print("🚀 SuperBuilder Tools - Тест интеграции")
    print("=" * 50)
    
    # Test imports
    errors = test_imports()
    
    # Test API routes if imports successful
    if not errors:
        test_api_routes()
    
    # Summary
    print("\n📋 Результаты тестирования:")
    if errors:
        print("❌ Найдены ошибки:")
        for error in errors:
            print(f"   {error}")
        print("\n🔧 Рекомендации:")
        print("   - Проверьте пути импортов")
        print("   - Убедитесь что все зависимости установлены")
        print("   - Проверьте синтаксис в файлах с ошибками")
    else:
        print("✅ Все тесты прошли успешно!")
        print("🎉 Система готова к запуску!")
        print("\n🚀 Для запуска сервера выполните:")
        print("   python core/main.py")

if __name__ == "__main__":
    main()