#!/usr/bin/env python3
"""
Тестирование Stage 0 - NTD Preprocessing с автоматической сортировкой в БАЗА
"""

import os
import sys
import shutil
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.ntd_preprocessor import initialize_ntd_system, ntd_preprocess, _determine_document_category

def test_category_detection():
    """Тест определения категорий документов"""
    print("🧪 Тестирование определения категорий документов")
    print("=" * 60)
    
    test_files = [
        ("SP_25.13330.2020.pdf", "СП 25.13330.2020 Конструкции каменные и армокаменные", "09. СВОДЫ ПРАВИЛ"),
        ("GOST_52742-2007.pdf", "ГОСТ 52742-2007 Арматура стеклопластиковая", "07. ГОСТы"),
        ("SNiP_2.02.01-83.pdf", "СНиП 2.02.01-83 Основания зданий и сооружений", "08. СНИПы"),
        ("GESN_01.pdf", "ГЭСН 01 Земляные работы", "05. ГЭСНЫ"),
        ("MDS_21-1.98.pdf", "МДС 21-1.98 Методические документы в строительстве", "02. МДС"),
        ("PPR_Karkas.pdf", "Проект производства работ на строительство каркаса", "03. ПОС/ППР"),
        ("Act_Skrytyh_Rabot.pdf", "Акт освидетельствования скрытых работ", "06. ОБРАЗЦЫ ДОКУМЕНТОВ"),
        ("Tipovoy_Proekt_Zhiloy_Dom.pdf", "Типовой проект жилого дома серии П-44Т", "04. ТИПОВЫЕ ПРОЕКТЫ"),
        ("Prikaz_Minstroya_123.pdf", "Приказ Минстроя России №123 от 01.01.2024", "01. НТД"),
        ("Neizvestny_Dokument.pdf", "Документ неизвестного типа", "10. ДРУГИЕ ДОКУМЕНТЫ")
    ]
    
    correct_predictions = 0
    for file_name, content, expected_category in test_files:
        predicted_category = _determine_document_category(file_name.lower(), content)
        status = "✅" if predicted_category == expected_category else "❌"
        print(f"{status} {file_name}")
        print(f"   Ожидалось: {expected_category}")
        print(f"   Получено:  {predicted_category}")
        
        if predicted_category == expected_category:
            correct_predictions += 1
        print()
    
    accuracy = (correct_predictions / len(test_files)) * 100
    print(f"🎯 Точность: {correct_predictions}/{len(test_files)} ({accuracy:.1f}%)")
    return accuracy > 80  # Требуем точность выше 80%

def test_full_stage0_processing():
    """Тест полной обработки Stage 0"""
    print("\n🧪 Тестирование полной обработки Stage 0")
    print("=" * 60)
    
    # Создаем тестовые файлы
    test_dir = Path("C:/temp/test_ntd")
    test_dir.mkdir(exist_ok=True)
    
    test_files = [
        "SP_25.13330.2020_Konstrukcii_kamennye.pdf",
        "GOST_52742-2007_Armatura_stekloplastikovaya.pdf", 
        "GESN_01_Zemlyanye_raboty.pdf",
        "MDS_21-1.98_Metodicheskie_dokumenty.pdf",
        "PPR_Stroitelstvo_karkasa.pdf"
    ]
    
    # Создаем фиктивные файлы для теста с содержимым, соответствующим их типу
    for file_name in test_files:
        test_file = test_dir / file_name
        # Создаем содержимое, соответствующее типу документа
        if "SP_" in file_name or "СП_" in file_name:
            content = f"СП 25.13330.2020 Конструкции каменные и армокаменные\n{file_name}\nСвод правил\nТестовый документ для проверки сортировки"
        elif "GOST_" in file_name or "ГОСТ_" in file_name:
            content = f"ГОСТ 52742-2007 Арматура стеклопластиковая\n{file_name}\nГосударственный стандарт\nТестовый документ для проверки сортировки"
        elif "GESN_" in file_name or "ГЭСН_" in file_name:
            content = f"ГЭСН 01 Земляные работы\n{file_name}\nГосударственные элементные сметные нормы\nТестовый документ для проверки сортировки"
        elif "MDS_" in file_name or "МДС_" in file_name:
            content = f"МДС 21-1.98 Методические документы в строительстве\n{file_name}\nМетодические документы\nТестовый документ для проверки сортировки"
        elif "PPR_" in file_name or "ППР_" in file_name:
            content = f"ППР Строительство каркаса\n{file_name}\nПроект производства работ\nТестовый документ для проверки сортировки"
        else:
            content = f"Test content for {file_name}\nТестовый документ для проверки сортировки"
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"📄 Создан тестовый файл: {file_name}")
    
    # Инициализируем систему НТД
    try:
        print("\n🔧 Инициализация системы НТД...")
        normative_db, normative_checker = initialize_ntd_system()
        print("✅ Система НТД инициализирована")
        
        # Обрабатываем каждый файл
        processed_files = []
        for file_name in test_files:
            test_file = test_dir / file_name
            print(f"\n🔄 Обработка файла: {file_name}")
            
            result = ntd_preprocess(str(test_file), normative_db, normative_checker, test_mode=True)
            
            if result:
                print(f"✅ Файл обработан: {result}")
                processed_files.append(result)
                
                # Проверяем, что файл переместился в правильную папку БАЗА
                if "БАЗА" in result:
                    print(f"📁 Файл перемещён в структуру БАЗА: {Path(result).parent.name}")
                else:
                    print("⚠️ Файл не был перемещён в БАЗА")
            else:
                print(f"❌ Ошибка обработки файла: {file_name}")
        
        print(f"\n📊 Результат: {len(processed_files)}/{len(test_files)} файлов успешно обработано")
        
        # Проверяем структуру папок БАЗА
        print("\n📁 Проверка структуры БАЗА:")
        base_path = Path("I:/docs/БАЗА")
        if base_path.exists():
            for folder in base_path.iterdir():
                if folder.is_dir():
                    file_count = len([f for f in folder.iterdir() if f.is_file()])
                    print(f"   {folder.name}: {file_count} файлов")
        
        # Очистка тестовых файлов
        print(f"\n🧹 Очистка тестовых файлов...")
        shutil.rmtree(test_dir, ignore_errors=True)
        print("✅ Тестовые файлы удалены")
        
        return len(processed_files) > 0
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_baza_structure():
    """Показать текущую структуру БАЗА"""
    print("\n📁 ТЕКУЩАЯ СТРУКТУРА БАЗА:")
    print("=" * 60)
    
    base_path = Path("I:/docs/БАЗА")
    if not base_path.exists():
        print("❌ Папка БАЗА не существует")
        return
    
    total_files = 0
    for folder in sorted(base_path.iterdir()):
        if folder.is_dir():
            files = [f for f in folder.iterdir() if f.is_file()]
            file_count = len(files)
            total_files += file_count
            
            print(f"📂 {folder.name}: {file_count} файлов")
            
            # Показываем первые 3 файла как примеры
            for i, file in enumerate(files[:3]):
                print(f"   📄 {file.name}")
            
            if file_count > 3:
                print(f"   ... и ещё {file_count - 3} файлов")
            print()
    
    print(f"📊 Всего файлов в БАЗА: {total_files}")

if __name__ == "__main__":
    print("🧪 ТЕСТИРОВАНИЕ STAGE 0 - NTD PREPROCESSING")
    print("🔥 С АВТОМАТИЧЕСКОЙ СОРТИРОВКОЙ В СТРУКТУРУ БАЗА")
    print("=" * 80)
    
    # Показываем текущую структуру
    show_baza_structure()
    
    # Тест 1: Определение категорий
    success1 = test_category_detection()
    
    # Тест 2: Полная обработка Stage 0
    success2 = test_full_stage0_processing()
    
    print("\n" + "=" * 80)
    if success1 and success2:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("✅ Stage 0 готов к работе с автоматической сортировкой")
        print("📁 Файлы будут автоматически сортироваться в I:/docs/БАЗА/")
    else:
        print("❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
        if not success1:
            print("   - Проблемы с определением категорий")
        if not success2:
            print("   - Проблемы с полной обработкой Stage 0")
    print("=" * 80)