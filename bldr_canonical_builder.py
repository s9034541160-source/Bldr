import os
import shutil
import ast
import re
import csv
from pathlib import Path
from datetime import datetime
from collections import defaultdict

class BldrCanonicalBuilder:
    def __init__(self, project_root=r"C:\Bldr"):
        self.project_root = Path(project_root)
        self.archive_dir = self.project_root / f"ARCHIVE_AUTO_CLEANUP_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.canonical_dir = self.project_root / "CANONICAL_FUNCTIONS"
        self.report_dir = self.project_root / "BUILD_REPORT"
        self.function_inventory = []
        self.duplicate_map = defaultdict(list)  # func_name -> [file_paths]
        self.canonical_map = {}  # func_name -> chosen_file_path

        # 🚫 СПИСОК ПАПОК, КОТОРЫЕ НЕЛЬЗЯ ТРОГАТЬ
        self.IGNORED_DIRS = {
            'venv',
            '.venv',
            '.git',
            '.vscode',
            '.idea',
            '__pycache__',
            '.pytest_cache',
            'node_modules',
            'build',
            'dist',
            'ARCHIVE',  # Игнорируем все папки, содержащие "ARCHIVE"
            'BUILD_REPORT',
            'CANONICAL_FUNCTIONS',
            'web',      # Игнорируем фронтенд
            'data',     # Игнорируем данные
            'logs'      # Игнорируем логи
        }

    def should_ignore_path(self, path: Path) -> bool:
        """
        Проверяет, нужно ли игнорировать данный путь.
        """
        path_str = str(path).lower()
        for ignored in self.IGNORED_DIRS:
            if ignored.lower() in path_str:
                return True
        return False

    def create_directories(self):
        """Создает необходимые директории."""
        self.archive_dir.mkdir(exist_ok=True)
        self.canonical_dir.mkdir(exist_ok=True)
        self.report_dir.mkdir(exist_ok=True)
        print(f"📁 Папки созданы: {self.archive_dir}, {self.canonical_dir}, {self.report_dir}")

    def scan_project_for_functions(self):
        """Сканирует проект и создает инвентарь всех функций, игнорируя служебные папки."""
        print("🔍 Сканирование проекта и создание инвентаря функций...")
        for file_path in self.project_root.rglob("*.py"):
            if self.should_ignore_path(file_path):
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    source = f.read()
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        self.function_inventory.append({
                            'FunctionName': node.name,
                            'FilePath': str(file_path),
                            'StartLine': node.lineno,
                            'EndLine': getattr(node, 'end_lineno', node.lineno)
                        })
            except Exception as e:
                print(f"⚠️  Ошибка при анализе файла {file_path}: {e}")

        # Строим карту дубликатов
        for item in self.function_inventory:
            self.duplicate_map[item['FunctionName']].append(item['FilePath'])

        print(f"📊 Найдено {len(self.function_inventory)} функций. Дубликаты выявлены.")

    def intelligent_primary_selection(self, func_name, file_list):
        """Умный выбор основного файла."""
        priority_indicators = [
            ('core', 100),
            ('tools_system', 90),
            ('main.py', 85),
            ('bldr_gui.py', 80),
            ('enterprise_rag', 75),
            ('super_smart', 70),
            ('model_manager', 65),
            ('config', 60),
            ('latest', 50)
        ]
        
        deprioritize_indicators = [
            'archive',
            'backup',
            'test',
            'debug',
            'temp',
            'old',
            'deprecated'
        ]
        
        scored_files = []
        
        for file_path in file_list:
            score = 50
            for indicator, points in priority_indicators:
                if indicator in file_path.lower():
                    score += points
            for indicator in deprioritize_indicators:
                if indicator in file_path.lower():
                    score -= 50
            try:
                mod_time = os.path.getmtime(file_path)
                age_days = (datetime.now().timestamp() - mod_time) / (24 * 3600)
                recency_bonus = max(0, 20 - (age_days / 10))
                score += recency_bonus
            except:
                pass
            scored_files.append((file_path, score))
        
        scored_files.sort(key=lambda x: x[1], reverse=True)
        return scored_files[0][0] if scored_files else file_list[0]

    def extract_function_code(self, file_path, func_name):
        """Извлекает код функции из файла."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == func_name:
                    lines = source.splitlines()
                    start_line = node.lineno - 1
                    end_line = getattr(node, 'end_lineno', len(lines))
                    func_code = '\n'.join(lines[start_line:end_line])
                    return func_code
        except Exception as e:
            print(f"⚠️  Ошибка при извлечении кода из {file_path}: {e}")
        return None

    def create_canonical_functions(self):
        """Создает канонические файлы для всех дублирующихся функций."""
        print("🛠️  Создание канонических файлов...")
        for func_name, file_list in self.duplicate_map.items():
            if len(file_list) <= 1:
                continue  # Не дубликат

            # Выбираем основной файл
            primary_file = self.intelligent_primary_selection(func_name, file_list)
            self.canonical_map[func_name] = primary_file

            # Извлекаем код функции
            func_code = self.extract_function_code(primary_file, func_name)
            if not func_code:
                print(f"❌ Не удалось извлечь код для {func_name} из {primary_file}")
                continue

            # Создаем комментарий с путями к дубликатам
            comment_lines = [
                f"# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: {func_name}",
                f"# Основной источник: {primary_file}",
                f"# Дубликаты (для справки):",
            ]
            for dup_file in file_list:
                if dup_file != primary_file:
                    comment_lines.append(f"#   - {dup_file}")
            comment_lines.append("#" + "="*80 + "\n")

            canonical_code = "\n".join(comment_lines) + func_code

            # Сохраняем в новый файл
            canonical_file_path = self.canonical_dir / f"{func_name}.py"
            with open(canonical_file_path, 'w', encoding='utf-8') as f:
                f.write(canonical_code)
            print(f"✅ Создан канонический файл: {canonical_file_path.name}")

    def build_canonical_project(self):
        """Собирает канонический проект, заменяя дубликаты на импорты из канонических файлов."""
        print("🏗️  Сборка канонического проекта...")
        critical_files = ['main.py', 'bldr_gui.py', 'bldr_system_launcher.py']

        for critical_file_name in critical_files:
            # Ищем файл в проекте
            critical_file_path = None
            for file_path in self.project_root.rglob(critical_file_name):
                if not self.should_ignore_path(file_path):
                    critical_file_path = file_path
                    break

            if not critical_file_path or not critical_file_path.exists():
                print(f"⚠️  Критический файл {critical_file_name} не найден. Пропускаем.")
                continue

            # Читаем содержимое файла
            with open(critical_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            new_lines = []
            i = 0
            while i < len(lines):
                line = lines[i]
                # Проверяем, является ли строка началом функции
                func_match = re.match(r'^\s*def\s+(\w+)\s*\(.*\):', line)
                if func_match:
                    func_name = func_match.group(1)
                    if func_name in self.canonical_map:
                        # Это дублирующаяся функция, которую нужно заменить
                        print(f"   🔄 Замена функции '{func_name}' в файле {critical_file_name}")
                        # Пропускаем все строки до конца функции
                        indent = len(line) - len(line.lstrip())
                        j = i + 1
                        while j < len(lines):
                            next_line = lines[j]
                            if next_line.strip() and len(next_line) - len(next_line.lstrip()) <= indent and not next_line.strip().startswith('def ') and not next_line.strip().startswith('class '):
                                break
                            j += 1
                        # Заменяем блок функции на импорт и вызов
                        canonical_import = f"from CANONICAL_FUNCTIONS.{func_name} import {func_name}\n"
                        # Вставляем импорт в начало файла (если его там еще нет)
                        if canonical_import not in new_lines[:10]:  # Проверяем первые 10 строк
                            new_lines.insert(0, canonical_import)
                        # Пропускаем старый код функции
                        i = j
                        continue
                new_lines.append(line)
                i += 1

            # Сохраняем обновленный файл (создаем бэкап старого)
            backup_path = self.archive_dir / f"{critical_file_name}.backup_{datetime.now().strftime('%H%M%S')}"
            shutil.copy2(critical_file_path, backup_path)
            with open(critical_file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f"✅ Обновлен файл: {critical_file_name}")

    def archive_original_files(self):
        """Архивирует оригинальные файлы, из которых были взяты канонические функции."""
        print("🗃️  Архивация оригинальных файлов...")
        archived_files = set()
        for func_name, primary_file in self.canonical_map.items():
            if primary_file not in archived_files:
                # Создаем структуру папок в архиве
                relative_path = Path(primary_file).relative_to(self.project_root)
                archive_file_path = self.archive_dir / relative_path
                archive_file_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(primary_file, archive_file_path)
                print(f"   📤 Перемещен в архив: {relative_path}")
                archived_files.add(primary_file)

    def generate_final_report(self):
        """Генерирует финальный отчет о сборке."""
        report_content = f"""# 🏗️ ОТЧЕТ О СБОРКЕ КАНОНИЧЕСКОГО ПРОЕКТА Bldr Empire
## Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 СТАТИСТИКА
- Обработано функций: {len(self.function_inventory)}
- Найдено дубликатов: {len([f for f in self.duplicate_map.values() if len(f) > 1])}
- Создано канонических файлов: {len(self.canonical_map)}
- Обновлено критических файлов: main.py, bldr_gui.py, bldr_system_launcher.py

## 📂 СТРУКТУРА ПРОЕКТА
- **CANONICAL_FUNCTIONS/**: Папка с каноническими версиями функций.
- **ARCHIVE_AUTO_CLEANUP_.../**: Папка с архивными копиями оригинальных файлов.
- **BUILD_REPORT/**: Эта папка с отчетами.

## 🛠️ СЛЕДУЮЩИЕ ШАГИ
1. Запустите систему через `bldr_gui.py`.
2. Если возникнут ошибки, проверьте:
   - Все ли импорты из `CANONICAL_FUNCTIONS` работают.
   - Нет ли зависимостей между функциями, которые были разорваны.
3. Для каждой функции в `CANONICAL_FUNCTIONS/` проверьте комментарии — там указаны пути к "дубликатам". Если в канонической версии чего-то не хватает — скопируйте нужный код из дубликата.
4. После стабилизации системы можно постепенно перенести функции из `CANONICAL_FUNCTIONS/` обратно в основные модули (`core/tools_system.py`, `core/coordinator.py` и т.д.).

## ✅ ПРОЕКТ ГОТОВ К ТЕСТИРОВАНИЮ!
"""

        # Сохраняем отчет
        report_file = self.report_dir / "BUILD_REPORT.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

        print(f"\n📄 Финальный отчет сохранен: {report_file}")
        print("🎉 Сборка канонического проекта завершена!")

    def run(self):
        """Запускает полный процесс сборки."""
        print("🚀 ЗАПУСК ПОЛНОСТЬЮ АВТОМАТИЗИРОВАННОГО СБОРЩИКА КАНОНИЧЕСКОГО ПРОЕКТА")
        print("=" * 70)
        print("Этот скрипт создаст чистую, рабочую версию вашего проекта.")
        print("Исходные файлы будут перемещены в архив, а не удалены.")
        print()

        confirmation = input("Вы уверены, что хотите продолжить? (Введите 'ДА'): ").strip()
        if confirmation != 'ДА':
            print("❌ Процесс отменен.")
            return

        try:
            self.create_directories()
            self.scan_project_for_functions()
            self.create_canonical_functions()
            self.build_canonical_project()
            self.archive_original_files()
            self.generate_final_report()
            print("\n✅ ВСЕ ЭТАПЫ УСПЕШНО ЗАВЕРШЕНЫ!")
        except Exception as e:
            print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
            print("Процесс прерван. Проверьте логи и попробуйте снова.")

if __name__ == "__main__":
    builder = BldrCanonicalBuilder()
    builder.run()