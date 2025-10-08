#!/usr/bin/env python3
"""
Тест выполнения инструментов
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_tools_system():
    """Тест системы инструментов"""
    try:
        from core.unified_tools_system import UnifiedToolsSystem
        from core.model_manager import ModelManager
        
        print("🔧 Тест системы инструментов...")
        model_manager = ModelManager()
        tools_system = UnifiedToolsSystem(rag_system=None, model_manager=model_manager)
        
        print(f"Система инструментов создана: {tools_system is not None}")
        
        # Проверяем доступные инструменты
        try:
            tools = tools_system.list_tools()
            print(f"Доступные инструменты: {len(tools)}")
            for tool in tools[:5]:  # Показываем первые 5
                print(f"  - {tool}")
        except Exception as e:
            print(f"Ошибка получения списка инструментов: {e}")
        
        # Тест выполнения простого инструмента
        try:
            print("\n🔍 Тест выполнения search_rag_database...")
            result = tools_system.execute_tool("search_rag_database", query="СП по земляным работам", doc_types=["norms"], n_results=3)
            print(f"Результат: {result}")
            print(f"Тип результата: {type(result)}")
            if hasattr(result, 'status'):
                print(f"Статус: {result.status}")
            if hasattr(result, 'data'):
                print(f"Данные: {result.data}")
        except Exception as e:
            print(f"Ошибка выполнения инструмента: {e}")
            import traceback
            traceback.print_exc()
        
        print("✅ Тест системы инструментов завершен")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка теста системы инструментов: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_coordinator_tools():
    """Тест выполнения инструментов через координатор"""
    try:
        from core.model_manager import ModelManager
        from core.unified_tools_system import UnifiedToolsSystem
        from core.coordinator import Coordinator
        
        print("🔧 Тест выполнения инструментов через координатор...")
        model_manager = ModelManager()
        tools_system = UnifiedToolsSystem(rag_system=None, model_manager=model_manager)
        coordinator = Coordinator(model_manager, tools_system, None)
        
        print(f"Координатор создан: {coordinator is not None}")
        print(f"Tools system в координаторе: {coordinator.tools_system is not None}")
        
        # Тест простого плана
        plan = {
            "status": "planning",
            "query_type": "normative_simple",
            "requires_tools": True,
            "tools": [
                {"name": "search_rag_database", "arguments": {"query": "СП по земляным работам", "doc_types": ["norms"], "n_results": 3}}
            ],
            "simple_response": True
        }
        
        print("\n🔍 Тест выполнения плана...")
        tool_results = coordinator.execute_tools(plan)
        print(f"Результаты инструментов: {len(tool_results)}")
        for i, result in enumerate(tool_results):
            print(f"  {i+1}. {result}")
        
        print("✅ Тест выполнения инструментов через координатор завершен")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка теста координатора: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Запуск тестов выполнения инструментов")
    print("=" * 50)
    
    success1 = test_tools_system()
    print("\n" + "=" * 50)
    success2 = test_coordinator_tools()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("✅ Все тесты прошли успешно!")
    else:
        print("❌ Некоторые тесты не прошли")
