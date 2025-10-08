#!/usr/bin/env python3
"""
Тест исправлений координатора
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_coordinator_execution():
    """Тест выполнения инструментов координатором"""
    try:
        from core.model_manager import ModelManager
        from core.unified_tools_system import UnifiedToolsSystem
        from core.coordinator import Coordinator
        
        print("🔧 Инициализация систем...")
        model_manager = ModelManager()
        tools_system = UnifiedToolsSystem()
        coordinator = Coordinator(model_manager, tools_system, None)
        
        print("📝 Тест 1: Простой запрос")
        response1 = coordinator.process_request("СП по земляным работам")
        print(f"Ответ: {response1}")
        
        print("\n📝 Тест 2: Запрос с документами")
        response2 = coordinator.process_request("сделай ежедневный чек-лист мастера СМР в ворд")
        print(f"Ответ: {response2}")
        
        print("\n📝 Тест 3: Анализ сметы")
        response3 = coordinator.process_request("проанализируй смету, сделай отчет по ней")
        print(f"Ответ: {response3}")
        
        print("\n✅ Тесты завершены")
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
        
        print("🔧 Инициализация CoordinatorAgent...")
        model_manager = ModelManager()
        tools_system = UnifiedToolsSystem()
        agent = CoordinatorAgent(tools_system=tools_system, enable_meta_tools=False)
        
        print("📝 Тест CoordinatorAgent: Простой запрос")
        response = agent.process_request("СП по земляным работам")
        print(f"Ответ: {response}")
        
        print("\n✅ Тест CoordinatorAgent завершен")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка теста CoordinatorAgent: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Запуск тестов исправлений координатора")
    print("=" * 50)
    
    success1 = test_coordinator_execution()
    print("\n" + "=" * 50)
    success2 = test_coordinator_agent()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("✅ Все тесты прошли успешно!")
    else:
        print("❌ Некоторые тесты не прошли")
