#!/usr/bin/env python3
"""
Создание тестовой сметы для проверки
"""

import pandas as pd
import os

def create_test_smeta():
    """Создание простой тестовой сметы"""
    print("📊 Создание тестовой сметы...")
    
    # Создаем простую тестовую смету
    data = {
        'Наименование работ': [
            'Устройство бетонной подготовки',
            'Устройство монолитных бетонных конструкций',
            'Устройство сборных железобетонных фундаментов'
        ],
        'Ед.изм': ['м3', 'м3', 'шт'],
        'Количество': [100, 250, 20],
        'Цена за ед.': [15000, 25000, 30000],
        'Сумма': [1500000, 6250000, 600000]
    }
    
    df = pd.DataFrame(data)
    output_file = 'test_smeta_simple.xlsx'
    df.to_excel(output_file, index=False, sheet_name='Смета')
    
    print(f"✅ Тестовая смета создана: {output_file}")
    print(f"📁 Путь: {os.path.abspath(output_file)}")
    
    return output_file

if __name__ == "__main__":
    create_test_smeta()
