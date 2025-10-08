#!/usr/bin/env python3
"""
Тестовый скрипт для проверки улучшенных парсеров смет и бюджета
"""

import os
import sys
import json
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_smeta_parser():
    """Тестирование улучшенного парсера смет"""
    print("🔧 Тестирование улучшенного парсера смет...")
    
    try:
        from core.enhanced_smeta_parser import EnhancedSmetaParser
        
        parser = EnhancedSmetaParser()
        print("✅ Улучшенный парсер смет загружен")
        
        # Тестируем определение формата
        test_file = "I:\\нейросетки\\стройтэк\\прога\\02-10-01 КЖ - ЛСР по Методике 2020 (БИМ).xlsx"
        if os.path.exists(test_file):
            format_type = parser.detect_format(test_file)
            print(f"📊 Определен формат: {format_type.value}")
            
            # Тестируем парсинг
            result = parser.parse_excel_estimate(test_file)
            print(f"📈 Найдено позиций: {result.get('positions_count', 0)}")
            print(f"💰 Общая стоимость: {result.get('total_cost', 0):,.2f} руб.")
            print(f"📋 Формат: {result.get('format', 'unknown')}")
            
            # Показываем первые 3 позиции
            positions = result.get('positions', [])
            if positions:
                print("\n📝 Первые 3 позиции:")
                for i, pos in enumerate(positions[:3], 1):
                    print(f"  {i}. {pos.get('description', 'N/A')[:50]}...")
                    print(f"     Код: {pos.get('code', 'N/A')}")
                    print(f"     Стоимость: {pos.get('total_cost', 0):,.2f} руб.")
        else:
            print(f"⚠️ Тестовый файл не найден: {test_file}")
            
    except Exception as e:
        print(f"❌ Ошибка тестирования парсера смет: {e}")
        import traceback
        traceback.print_exc()

def test_enhanced_budget_parser():
    """Тестирование улучшенного парсера бюджета"""
    print("\n💰 Тестирование улучшенного парсера бюджета...")
    
    try:
        from core.enhanced_budget_parser import EnhancedBudgetParser
        
        parser = EnhancedBudgetParser()
        print("✅ Улучшенный парсер бюджета загружен")
        
        # Тестируем расчет бюджета на основе сметы
        test_estimate_data = {
            'total_cost': 50_000_000,  # 50 млн руб
            'project_name': 'Тестовый проект',
            'project_type': 'residential'
        }
        
        result = parser.calculate_budget_from_estimate(test_estimate_data)
        
        if result.get('status') == 'success':
            print(f"📊 Базовая стоимость: {result.get('base_cost', 0):,.2f} руб.")
            print(f"💸 Общие расходы: {result.get('total_expenses', 0):,.2f} руб.")
            print(f"💵 Чистая прибыль: {result.get('net_profit', 0):,.2f} руб.")
            print(f"📈 Маржа прибыли: {result.get('profit_margin', 0):.2f}%")
            
            # Показываем статьи бюджета
            budget_items = result.get('budget_items', {})
            if budget_items:
                print("\n📋 Статьи бюджета:")
                for item_code, item_data in budget_items.items():
                    print(f"  • {item_data['name']}: {item_data['amount']:,.2f} руб. ({item_data['percentage']}%)")
        else:
            print(f"❌ Ошибка расчета бюджета: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Ошибка тестирования парсера бюджета: {e}")
        import traceback
        traceback.print_exc()

def test_integration():
    """Тестирование интеграции с существующей системой"""
    print("\n🔗 Тестирование интеграции...")
    
    try:
        # Тестируем обновленный estimate_parser_enhanced
        from core.estimate_parser_enhanced import parse_estimate_gesn
        
        test_file = "I:\\нейросетки\\стройтэк\\прога\\02-10-01 КЖ - ЛСР по Методике 2020 (БИМ).xlsx"
        if os.path.exists(test_file):
            result = parse_estimate_gesn(test_file)
            print(f"✅ Интеграция работает")
            print(f"📊 Позиций: {len(result.get('positions', []))}")
            print(f"💰 Общая стоимость: {result.get('total_cost', 0):,.2f} руб.")
            print(f"📋 Формат: {result.get('format', 'unknown')}")
        else:
            print(f"⚠️ Тестовый файл не найден: {test_file}")
            
    except Exception as e:
        print(f"❌ Ошибка тестирования интеграции: {e}")
        import traceback
        traceback.print_exc()

def test_auto_budget_tool():
    """Тестирование обновленного auto_budget инструмента"""
    print("\n🛠️ Тестирование auto_budget инструмента...")
    
    try:
        from tools.custom.auto_budget import execute
        
        # Тестируем выполнение инструмента
        result = execute(
            project_name="Тестовый проект",
            base_cost=100_000_000,
            project_type="residential"
        )
        
        if result.get('status') == 'success':
            print("✅ auto_budget инструмент работает")
            data = result.get('data', {})
            print(f"💰 Общая стоимость: {data.get('total_cost', 0):,.2f} руб.")
            print(f"📊 Статус: {result.get('status')}")
            print(f"⏱️ Время выполнения: {result.get('execution_time', 0):.2f} сек.")
        else:
            print(f"❌ Ошибка auto_budget: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Ошибка тестирования auto_budget: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Основная функция тестирования"""
    print("🚀 ТЕСТИРОВАНИЕ УЛУЧШЕННЫХ ПАРСЕРОВ")
    print("=" * 50)
    
    # Тестируем все компоненты
    test_enhanced_smeta_parser()
    test_enhanced_budget_parser()
    test_integration()
    test_auto_budget_tool()
    
    print("\n🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
    print("=" * 50)

if __name__ == "__main__":
    main()
