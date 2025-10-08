# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: mark_function_as_processed
# Основной источник: C:\Bldr\semi_automated_duplicate_eliminator.py
# Дубликаты (для справки):
#   - C:\Bldr\duplicate_elimination_workflow.py
#================================================================================
def mark_function_as_processed(duplicates, func_name, status, notes=""):
    """Mark a function as processed in the duplicates list."""
    for dup in duplicates:
        if dup['FunctionName'] == func_name:
            dup['Status'] = status
            if notes:
                dup['Notes'] = notes
            return True
    return False