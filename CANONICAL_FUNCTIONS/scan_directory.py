# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: scan_directory
# Основной источник: C:\Bldr\analyze_duplicates.py
# Дубликаты (для справки):
#   - C:\Bldr\find_duplicates.py
#================================================================================
def scan_directory(root_dir):
    """
    Scan directory and subdirectories for Python files and extract functions.
    
    Args:
        root_dir (str): Root directory to scan
        
    Returns:
        dict: Dictionary mapping file paths to lists of function names
    """
    file_functions = {}
    
    # Folders to exclude
    exclude_folders = {'venv', 'archive', '.git'}
    
    for root, dirs, files in os.walk(root_dir):
        # Remove excluded directories from dirs so os.walk doesn't traverse them
        dirs[:] = [d for d in dirs if d not in exclude_folders]
        
        # Check if current directory should be skipped
        should_skip = False
        for exclude in exclude_folders:
            if exclude in root.split(os.sep):
                should_skip = True
                break
                
        if should_skip:
            continue
            
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                functions = extract_functions_from_file(file_path)
                file_functions[file_path] = functions
                
    return file_functions