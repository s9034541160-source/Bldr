import ast
import difflib
from pathlib import Path

def extract_function_code(file_path, func_name):
    """Извлекает исходный код функции из файла."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                # Извлекаем строки кода функции
                lines = source.splitlines()
                start_line = node.lineno - 1
                # Try to get end line number, fallback if not available
                end_line = getattr(node, 'end_lineno', node.lineno + 20)
                func_code = "\n".join(lines[start_line:end_line])
                return func_code
    except Exception as e:
        return f"# ERROR extracting function: {e}"
    return f"# Function '{func_name}' not found in {file_path}"

def compare_versions(primary_file, duplicate_files, func_name):
    print(f"\n" + "="*80)
    print(f"🔍 Сравнение версий функции: {func_name}")
    print(f"✅ Основная версия: {primary_file}")
    print("="*80)

    primary_code = extract_function_code(primary_file, func_name)

    for dup_file in duplicate_files:
        if dup_file == primary_file:
            continue
        dup_code = extract_function_code(dup_file, func_name)
        print(f"\n--- Сравнение с: {dup_file} ---")
        # Создаем объект для сравнения
        differ = difflib.Differ()
        diff = list(differ.compare(primary_code.splitlines(), dup_code.splitlines()))
        # Выводим только различия
        has_diff = False
        for line in diff:
            if line.startswith('+ ') or line.startswith('- ') or line.startswith('? '):
                has_diff = True
                print(line)

        if not has_diff:
            print("  Нет различий.")
        else:
            print("  (Строки, начинающиеся с '+' — есть в дубле, но нет в основном. '-' — наоборот)")

# Пример использования (вставь свои данные из CSV)
if __name__ == "__main__":
    # Пример для функции 'main'
    func_to_compare = "main"
    primary_version = r"C:\Bldr\bldr_gui.py"  # Из столбца ChosenPrimaryFile
    duplicates = [
        r"C:\Bldr\bldr_gui_manager.py",
        r"C:\Bldr\core\test_main.py",
        # ... добавь все остальные из FileList
    ]

    compare_versions(primary_version, duplicates, func_to_compare)

    # Повтори для других функций...