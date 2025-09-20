#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Установка poppler для pdf2image на Windows
"""

import os
import sys
import urllib.request
import zipfile
import shutil
from pathlib import Path

def setup_poppler():
    """Установка poppler на Windows"""
    
    print("🔧 УСТАНОВКА POPPLER ДЛЯ PDF2IMAGE")
    print("=" * 40)
    
    # Пути
    poppler_dir = Path("C:/poppler")
    poppler_bin = poppler_dir / "bin"
    
    # Проверяем, уже установлен ли poppler
    if poppler_bin.exists():
        pdftoppm_path = poppler_bin / "pdftoppm.exe"
        if pdftoppm_path.exists():
            print(f"✅ Poppler уже установлен: {poppler_bin}")
            
            # Добавляем в PATH
            current_path = os.environ.get('PATH', '')
            poppler_bin_str = str(poppler_bin)
            if poppler_bin_str not in current_path:
                os.environ['PATH'] = f"{poppler_bin_str};{current_path}"
                print(f"✅ Poppler добавлен в PATH: {poppler_bin_str}")
            
            return True
    
    print("📥 Скачивание poppler...")
    
    # URL для скачивания poppler (версия 24.02.0)
    poppler_url = "https://github.com/oschwartz10612/poppler-windows/releases/download/v24.02.0-0/Release-24.02.0-0.zip"
    zip_path = "poppler.zip"
    
    try:
        # Скачиваем poppler
        print(f"🔄 Скачивание {poppler_url}...")
        urllib.request.urlretrieve(poppler_url, zip_path)
        print(f"✅ Скачано: {zip_path}")
        
        # Распаковываем
        print("📦 Распаковка...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(".")
        
        # Перемещаем в правильную папку
        extracted_folder = None
        for item in os.listdir("."):
            if os.path.isdir(item) and "poppler" in item.lower():
                extracted_folder = item
                break
        
        if extracted_folder:
            print(f"🔄 Перемещение {extracted_folder} -> {poppler_dir}")
            if poppler_dir.exists():
                shutil.rmtree(poppler_dir)
            shutil.move(extracted_folder, poppler_dir)
            
            # Проверяем установку
            pdftoppm_path = poppler_bin / "pdftoppm.exe"
            if pdftoppm_path.exists():
                print(f"✅ Poppler установлен успешно: {poppler_bin}")
                
                # Добавляем в PATH
                current_path = os.environ.get('PATH', '')
                poppler_bin_str = str(poppler_bin)
                if poppler_bin_str not in current_path:
                    os.environ['PATH'] = f"{poppler_bin_str};{current_path}"
                    print(f"✅ Poppler добавлен в PATH")
                
                return True
            else:
                print(f"❌ Не найден pdftoppm.exe в {poppler_bin}")
                return False
        else:
            print("❌ Не найдена папка poppler в архиве")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка установки poppler: {e}")
        return False
        
    finally:
        # Очистка
        if os.path.exists(zip_path):
            os.remove(zip_path)

def test_poppler():
    """Тест poppler"""
    print("\n🧪 ТЕСТ POPPLER")
    print("=" * 20)
    
    try:
        import pdf2image
        
        # Найдем тестовый PDF
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
        
        if test_pdf:
            print(f"🔍 Тестовый файл: {test_pdf}")
            
            # Пробуем конвертировать
            images = pdf2image.convert_from_path(
                test_pdf, 
                dpi=150, 
                first_page=1, 
                last_page=1
            )
            
            if images:
                print(f"✅ PDF2IMAGE РАБОТАЕТ! Конвертировано {len(images)} страниц")
                return True
            else:
                print("❌ PDF2IMAGE не смог конвертировать страницы")
                return False
        else:
            print("⚠️ Не найдено PDF файлов для теста")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка теста poppler: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 НАСТРОЙКА OCR ИНФРАСТРУКТУРЫ")
    print("=" * 50)
    
    success = setup_poppler()
    
    if success:
        test_success = test_poppler()
        if test_success:
            print("\n🎉 POPPLER ГОТОВ К РАБОТЕ!")
            sys.exit(0)
        else:
            print("\n❌ POPPLER НЕ ПРОШЕЛ ТЕСТ!")
            sys.exit(1)
    else:
        print("\n❌ POPPLER НЕ УСТАНОВЛЕН!")
        sys.exit(1)