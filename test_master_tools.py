#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки Master Tools System
"""

import sys
import os
sys.path.append('C:/Bldr/core')

def test_master_tools_system():
    """Тестирование Master Tools System"""
    print("🚀 MASTER TOOLS SYSTEM - ТЕСТ")
    print("=" * 50)
    
    try:
        # Импортируем систему
        from master_tools_system import MasterToolsSystem, get_master_tools_system
        print("✅ Импорт модуля успешен")
        
        # Создаём экземпляр системы
        mts = MasterToolsSystem()
        print("✅ Создание MasterToolsSystem успешно")
        
        # Получаем список всех инструментов
        tools_info = mts.list_all_tools()
        print(f"✅ Загружено {tools_info['total_count']} инструментов")
        print(f"📊 Категории: {', '.join(tools_info['categories'])}")
        
        # Тестируем конкретные инструменты
        test_cases = [
            {
                "name": "search_rag_database",
                "params": {"query": "строительные нормы"},
                "expected": "success"
            },
            {
                "name": "create_pie_chart", 
                "params": {"data": {"Материалы": 40, "Работа": 35, "Накладные": 25}},
                "expected": "success"
            },
            {
                "name": "calculate_financial_metrics",
                "params": {
                    "metric_type": "roi",
                    "investment": 1000000,
                    "cash_flows": [300000, 400000, 500000]
                },
                "expected": "success"  
            },
            {
                "name": "extract_works_nlp",
                "params": {
                    "text": "Выполнение работ по устройству фундамента. Монтаж конструкций здания.",
                    "doc_type": "norms"
                },
                "expected": "success"
            }
        ]
        
        print(f"\n🧪 Тестирование {len(test_cases)} инструментов:")
        
        passed_tests = 0
        for i, test_case in enumerate(test_cases, 1):
            tool_name = test_case["name"]
            params = test_case["params"]
            expected = test_case["expected"]
            
            try:
                result = mts.execute_tool(tool_name, **params)
                
                if expected == "success" and result.is_success():
                    print(f"  ✅ {i}. {tool_name}: PASSED")
                    passed_tests += 1
                elif expected == "error" and not result.is_success():
                    print(f"  ✅ {i}. {tool_name}: PASSED (expected error)")
                    passed_tests += 1
                else:
                    print(f"  ❌ {i}. {tool_name}: FAILED - {result.error}")
                    
            except Exception as e:
                print(f"  ❌ {i}. {tool_name}: EXCEPTION - {str(e)}")
        
        # Тестируем информацию об инструментах
        print(f"\n📋 Информация об инструментах:")
        sample_tools = ["generate_letter", "auto_budget", "analyze_image"]
        
        for tool_name in sample_tools:
            tool_info = mts.get_tool_info(tool_name)
            if "error" not in tool_info:
                print(f"  ℹ️  {tool_name}: {tool_info['category']}, {len(tool_info['required_params'])} обяз. параметров")
            else:
                print(f"  ❌ {tool_name}: не найден")
        
        # Тестируем статистику
        print(f"\n📈 Статистика выполнения:")
        stats = mts.get_execution_stats()
        if stats:
            for tool_name, tool_stats in stats.items():
                success_rate = (tool_stats['successful_calls'] / tool_stats['total_calls']) * 100
                print(f"  📊 {tool_name}: {success_rate:.1f}% успех, {tool_stats['avg_execution_time']:.3f}s")
        else:
            print("  📊 Статистика пуста (инструменты не выполнялись)")
        
        # Тестируем цепочку инструментов
        print(f"\n🔗 Тестирование цепочки инструментов:")
        chain = [
            {
                "tool": "extract_works_nlp",
                "params": {
                    "text": "Устройство фундамента железобетонного. Монтаж стен из кирпича."
                }
            },
            {
                "tool": "create_pie_chart",
                "params": {
                    "data": {"Фундамент": 60, "Стены": 40},
                    "title": "Распределение работ"
                }
            }
        ]
        
        try:
            chain_results = mts.execute_tool_chain(chain)
            successful_steps = sum(1 for r in chain_results if r.is_success())
            print(f"  🔗 Цепочка: {successful_steps}/{len(chain)} шагов успешно")
        except Exception as e:
            print(f"  ❌ Ошибка цепочки: {str(e)}")
        
        # Итоговый результат
        print(f"\n🏆 РЕЗУЛЬТАТ ТЕСТИРОВАНИЯ:")
        print(f"  Пройдено тестов: {passed_tests}/{len(test_cases)}")
        print(f"  Процент успеха: {(passed_tests/len(test_cases))*100:.1f}%")
        
        if passed_tests == len(test_cases):
            print("  🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Master Tools System готов к использованию!")
        else:
            print("  ⚠️  Некоторые тесты не прошли. Требуется доработка.")
            
        # Демонстрация удобных функций
        print(f"\n🛠  Демонстрация convenience functions:")
        from master_tools_system import execute_tool, list_available_tools
        
        # Список pro инструментов
        pro_tools = list_available_tools("pro_features")
        if "error" not in pro_tools:
            print(f"  📋 PRO инструменты: {pro_tools['total_count']}")
        
        # Быстрое выполнение инструмента
        quick_result = execute_tool("create_bar_chart", 
                                  data={"Q1": 100, "Q2": 120, "Q3": 90, "Q4": 110},
                                  title="Квартальная отчетность")
        
        if quick_result.is_success():
            print(f"  ⚡ Быстрое выполнение: успех за {quick_result.execution_time:.3f}s")
        else:
            print(f"  ❌ Быстрое выполнение: {quick_result.error}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_master_tools_system()
    exit(0 if success else 1)