#!/usr/bin/env python3
"""
Тестовый скрипт для проверки универсального представления инструментов.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from core.tools.base_tool import tool_registry, ToolManifest, ToolInterface
from core.coordinator_with_tool_interfaces import CoordinatorWithToolInterfaces

def test_tool_registration():
    """Тест регистрации инструментов в реестре."""
    print("🔧 Тестирование регистрации инструментов...")
    
    # Регистрируем тестовые инструменты
    try:
        from tools.custom.search_rag_database_v2 import manifest as search_manifest
        from tools.custom.generate_letter_v2 import manifest as letter_manifest
        from tools.custom.auto_budget_v2 import manifest as budget_manifest
        
        tool_registry.register_tool(search_manifest)
        tool_registry.register_tool(letter_manifest)
        tool_registry.register_tool(budget_manifest)
        
        print(f"✅ Зарегистрировано инструментов: {len(tool_registry.tools)}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка регистрации: {e}")
        return False

def test_tool_interfaces():
    """Тест получения интерфейсов инструментов."""
    print("\n🔍 Тестирование интерфейсов инструментов...")
    
    try:
        # Получаем все интерфейсы
        interfaces = tool_registry.get_all_interfaces()
        print(f"✅ Получено интерфейсов: {len(interfaces)}")
        
        # Тестируем каждый инструмент
        for tool_name, interface in interfaces.items():
            print(f"\n📋 Инструмент: {tool_name}")
            print(f"   Назначение: {interface.purpose}")
            print(f"   Параметры: {list(interface.input_requirements.keys())}")
            print(f"   Шагов выполнения: {len(interface.execution_flow)}")
            print(f"   Производительность: {interface.integration_notes.get('performance', 'Неизвестно')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка получения интерфейсов: {e}")
        return False

def test_coordinator_planning():
    """Тест планирования с координатором."""
    print("\n🤖 Тестирование планирования координатора...")
    
    try:
        coordinator = CoordinatorWithToolInterfaces()
        
        # Тестируем поиск инструментов
        search_tools = coordinator.find_tools_by_purpose(["поиск", "документы"])
        print(f"✅ Найдено инструментов для поиска: {search_tools}")
        
        budget_tools = coordinator.find_tools_by_purpose(["бюджет", "расчет"])
        print(f"✅ Найдено инструментов для бюджета: {budget_tools}")
        
        # Тестируем планирование
        test_queries = [
            "найти документы о бетоне",
            "рассчитать бюджет строительства",
            "создать письмо поставщику"
        ]
        
        for query in test_queries:
            print(f"\n📝 Запрос: {query}")
            plan = coordinator.plan_with_tool_interfaces(query)
            print(f"   Статус: {plan.get('status', 'unknown')}")
            if plan.get('status') == 'success':
                print(f"   Выбранный инструмент: {plan.get('selected_tool', 'unknown')}")
                print(f"   Назначение: {plan.get('tool_purpose', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка планирования: {e}")
        return False

def test_tool_capabilities():
    """Тест получения возможностей инструментов."""
    print("\n⚡ Тестирование возможностей инструментов...")
    
    try:
        coordinator = CoordinatorWithToolInterfaces()
        
        # Получаем сводку по всем инструментам
        summary = coordinator.get_tool_interface_summary()
        print(f"✅ Получена сводка по {len(summary)} инструментам")
        
        for tool_name, info in summary.items():
            print(f"\n🔧 {tool_name}:")
            print(f"   Назначение: {info['purpose']}")
            print(f"   Параметры: {info['input_params']}")
            print(f"   Шагов: {info['execution_steps']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка получения возможностей: {e}")
        return False

def test_tool_search():
    """Тест поиска инструментов по ключевым словам."""
    print("\n🔍 Тестирование поиска инструментов...")
    
    try:
        # Тестируем поиск по разным ключевым словам
        search_terms = [
            ["поиск", "документы"],
            ["бюджет", "расчет"],
            ["письмо", "генерация"],
            ["анализ", "данные"]
        ]
        
        for terms in search_terms:
            matching = tool_registry.find_tools_by_purpose(terms)
            print(f"✅ Поиск по {terms}: {matching}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка поиска: {e}")
        return False

def main():
    """Основная функция тестирования."""
    print("🚀 ТЕСТИРОВАНИЕ УНИВЕРСАЛЬНОГО ПРЕДСТАВЛЕНИЯ ИНСТРУМЕНТОВ")
    print("=" * 60)
    
    tests = [
        ("Регистрация инструментов", test_tool_registration),
        ("Интерфейсы инструментов", test_tool_interfaces),
        ("Планирование координатора", test_coordinator_planning),
        ("Возможности инструментов", test_tool_capabilities),
        ("Поиск инструментов", test_tool_search)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}...")
        try:
            if test_func():
                print(f"✅ {test_name} - ПРОЙДЕН")
                passed += 1
            else:
                print(f"❌ {test_name} - ПРОВАЛЕН")
        except Exception as e:
            print(f"❌ {test_name} - ОШИБКА: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 РЕЗУЛЬТАТЫ: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Универсальное представление работает!")
        return True
    else:
        print("⚠️ Некоторые тесты не пройдены. Требуется доработка.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
