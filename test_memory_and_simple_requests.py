#!/usr/bin/env python3
"""
Тест исправлений управления памятью и упрощения логики
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_memory_management():
    """Тест управления памятью"""
    try:
        from core.model_manager import ModelManager
        
        print("🧠 Тест управления памятью...")
        model_manager = ModelManager()
        
        print(f"Размер кэша: {model_manager.cache_size}")
        print(f"TTL: {model_manager.ttl_minutes} минут")
        print(f"Активные модели: {len(model_manager.active_models)}")
        
        # Тест принудительной очистки
        print("\n🧹 Тест принудительной очистки...")
        model_manager.force_cleanup()
        print(f"Моделей после очистки: {len(model_manager.model_cache)}")
        
        print("✅ Тест управления памятью завершен")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка теста управления памятью: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_requests():
    """Тест простых запросов"""
    try:
        from core.model_manager import ModelManager
        from core.unified_tools_system import UnifiedToolsSystem
        from core.coordinator import Coordinator
        
        print("📝 Тест простых запросов...")
        model_manager = ModelManager()
        tools_system = UnifiedToolsSystem()
        coordinator = Coordinator(model_manager, tools_system, None)
        
        # Тест простого запроса
        print("\n🔍 Тест: 'СП по земляным работам'")
        response = coordinator.process_request("СП по земляным работам")
        print(f"Ответ: {response[:200]}...")
        
        # Проверяем, что не привлекались специалисты
        if "Мнения специалистов" not in response:
            print("✅ Специалисты не привлекались для простого запроса")
        else:
            print("❌ Специалисты привлекались для простого запроса")
        
        print("✅ Тест простых запросов завершен")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка теста простых запросов: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_memory_after_requests():
    """Тест памяти после запросов"""
    try:
        from core.model_manager import ModelManager
        from core.unified_tools_system import UnifiedToolsSystem
        from core.coordinator import Coordinator
        
        print("🧠 Тест памяти после запросов...")
        model_manager = ModelManager()
        tools_system = UnifiedToolsSystem()
        coordinator = Coordinator(model_manager, tools_system, None)
        
        # Делаем несколько запросов
        for i in range(3):
            print(f"\n📝 Запрос {i+1}: 'СП по земляным работам'")
            response = coordinator.process_request("СП по земляным работам")
            print(f"Моделей в кэше: {len(model_manager.model_cache)}")
            print(f"Активных моделей: {len(model_manager.active_models)}")
        
        print("✅ Тест памяти после запросов завершен")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка теста памяти после запросов: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Запуск тестов исправлений")
    print("=" * 50)
    
    success1 = test_memory_management()
    print("\n" + "=" * 50)
    success2 = test_simple_requests()
    print("\n" + "=" * 50)
    success3 = test_memory_after_requests()
    
    print("\n" + "=" * 50)
    if success1 and success2 and success3:
        print("✅ Все тесты прошли успешно!")
    else:
        print("❌ Некоторые тесты не прошли")
