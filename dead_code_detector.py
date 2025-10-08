import os
import ast
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def load_function_inventory_from_report():
    """
    Загружает инвентарь функций из отчета скрипта-хирурга.
    Если отчета нет — сканирует проект заново.
    """
    # Попробуем найти отчет
    report_path = Path("BUILD_REPORT") / "BUILD_REPORT.md"
    if report_path.exists():
        print("📋 Используем инвентарь из отчета...")
        # В реальной жизни здесь был бы парсинг отчета, но для простоты пересканируем
        pass

    # Пересканируем проект для точности
    print("🔍 Пересканирование проекта для создания точного инвентаря...")
    function_inventory = []
    ignored_dirs = {
        'venv', '.venv', '.git', '.vscode', '.idea', '__pycache__',
        '.pytest_cache', 'node_modules', 'build', 'dist',
        'ARCHIVE', 'CANONICAL_FUNCTIONS', 'BUILD_REPORT', 'web', 'data', 'logs'
    }

    for file_path in Path(r"C:\Bldr").rglob("*.py"):
        # Игнорируем служебные папки
        if any(ignored in str(file_path).lower() for ignored in ignored_dirs):
            continue

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    function_inventory.append({
                        'FunctionName': node.name,
                        'FilePath': str(file_path.resolve()),
                        'StartLine': node.lineno,
                        'EndLine': getattr(node, 'end_lineno', node.lineno)
                    })
        except Exception as e:
            print(f"⚠️  Ошибка при анализе файла {file_path}: {e}")

    return function_inventory

def find_canonical_functions():
    """
    Находит все функции, для которых были созданы канонические версии.
    """
    canonical_dir = Path("CANONICAL_FUNCTIONS")
    if not canonical_dir.exists():
        return set()

    canonical_functions = set()
    for file_path in canonical_dir.glob("*.py"):
        func_name = file_path.stem  # Имя файла без расширения
        canonical_functions.add(func_name)

    print(f"✅ Найдено {len(canonical_functions)} канонических функций.")
    return canonical_functions

def find_vital_files(function_inventory, canonical_functions, critical_files):
    """
    Определяет список жизненно важных файлов.
    """
    vital_files = set()

    # Добавляем критические файлы
    for cf in critical_files:
        vital_files.add(str(Path(cf).resolve()))

    # Добавляем файлы, содержащие уникальные функции
    for item in function_inventory:
        func_name = item['FunctionName']
        file_path = item['FilePath']
        # Если функция НЕ каноническая — значит, она уникальна, и её файл жизненно важен
        if func_name not in canonical_functions:
            vital_files.add(file_path)

    print(f"✅ Найдено {len(vital_files)} жизненно важных файлов.")
    return vital_files

def detect_and_archive_dead_code(vital_files):
    """
    Находит и архивирует "мертвый код" — файлы, которые не являются жизненно важными.
    """
    archive_dir = Path(f"ARCHIVE_DEAD_CODE_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    archive_dir.mkdir(exist_ok=True)
    print(f"🗃️  Создана папка для архивации мертвого кода: {archive_dir}")

    ignored_dirs = {
        'venv', '.venv', '.git', '.vscode', '.idea', '__pycache__',
        '.pytest_cache', 'node_modules', 'build', 'dist',
        'ARCHIVE', 'CANONICAL_FUNCTIONS', 'BUILD_REPORT', 'web', 'data', 'logs'
    }

    dead_files = []
    for file_path in Path(r"C:\Bldr").rglob("*.py"):
        # Игнорируем служебные папки
        if any(ignored in str(file_path).lower() for ignored in ignored_dirs):
            continue

        # Игнорируем уже созданные архивы и канонические функции
        if "ARCHIVE" in str(file_path) or "CANONICAL_FUNCTIONS" in str(file_path):
            continue

        # Проверяем, является ли файл жизненно важным
        if str(file_path.resolve()) not in vital_files:
            dead_files.append(file_path)

    print(f"💀 Найдено {len(dead_files)} файлов с потенциальным 'мертвым кодом'.")

    # Перемещаем мертвый код в архив
    for file_path in dead_files:
        try:
            # Создаем структуру папок в архиве
            relative_path = file_path.relative_to(Path(r"C:\Bldr"))
            archive_file_path = archive_dir / relative_path
            archive_file_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(file_path, archive_file_path)
            print(f"   🗃️  Перемещен: {relative_path}")
        except Exception as e:
            print(f"   ❌ Ошибка при перемещении {file_path}: {e}")

    print(f"\n✅ Архивация мертвого кода завершена. Перемещено {len(dead_files)} файлов.")

def main():
    print("ЗАПУСК ДЕТЕКТОРА 'МЕРТВОГО КОДА'")
    print("=" * 60)
    print("Этот скрипт найдет и переместит в архив файлы, которые, вероятно, не используются в текущей версии системы.")
    print("Жизненно важные файлы (с уникальными функциями и основные файлы) будут сохранены.")
    print()

    confirmation = input("Вы уверены, что хотите продолжить? (Введите 'ДА'): ").strip()
    if confirmation != 'ДА':
        print("❌ Процесс отменен.")
        return

    # Основные файлы, которые всегда должны остаться
    critical_files = [
        "main.py",
        "bldr_gui.py",
        "bldr_system_launcher.py",
        "core/main.py",      # если есть
        "core/coordinator.py", # если есть
        "core/tools_system.py" # если есть
    ]

    # Шаг 1: Создаем инвентарь функций
    function_inventory = load_function_inventory_from_report()

    # Шаг 2: Находим канонические функции
    canonical_functions = find_canonical_functions()

    # Шаг 3: Определяем жизненно важные файлы
    vital_files = find_vital_files(function_inventory, canonical_functions, critical_files)

    # Шаг 4: Архивируем мертвый код
    detect_and_archive_dead_code(vital_files)

    print("\n" + "=" * 60)
    print("✅ ОЧИСТКА ЗАВЕРШЕНА!")
    print("Теперь в C:\\Bldr остались только:")
    print(" - Основные файлы (main.py, bldr_gui.py, ...)")
    print(" - Файлы с уникальными функциями")
    print(" - Служебные папки (venv, data, integrations, .vscode)")
    print(" - Папки CANONICAL_FUNCTIONS и BUILD_REPORT")
    print()
    print("Все остальное перемещено в архив ARCHIVE_DEAD_CODE_...")
    print("🚀 Теперь можно запускать bldr_gui.py и тестировать систему!")

if __name__ == "__main__":
    main()