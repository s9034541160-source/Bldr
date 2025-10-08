#!/usr/bin/env python3
"""
Скрипт для сравнения расчетов бюджета между разными методами
"""

from tools.custom.auto_budget import _calculate_comprehensive_budget
from core.enhanced_budget_parser import EnhancedBudgetParser

def test_comprehensive_budget():
    """Тестирование комплексного расчета бюджета"""
    print("=== Расчет бюджета через _calculate_comprehensive_budget ===")
    
    # Параметры для теста
    base_cost = 100_000_000  # 100 миллионов рублей
    project_type = 'residential'
    profit_margin = 0.15
    overhead_rate = 0.20
    tax_rate = 0.20
    risk_factor = 0.05
    inflation_rate = 0.08
    project_duration = 12
    currency = 'RUB'
    
    result = _calculate_comprehensive_budget(
        base_cost, project_type, profit_margin, overhead_rate,
        tax_rate, risk_factor, inflation_rate, project_duration, currency
    )
    
    print(f"Базовая стоимость: {result['base_cost']:,.2f} руб.")
    print(f"Накладные расходы: {result['overhead_cost']:,.2f} руб. ({overhead_rate*100:.1f}%)")
    print(f"Прибыль: {result['profit_cost']:,.2f} руб. ({profit_margin*100:.1f}%)")
    print(f"Резерв на риски: {result['risk_cost']:,.2f} руб. ({risk_factor*100:.1f}%)")
    print(f"Инфляционная корректировка: {result['inflation_cost']:,.2f} руб. ({inflation_rate*100:.1f}% * {project_duration/12:.1f} лет)")
    print(f"Налоги: {result['tax_cost']:,.2f} руб. ({tax_rate*100:.1f}% от подитога)")
    print(f"Подитог: {result['subtotal']:,.2f} руб.")
    print(f"ИТОГО: {result['total_cost']:,.2f} руб.")
    print()
    
    return result

def test_enhanced_parser():
    """Тестирование улучшенного парсера бюджета"""
    print("=== Расчет бюджета через EnhancedBudgetParser ===")
    
    parser = EnhancedBudgetParser()
    estimate_data = {'total_cost': 100_000_000}
    result = parser.calculate_budget_from_estimate(estimate_data)
    
    if result.get('status') == 'success':
        print(f"Базовая стоимость: {result['base_cost']:,.2f} руб.")
        budget_items = result.get('budget_items', {})
        
        total_expenses = 0
        for item_code, item_data in budget_items.items():
            print(f"{item_data['name']}: {item_data['amount']:,.2f} руб. ({item_data['percentage']:.2f}%)")
            total_expenses += item_data['amount']
        
        print(f"ИТОГО РАСХОДЫ: {total_expenses:,.2f} руб.")
        print(f"ЧИСТАЯ ПРИБЫЛЬ: {result['net_profit']:,.2f} руб.")
        print(f"МАРЖА ПРИБЫЛИ: {result['profit_margin']:.2f}%")
        print()
        
        return result
    else:
        print(f"Ошибка: {result.get('error')}")
        return None

def main():
    """Основная функция"""
    print("СРАВНЕНИЕ МЕТОДОВ РАСЧЕТА БЮДЖЕТА")
    print("=" * 50)
    
    # Тестируем оба метода
    comprehensive_result = test_comprehensive_budget()
    enhanced_result = test_enhanced_parser()
    
    if comprehensive_result and enhanced_result:
        print("=== СРАВНЕНИЕ РЕЗУЛЬТАТОВ ===")
        print(f"Комплексный расчет - ИТОГО: {comprehensive_result['total_cost']:,.2f} руб.")
        print(f"Улучшенный парсер - ИТОГО РАСХОДЫ: {enhanced_result['total_expenses']:,.2f} руб.")
        print(f"Улучшенный парсер - ЧИСТАЯ ПРИБЫЛЬ: {enhanced_result['net_profit']:,.2f} руб.")
        print(f"Разница в прибыли: {comprehensive_result['total_cost'] - enhanced_result['net_profit']:,.2f} руб.")

if __name__ == "__main__":
    main()