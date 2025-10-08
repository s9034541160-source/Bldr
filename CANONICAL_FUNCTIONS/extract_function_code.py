# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: extract_function_code
# Основной источник: C:\Bldr\full_automatic_duplicate_eliminator.py
# Дубликаты (для справки):
#   - C:\Bldr\compare_function_versions.py
#   - C:\Bldr\function_merger_helper.py
#   - C:\Bldr\merge_duplicates.py
#================================================================================
def extract_function_code(file_path, func_name):
    """Extract the complete source code of a function from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                lines = source.splitlines()
                start_line = node.lineno - 1
                end_line = getattr(node, 'end_lineno', len(lines))
                func_code = "\n".join(lines[start_line:end_line])
                return func_code, start_line, end_line
    except Exception as e:
        return f"# ERROR extracting function: {e}", 0, 0
    
    return f"# Function '{func_name}' not found in {file_path}", 0, 0