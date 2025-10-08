import os
import ast
import re
from pathlib import Path

def find_function_references(root_dir, func_name):
    """Ищет все вызовы и импорты функции по имени в проекте."""
    references = []
    exclude_dirs = {'.git', 'venv', '__pycache__', 'archive'}
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip excluded directories
        dirnames[:] = [d for d in dirnames if d.lower() not in exclude_dirs]
        
        # Check if we're in an excluded directory
        if any(excluded in dirpath.lower() for excluded in exclude_dirs):
            continue
            
        for filename in filenames:
            if filename.endswith('.py'):
                file_path = os.path.join(dirpath, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        source = f.read()

                    # Простой поиск по тексту (для вызовов func_name(...))
                    # Use word boundary to avoid partial matches
                    if re.search(rf'\b{func_name}\s*\(', source):
                        references.append(f"Вызов в: {file_path}")

                    # Парсим AST для поиска импортов
                    tree = ast.parse(source)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ImportFrom):
                            for alias in node.names:
                                if alias.name == func_name:
                                    references.append(f"Импорт из: {file_path} (from {node.module} import {func_name})")
                        elif isinstance(node, ast.Import):
                            for alias in node.names:
                                if alias.name == func_name or (alias.asname and alias.asname == func_name):
                                    references.append(f"Импорт: {file_path} (import {alias.name})")
                        # Also check for attribute access (obj.func_name)
                        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                            if node.func.attr == func_name:
                                references.append(f"Вызов метода: {file_path}")
                except Exception as e:
                    # Silently skip files that can't be parsed
                    pass
    return references

if __name__ == "__main__":
    project_root = r"C:\Bldr"
    function_to_check = "initialize_system"  # Замени на имя функции, которую ты только что "очистил"

    refs = find_function_references(project_root, function_to_check)
    if refs:
        print(f"\n🔍 Найдены ссылки на '{function_to_check}':")
        for ref in refs:
            print(f"  {ref}")
    else:
        print(f"✅ Ссылки на '{function_to_check}' не найдены.")