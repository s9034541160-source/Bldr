# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: backup_file
# Основной источник: C:\Bldr\full_automatic_duplicate_eliminator.py
# Дубликаты (для справки):
#   - C:\Bldr\duplicate_elimination_workflow.py
#   - C:\Bldr\duplicate_file_manager.py
#   - C:\Bldr\merge_duplicates.py
#   - C:\Bldr\semi_automated_duplicate_eliminator.py
#================================================================================
def backup_file(file_path):
    """Create a backup of a file before modifying it."""
    if not os.path.exists(file_path):
        return None
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{file_path}.auto_backup_{timestamp}"
    shutil.copy2(file_path, backup_path)
    return backup_path