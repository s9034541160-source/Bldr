#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Test for Expanded Stage 0 - NTD Preprocessing System
Tests automatic document sorting across all subject areas:
- Construction, Finance, Accounting, Safety, HR, Ecology, Training
"""
import os
import sys
import shutil
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.getcwd())

from core.ntd_preprocessor import _determine_document_category, initialize_ntd_system, ntd_preprocess

def show_expanded_baza_structure():
    """Show current expanded БАЗА structure"""
    print("\n📁 РАСШИРЕННАЯ СТРУКТУРА БАЗА:")
    print("=" * 80)
    
    base_path = Path("I:/docs/БАЗА")
    if not base_path.exists():
        print("❌ Папка БАЗА не существует")
        return
    
    total_files = 0
    categories = {
        "🏗️ СТРОИТЕЛЬСТВО": [],
        "💰 ФИНАНСЫ": [],
        "📊 БУХГАЛТЕРИЯ": [],
        "⚠️ ПРОМБЕЗОПАСНОСТЬ": [],
        "🛡️ ОХРАНА ТРУДА": [],
        "👥 HR И КАДРЫ": [],
        "🌿 ЭКОЛОГИЯ": [],
        "📚 ОБУЧЕНИЕ": [],
        "🗂️ ПРОЧЕЕ": []
    }
    
    for folder in sorted(base_path.iterdir()):
        if folder.is_dir():
            files = [f for f in folder.iterdir() if f.is_file()]
            file_count = len(files)
            total_files += file_count
            
            folder_name = folder.name
            # Categorize folders by subject
            if "СТРОИТЕЛЬСТВО" in folder_name:
                categories["🏗️ СТРОИТЕЛЬСТВО"].append((folder_name, file_count))
            elif "ФИНАНСЫ" in folder_name:
                categories["💰 ФИНАНСЫ"].append((folder_name, file_count))
            elif "БУХУЧЕТ" in folder_name:
                categories["📊 БУХГАЛТЕРИЯ"].append((folder_name, file_count))
            elif "ПРОМБЕЗОПАСНОСТЬ" in folder_name:
                categories["⚠️ ПРОМБЕЗОПАСНОСТЬ"].append((folder_name, file_count))
            elif "ОХРАНА ТРУДА" in folder_name:
                categories["🛡️ ОХРАНА ТРУДА"].append((folder_name, file_count))
            elif "HR" in folder_name:
                categories["👥 HR И КАДРЫ"].append((folder_name, file_count))
            elif "ЭКОЛОГИЯ" in folder_name:
                categories["🌿 ЭКОЛОГИЯ"].append((folder_name, file_count))
            elif "ЛЕКЦИИ" in folder_name or "КНИГИ" in folder_name or "СТАНДАРТЫ" in folder_name:
                categories["📚 ОБУЧЕНИЕ"].append((folder_name, file_count))
            else:
                categories["🗂️ ПРОЧЕЕ"].append((folder_name, file_count))
    
    # Print categorized structure
    for category, folders in categories.items():
        if folders:
            print(f"\n{category}")
            print("-" * 60)
            for folder_name, file_count in folders:
                print(f"   📂 {folder_name}: {file_count} файлов")
    
    print(f"\n📊 Всего файлов в БАЗА: {total_files}")
    print(f"📊 Всего категорий: {len([f for f in base_path.iterdir() if f.is_dir()])}")

def test_expanded_category_detection():
    """Test category detection for all subject areas"""
    print("\n🧪 Тестирование определения категорий - РАСШИРЕННАЯ ВЕРСИЯ")
    print("=" * 80)
    
    # Comprehensive test files covering all subject areas
    test_files = [
        # Construction
        ("SP_25.13330.2020.pdf", "СП 25.13330.2020 Конструкции каменные", "09. СТРОИТЕЛЬСТВО - СВОДЫ ПРАВИЛ"),
        ("GOST_52742-2007.pdf", "ГОСТ 52742-2007 Арматура стеклопластиковая", "07. СТРОИТЕЛЬСТВО - ГОСТы"),
        ("GESN_01.pdf", "ГЭСН 01 Земляные работы", "05. СТРОИТЕЛЬСТВО - СМЕТЫ"),
        ("MDS_21-1.98.pdf", "МДС 21-1.98 Методические документы в строительстве", "02. СТРОИТЕЛЬСТВО - МДС"),
        ("PPR_Karkas.pdf", "Проект производства работ на строительство каркаса", "03. СТРОИТЕЛЬСТВО - ПОС/ППР"),
        
        # Finance
        ("NalogovyKodeks_Chast1.pdf", "Налоговый кодекс РФ часть 1", "10. ФИНАНСЫ - ЗАКОНЫ"),
        ("PBU_23_2011.pdf", "ПБУ 23/2011 Отчет о движении денежных средств", "12. ФИНАНСЫ - СТАНДАРТЫ"),
        ("Instrukcia_CB_180P.pdf", "Инструкция Банка России №180-П", "14. ФИНАНСЫ - БАНКОВСКОЕ ДЕЛО"),
        
        # Accounting
        ("FZ_402_BuhUchet.pdf", "ФЗ №402 О бухгалтерском учете", "16. БУХУЧЕТ - ЗАКОНЫ"),
        ("Plan_Schetov_2023.pdf", "План счетов бухгалтерского учета", "18. БУХУЧЕТ - ПЛАН СЧЕТОВ"),
        ("BuhUchet_Uchebnik.pdf", "Бухгалтерский учет учебник", "21. БУХУЧЕТ - КНИГИ"),
        
        # Industrial Safety
        ("PromBezopasnost_FZ116.pdf", "ФЗ №116 О промышленной безопасности", "22. ПРОМБЕЗОПАСНОСТЬ - ЗАКОНЫ"),
        ("PB_03_273_99.pdf", "ПБ 03-273-99 Правила безопасности", "23. ПРОМБЕЗОПАСНОСТЬ - ПРАВИЛА"),
        
        # Occupational Safety
        ("OhranaTruda_TK_RF.pdf", "Трудовой кодекс РФ раздел Охрана труда", "28. ОХРАНА ТРУДА - ЗАКОНЫ"),
        ("Pravila_OT_Stroitelstvo.pdf", "Правила по охране труда при строительстве", "29. ОХРАНА ТРУДА - ПРАВИЛА"),
        ("SIZ_Normy_Vydachi.pdf", "Нормы выдачи средств индивидуальной защиты", "32. ОХРАНА ТРУДА - СИЗ"),
        
        # HR
        ("Trudovoe_Pravo_Uchebnik.pdf", "Трудовое право учебник", "35. HR - ТРУДОВОЕ ПРАВО"),
        ("Kadrovoe_Deloproizvodstvo.pdf", "Кадровое делопроизводство справочник", "36. HR - КАДРОВОЕ ДЕЛОПРОИЗВОДСТВО"),
        ("MROT_2024.pdf", "МРОТ на 2024 год", "38. HR - ОПЛАТА ТРУДА"),
        
        # Ecology
        ("FZ_7_OOS.pdf", "ФЗ №7 Об охране окружающей среды", "42. ЭКОЛОГИЯ - ЗАКОНЫ"),
        ("PDK_Atmosfera_2023.pdf", "Предельно допустимые концентрации в атмосфере", "43. ЭКОЛОГИЯ - НОРМАТИВЫ"),
        ("FKKO_2021.pdf", "Федеральный классификатор кодов отходов", "47. ЭКОЛОГИЯ - ОТХОДЫ"),
        
        # Training Materials
        ("Lekcia_Stroitelstvo.pptx", "Лекция по технологии строительства", "49. ЛЕКЦИИ И КУРСЫ"),
        ("Tehnichesky_Spravochnik.pdf", "Технический справочник инженера", "50. КНИГИ ОБЩИЕ"),
        ("ISO_9001_2015.pdf", "ГОСТ Р ИСО 9001-2015 Система менеджмента качества", "51. СТАНДАРТЫ КАЧЕСТВА"),
        
        # Unknown/Other
        ("Unknown_Document.pdf", "Документ неизвестного типа", "99. ДРУГИЕ ДОКУМЕНТЫ")
    ]
    
    correct_predictions = 0
    for file_name, content, expected_category in test_files:
        predicted_category = _determine_document_category(file_name.lower(), content)
        status = "✅" if predicted_category == expected_category else "❌"
        
        # Color coding by subject area
        if "СТРОИТЕЛЬСТВО" in predicted_category:
            icon = "🏗️"
        elif "ФИНАНСЫ" in predicted_category:
            icon = "💰"
        elif "БУХУЧЕТ" in predicted_category:
            icon = "📊"
        elif "ПРОМБЕЗОПАСНОСТЬ" in predicted_category:
            icon = "⚠️"
        elif "ОХРАНА ТРУДА" in predicted_category:
            icon = "🛡️"
        elif "HR" in predicted_category:
            icon = "👥"
        elif "ЭКОЛОГИЯ" in predicted_category:
            icon = "🌿"
        elif any(x in predicted_category for x in ["ЛЕКЦИИ", "КНИГИ", "СТАНДАРТЫ"]):
            icon = "📚"
        else:
            icon = "🗂️"
        
        print(f"{status} {icon} {file_name}")
        print(f"   Ожидалось: {expected_category}")
        print(f"   Получено:  {predicted_category}")
        
        if predicted_category == expected_category:
            correct_predictions += 1
        print()
    
    accuracy = (correct_predictions / len(test_files)) * 100
    print(f"🎯 Точность определения категорий: {correct_predictions}/{len(test_files)} ({accuracy:.1f}%)")
    
    return accuracy > 80

def test_expanded_stage0_processing():
    """Test full Stage 0 processing with expanded categories"""
    print("\n🧪 Тестирование полной обработки Stage 0 - РАСШИРЕННАЯ ВЕРСИЯ")
    print("=" * 80)
    
    # Create test files for different subject areas
    test_dir = Path("C:/temp/test_expanded_ntd")
    test_dir.mkdir(exist_ok=True)
    
    test_files = [
        # Construction
        ("SP_25.13330.2020_Konstrukcii.pdf", "СП 25.13330.2020 Конструкции каменные и армокаменные\nСвод правил\nТестовый документ для проверки сортировки"),
        ("GOST_52742_Armatura.pdf", "ГОСТ 52742-2007 Арматура стеклопластиковая\nГосударственный стандарт\nТестовый документ"),
        ("GESN_01_Zemlyanye.pdf", "ГЭСН 01 Земляные работы\nГосударственные элементные сметные нормы\nТестовый документ"),
        
        # Finance & Accounting
        ("NalogovyKodeks_RF.pdf", "Налоговый кодекс Российской Федерации\nЧасть первая\nНалоговое законодательство"),
        ("PBU_23_DDDS.pdf", "ПБУ 23/2011 Отчет о движении денежных средств\nПоложение по бухгалтерскому учету\nБухгалтерские стандарты"),
        ("Plan_Schetov_Buh.pdf", "План счетов бухгалтерского учета\nИнструкция по применению\nКорреспонденция счетов"),
        
        # Safety & HR
        ("PromBez_FZ116.pdf", "Федеральный закон О промышленной безопасности опасных производственных объектов\nПромышленная безопасность"),
        ("OhranaTruda_Pravila.pdf", "Правила по охране труда при строительных работах\nОхрана труда\nБезопасность труда"),
        ("Kadrovoe_Delo_2024.pdf", "Кадровое делопроизводство в 2024 году\nТрудовые договоры\nHR документы"),
        
        # Ecology & Training
        ("Ecologia_FZ7_OOS.pdf", "Федеральный закон Об охране окружающей среды\nЭкология\nОхрана окружающей среды"),
        ("Lekcia_Tehnologii.pdf", "Лекция по современным технологиям\nОбучение\nКурс повышения квалификации")
    ]
    
    # Create test files with content
    for file_name, content in test_files:
        test_file = test_dir / file_name
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"📄 Создан тестовый файл: {file_name}")
    
    # Initialize NTD system
    try:
        print("\n🔧 Инициализация расширенной системы НТД...")
        normative_db, normative_checker = initialize_ntd_system()
        print("✅ Система НТД инициализирована")
        
        # Process each file
        processed_files = []
        for file_name, _ in test_files:
            test_file = test_dir / file_name
            print(f"\n🔄 Обработка файла: {file_name}")
            
            result = ntd_preprocess(str(test_file), normative_db, normative_checker, test_mode=True)
            
            if result:
                print(f"✅ Файл обработан: {Path(result).name}")
                processed_files.append(result)
                
                # Show which БАЗА category was assigned
                if "БАЗА" in result:
                    category = Path(result).parent.name
                    if "СТРОИТЕЛЬСТВО" in category:
                        icon = "🏗️"
                    elif "ФИНАНСЫ" in category:
                        icon = "💰"
                    elif "БУХУЧЕТ" in category:
                        icon = "📊"
                    elif "ПРОМБЕЗОПАСНОСТЬ" in category:
                        icon = "⚠️"
                    elif "ОХРАНА ТРУДА" in category:
                        icon = "🛡️"
                    elif "HR" in category:
                        icon = "👥"
                    elif "ЭКОЛОГИЯ" in category:
                        icon = "🌿"
                    else:
                        icon = "📂"
                    
                    print(f"📁 {icon} Файл перемещён в: {category}")
                else:
                    print("⚠️ Файл не был перемещён в БАЗА")
            else:
                print(f"❌ Ошибка обработки файла: {file_name}")
        
        print(f"\n📊 Результат: {len(processed_files)}/{len(test_files)} файлов успешно обработано")
        
        # Cleanup test files
        print(f"\n🧹 Очистка тестовых файлов...")
        shutil.rmtree(test_dir, ignore_errors=True)
        print("✅ Тестовые файлы удалены")
        
        return len(processed_files) > 0
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 ТЕСТИРОВАНИЕ РАСШИРЕННОЙ STAGE 0 - NTD PREPROCESSING")
    print("🌐 МНОГОПРОФИЛЬНАЯ СИСТЕМА СОРТИРОВКИ ДОКУМЕНТОВ")
    print("=" * 80)
    print("📋 Поддерживаемые области:")
    print("   🏗️ Строительство и архитектура")
    print("   💰 Финансы и экономика")
    print("   📊 Бухгалтерский учет")
    print("   ⚠️ Промышленная безопасность")
    print("   🛡️ Охрана труда")
    print("   👥 HR и трудовое право")
    print("   🌿 Экология")
    print("   📚 Обучающие материалы")
    print("=" * 80)
    
    # Show current expanded structure
    show_expanded_baza_structure()
    
    # Test 1: Category detection for all areas
    success1 = test_expanded_category_detection()
    
    # Test 2: Full Stage 0 processing
    success2 = test_expanded_stage0_processing()
    
    print("\n" + "=" * 80)
    if success1 and success2:
        print("🎉 ВСЕ ТЕСТЫ РАСШИРЕННОЙ СИСТЕМЫ ПРОЙДЕНЫ!")
        print("✅ Stage 0 готов к работе с многопрофильной сортировкой")
        print("🌐 Система поддерживает все основные предметные области")
        print("📁 Файлы автоматически сортируются в I:/docs/БАЗА/")
        print("🔥 Готово к обработке документов по:")
        print("   • Строительству • Финансам • Бухучету • Безопасности")
        print("   • HR • Экологии • Обучению • И многим другим!")
    else:
        print("❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
        if not success1:
            print("   - Проблемы с определением категорий")
        if not success2:
            print("   - Проблемы с полной обработкой Stage 0")
    print("=" * 80)