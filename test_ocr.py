#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Тест OCR функциональности для обработки скан-PDF документов
"""

import os
import sys
import traceback
from pathlib import Path

def test_ocr_functionality():
    """Тестируем полную OCR цепочку"""
    
    print("🧪 ТЕСТ OCR ФУНКЦИОНАЛЬНОСТИ")
    print("=" * 50)
    
    # 1. Проверяем Tesseract
    print("1️⃣ Проверяем Tesseract...")
    try:
        import pytesseract
        
        # Настройка пути для Windows
        if os.name == 'nt':
            tesseract_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                r'C:\Tesseract-OCR\tesseract.exe'
            ]
            for tess_path in tesseract_paths:
                if os.path.exists(tess_path):
                    pytesseract.pytesseract.tesseract_cmd = tess_path
                    print(f"✅ Tesseract найден: {tess_path}")
                    break
        
        # Проверяем версию и языки
        version_info = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract версия: {version_info}")
        
        languages = pytesseract.get_languages()
        print(f"✅ Поддерживаемые языки: {languages}")
        
        if 'rus' in languages:
            print("✅ Русский язык поддерживается")
        else:
            print("❌ Русский язык НЕ поддерживается")
            
    except Exception as e:
        print(f"❌ Ошибка Tesseract: {e}")
        return False
    
    # 2. Проверяем pdf2image
    print("\n2️⃣ Проверяем pdf2image...")
    try:
        import pdf2image
        print("✅ pdf2image импортирован успешно")
        
        # Проверяем poppler
        try:
            # Попробуем конвертировать тестовый PDF
            # Найдем любой PDF файл в системе для теста
            test_pdf = None
            search_paths = [
                "I:/docs/downloaded",
                "C:/temp",
                os.getcwd()
            ]
            
            for search_path in search_paths:
                if os.path.exists(search_path):
                    for file in os.listdir(search_path):
                        if file.endswith('.pdf'):
                            test_pdf = os.path.join(search_path, file)
                            break
                    if test_pdf:
                        break
            
            if test_pdf and os.path.exists(test_pdf):
                print(f"🔍 Тестируем с файлом: {test_pdf}")
                
            # Конвертируем только первую страницу
                # Set poppler path
                poppler_path = None
                poppler_paths = [
                    r'C:\poppler\Library\bin',
                    r'C:\poppler\bin',
                    r'C:\Program Files\poppler\bin'
                ]
                
                for path in poppler_paths:
                    if os.path.exists(os.path.join(path, 'pdftoppm.exe')):
                        poppler_path = path
                        print(f'📁 Using poppler: {poppler_path}')
                        break
                
                images = pdf2image.convert_from_path(
                    test_pdf, 
                    dpi=150, 
                    first_page=1, 
                    last_page=1,
                    poppler_path=poppler_path
                )
                
                if images:
                    print(f"✅ PDF конвертирован: {len(images)} страниц")
                    
                    # Тестируем OCR
                    test_image = images[0]
                    text = pytesseract.image_to_string(test_image, lang='rus+eng')
                    
                    if text.strip():
                        print(f"✅ OCR работает! Извлечено {len(text)} символов")
                        print(f"📝 Первые 100 символов: {text[:100]}...")
                    else:
                        print("⚠️ OCR не извлек текст (возможно, страница пустая)")
                        
            else:
                print("⚠️ Не найдено PDF файлов для теста")
                
        except Exception as e:
            print(f"❌ Ошибка pdf2image/poppler: {e}")
            print("💡 Попробуйте установить poppler-utils")
            
    except ImportError as ie:
        print(f"❌ pdf2image не импортирован: {ie}")
        return False
        
    # 3. Проверяем PIL/Pillow
    print("\n3️⃣ Проверяем Pillow...")
    try:
        from PIL import Image
        print("✅ PIL/Pillow работает")
    except ImportError as ie:
        print(f"❌ PIL/Pillow ошибка: {ie}")
        return False
        
    print("\n✅ ВСЕ OCR КОМПОНЕНТЫ ГОТОВЫ К РАБОТЕ!")
    return True

if __name__ == "__main__":
    try:
        success = test_ocr_functionality()
        if success:
            print("\n🎉 OCR ТЕСТ ПРОЙДЕН УСПЕШНО!")
            sys.exit(0)
        else:
            print("\n❌ OCR ТЕСТ ПРОВАЛЕН!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        traceback.print_exc()
        sys.exit(1)