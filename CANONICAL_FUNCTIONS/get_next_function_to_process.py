# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: get_next_function_to_process
# Основной источник: C:\Bldr\semi_automated_duplicate_eliminator.py
# Дубликаты (для справки):
#   - C:\Bldr\duplicate_elimination_workflow.py
#================================================================================
def get_next_function_to_process(duplicates):
    """Get the next function that needs to be processed (status = Pending)."""
    # Sort by file count (descending) to process high-priority functions first
    pending = [d for d in duplicates if d['Status'] == 'Pending']
    pending.sort(key=lambda x: int(x['FileCount']), reverse=True)
    return pending[0] if pending else None