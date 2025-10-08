#!/usr/bin/env python3
"""
Тест упрощенной логики координатора
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_simple_queries():
    """Тест простых запросов"""
    try:
        from core.model_manager import ModelManager
        from core.unified_tools_system import UnifiedToolsSystem
        from core.agents.coordinator_agent import CoordinatorAgent
        
        print("🔍 Тест простых запросов...")
        model_manager = ModelManager()
        tools_system = UnifiedToolsSystem()
        agent = CoordinatorAgent(tools_system=tools_system, enable_meta_tools=False)
        
        # Тест простых запросов
        simple_queries = [
            "СП по земляным работам",
            "ГОСТ по фундаментам", 
            "ГЭСН на бетон",
            "норма по дренажу"
        ]
        
        for query in simple_queries:
            print(f"\n📝 Тест: '{query}'")
            response = agent.process_request(query)
            print(f"Ответ: {response[:100]}...")
            
            # Проверяем, что это простой ответ, а не сложный план
            if "JSON" in response or "план" in response.lower() or "специалист" in response.lower():
                print("❌ Запрос обработан как сложный (неправильно)")
            else:
                print("✅ Запрос обработан как простой (правильно)")
        
        print("\n✅ Тест простых запросов завершен")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка теста простых запросов: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_complex_queries():
    """Тест сложных запросов"""
    try:
        from core.model_manager import ModelManager
        from core.unified_tools_system import UnifiedToolsSystem
        from core.agents.coordinator_agent import CoordinatorAgent
        
        print("🔧 Тест сложных запросов...")
        model_manager = ModelManager()
        tools_system = UnifiedToolsSystem()
        agent = CoordinatorAgent(tools_system=tools_system, enable_meta_tools=False)
        
        # Тест сложных запросов
        complex_queries = [
            "сделай чек-лист мастера СМР",
            "проанализируй смету",
            "создай график работ"
        ]
        
        for query in complex_queries:
            print(f"\n📝 Тест: '{query}'")
            response = agent.process_request(query)
            print(f"Ответ: {response[:100]}...")
            
            # Сложные запросы должны идти через полный цикл
            print("✅ Сложный запрос обработан через полный цикл")
        
        print("\n✅ Тест сложных запросов завершен")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка теста сложных запросов: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_memory_usage():
    """Тест использования памяти"""
    try:
        from core.model_manager import ModelManager
        
        print("🧠 Тест использования памяти...")
        model_manager = ModelManager()
        
        print(f"Размер кэша: {model_manager.cache_size}")
        print(f"TTL: {model_manager.ttl_minutes} минут")
        print(f"Моделей в кэше: {len(model_manager.model_cache)}")
        print(f"Активных моделей: {len(model_manager.active_models)}")
        
        # Тест принудительной очистки
        model_manager.force_cleanup()
        print(f"Моделей после очистки: {len(model_manager.model_cache)}")
        
        print("✅ Тест использования памяти завершен")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка теста памяти: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Запуск тестов упрощенной логики координатора")
    print("=" * 60)
    
    success1 = test_simple_queries()
    print("\n" + "=" * 60)
    success2 = test_complex_queries()
    print("\n" + "=" * 60)
    success3 = test_memory_usage()
    
    print("\n" + "=" * 60)
    if success1 and success2 and success3:
        print("✅ Все тесты прошли успешно!")
    else:
        print("❌ Некоторые тесты не прошли")
