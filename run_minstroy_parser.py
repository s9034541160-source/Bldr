#!/usr/bin/env python3
"""
Простой скрипт для запуска парсера Минстроя
"""

import sys
import os
from minstroy_parser import MinstroyParser

def main():
    print("Парсер Минстроя России")
    print("=" * 40)
    
    # Проверка зависимостей
    try:
        import requests
        import bs4
    except ImportError as e:
        print(f"ОШИБКА: Отсутствует зависимость: {e}")
        print("Установите зависимости: pip install requests beautifulsoup4")
        return 1
    
    # Создание парсера
    try:
        parser = MinstroyParser()
    except Exception as e:
        print(f"ОШИБКА: Ошибка инициализации парсера: {e}")
        return 1
    
    # Запуск парсинга
    try:
        print("Начинаем парсинг...")
        results = parser.parse_and_download()
        
        if results["success"]:
            print("\nПарсинг завершен успешно!")
            return 0
        else:
            print(f"\nОШИБКА парсинга: {results.get('error', 'Неизвестная ошибка')}")
            return 1
            
    except KeyboardInterrupt:
        print("\nПарсинг прерван пользователем")
        return 1
    except Exception as e:
        print(f"\nКРИТИЧЕСКАЯ ОШИБКА: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
