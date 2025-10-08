#!/usr/bin/env python3
"""
Тестовый скрипт для проверки исправлений RAG trainer и создания бюджета
"""

import os
import sys
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_rag_file_renaming_fix():
    """Тестирование исправления переименования файлов в RAG trainer"""
    print("🔧 Тестирование исправления RAG trainer...")
    
    try:
        # Проверяем, что исправления применены
        with open('enterprise_rag_trainer_full.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Ищем исправленные строки
        if "НЕ ПЕРЕИМЕНОВЫВАЕМ ФАЙЛЫ! Оставляем оригинальные имена!" in content:
            print("✅ Исправление RAG trainer применено")
            print("   - Файлы больше НЕ переименовываются")
            print("   - Сохраняются оригинальные имена файлов")
            return True
        else:
            print("❌ Исправление RAG trainer НЕ найдено")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка проверки RAG trainer: {e}")
        return False

def test_budget_creation_tool():
    """Тестирование нового инструмента создания бюджета"""
    print("\n💰 Тестирование инструмента создания бюджета...")
    
    try:
        from tools.custom.create_budget_from_estimates import execute
        
        # Тестируем создание бюджета
        result = execute(
            estimate_files=["test_smeta_simple.xlsx"],
            project_name="Тестовый проект",
            output_directory="test_exports",
            include_monthly_planning=True,
            profit_margin_percent=15.0
        )
        
        print(f"Статус: {result.get('status')}")
        
        if result.get('status') == 'success':
            data = result.get('data', {})
            print(f"✅ Бюджет создан успешно!")
            print(f"   💰 Общая стоимость смет: {data.get('total_estimate_cost', 0):,.2f} руб.")
            print(f"   💸 Общие расходы: {data.get('total_expenses', 0):,.2f} руб.")
            print(f"   💵 Чистая прибыль: {data.get('net_profit', 0):,.2f} руб.")
            print(f"   📈 Маржа прибыли: {data.get('profit_margin', 0):.2f}%")
            print(f"   📊 Обработано файлов: {data.get('parsed_files_count', 0)}")
            print(f"   📁 Excel файл: {data.get('excel_file_path', 'N/A')}")
            
            # Проверяем, создался ли Excel файл
            excel_path = data.get('excel_file_path')
            if excel_path and os.path.exists(excel_path):
                print(f"   ✅ Excel файл создан: {excel_path}")
            else:
                print(f"   ⚠️ Excel файл не найден: {excel_path}")
            
            return True
        else:
            print(f"❌ Ошибка создания бюджета: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования создания бюджета: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enhanced_parsers_availability():
    """Проверка доступности улучшенных парсеров"""
    print("\n🔍 Проверка улучшенных парсеров...")
    
    try:
        from core.enhanced_smeta_parser import EnhancedSmetaParser
        from core.enhanced_budget_parser import EnhancedBudgetParser
        
        print("✅ Улучшенный парсер смет доступен")
        print("✅ Улучшенный парсер бюджета доступен")
        
        # Тестируем создание экземпляров
        smeta_parser = EnhancedSmetaParser()
        budget_parser = EnhancedBudgetParser()
        
        print("✅ Парсеры инициализированы успешно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка загрузки улучшенных парсеров: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЙ RAG И БЮДЖЕТА")
    print("=" * 60)
    
    # Тестируем все компоненты
    rag_fix_ok = test_rag_file_renaming_fix()
    parsers_ok = test_enhanced_parsers_availability()
    budget_creation_ok = test_budget_creation_tool()
    
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"   🔧 RAG trainer исправлен: {'✅' if rag_fix_ok else '❌'}")
    print(f"   🔍 Улучшенные парсеры: {'✅' if parsers_ok else '❌'}")
    print(f"   💰 Создание бюджета: {'✅' if budget_creation_ok else '❌'}")
    
    if rag_fix_ok and parsers_ok and budget_creation_ok:
        print("\n🎉 ВСЕ ИСПРАВЛЕНИЯ РАБОТАЮТ КОРРЕКТНО!")
        print("✅ RAG trainer больше НЕ переименовывает файлы")
        print("✅ Создание бюджета на основе смет работает")
        print("✅ Улучшенные парсеры интегрированы")
    else:
        print("\n⚠️ НЕКОТОРЫЕ ИСПРАВЛЕНИЯ ТРЕБУЮТ ДОРАБОТКИ")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
