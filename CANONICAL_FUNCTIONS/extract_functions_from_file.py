# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: extract_functions_from_file
# Основной источник: C:\Bldr\analyze_duplicates.py
# Дубликаты (для справки):
#   - C:\Bldr\find_duplicates.py
#================================================================================
def extract_functions_from_file(file_path):
    """
    Extract all function definitions from a Python file.
    
    Args:
        file_path (str): Path to the Python file
        
    Returns:
        list: List of function names defined in the file
    """
    functions = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Parse the Python code
        tree = ast.parse(content)
        
        # Extract function definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
                
    except Exception as e:
        # Silent fail for files that can't be parsed
        pass
        
    return functions