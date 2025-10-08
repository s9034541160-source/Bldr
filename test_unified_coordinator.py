#!/usr/bin/env python3
"""
Тест единого пути обработки запросов
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_unified_processing():
    """Тест единого пути обработки"""
    try:
        from core.model_manager import ModelManager
        from core.unified_tools_system import UnifiedToolsSystem
        from core.coordinator import Coordinator
        
        print("🔧 Тест единого пути обработки...")
        model_manager = ModelManager()
        tools_system = UnifiedToolsSystem(rag_system=None, model_manager=model_manager)
        coordinator = Coordinator(model_manager, tools_system, None)
        
        print(f"Координатор создан: {coordinator is not None}")
        
        # Тест простого запроса
        print("\n📝 Тест простого запроса: 'СП по земляным работам'")
        response1 = coordinator.process_request("СП по земляным работам")
        print(f"Ответ: {response1[:100]}...")
        
        # Тест сложного запроса
        print("\n📝 Тест сложного запроса: 'сделай чек-лист мастера'")
        response2 = coordinator.process_request("сделай чек-лист мастера")
        print(f"Ответ: {response2[:100]}...")
        
        # Тест неопределенного запроса
        print("\n📝 Тест неопределенного запроса: 'что-то по земле'")
        response3 = coordinator.process_request("что-то по земле")
        print(f"Ответ: {response3[:100]}...")
        
        print("✅ Тест единого пути обработки завершен")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_coordinator_agent():
    """Тест CoordinatorAgent"""
    try:
        from core.model_manager import ModelManager
        from core.unified_tools_system import UnifiedToolsSystem
        from core.agents.coordinator_agent import CoordinatorAgent
        
        print("🔧 Тест CoordinatorAgent...")
        model_manager = ModelManager()
        tools_system = UnifiedToolsSystem(rag_system=None, model_manager=model_manager)
        agent = CoordinatorAgent(tools_system=tools_system, enable_meta_tools=False)
        
        print(f"Agent создан: {agent is not None}")
        
        # Тест простого запроса
        print("\n📝 Тест простого запроса: 'ГОСТ по фундаментам'")
        response1 = agent.process_request("ГОСТ по фундаментам")
        print(f"Ответ: {response1[:100]}...")
        
        # Тест сложного запроса
        print("\n📝 Тест сложного запроса: 'проанализируй смету'")
        response2 = agent.process_request("проанализируй смету")
        print(f"Ответ: {response2[:100]}...")
        
        print("✅ Тест CoordinatorAgent завершен")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Запуск тестов единого пути обработки")
    print("=" * 60)
    
    success1 = test_unified_processing()
    print("\n" + "=" * 60)
    success2 = test_coordinator_agent()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("✅ Все тесты прошли успешно!")
        print("🎉 Координатор теперь работает как единая интеллектуальная система!")
    else:
        print("❌ Некоторые тесты не прошли")
