#!/usr/bin/env python3
"""
Тест исправления auto_budget
"""

from tools.custom.auto_budget import execute

def test_auto_budget():
    """Тестирование исправленного auto_budget"""
    print("🛠️ Тестирование исправленного auto_budget...")
    
    try:
        result = execute(
            project_name='Тестовый проект',
            base_cost=100_000_000,
            project_type='residential'
        )
        
        print('Результат тестирования:')
        print(f'Статус: {result.get("status")}')
        
        if result.get('status') == 'success':
            data = result.get('data', {})
            print(f'Общая стоимость: {data.get("total_cost", 0):,.2f} руб.')
            budget = data.get('budget', {})
            print(f'Чистая прибыль: {budget.get("net_profit", 0):,.2f} руб.')
            print(f'Маржа прибыли: {budget.get("profit_margin", 0):.2f}%')
            print('✅ auto_budget работает корректно!')
        else:
            print(f'Ошибка: {result.get("error", "Unknown error")}')
            
    except Exception as e:
        print(f'❌ Ошибка тестирования: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_auto_budget()
