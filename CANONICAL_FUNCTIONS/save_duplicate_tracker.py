# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: save_duplicate_tracker
# Основной источник: C:\Bldr\full_automatic_duplicate_eliminator.py
# Дубликаты (для справки):
#   - C:\Bldr\batch_duplicate_processor.py
#   - C:\Bldr\duplicate_elimination_workflow.py
#   - C:\Bldr\semi_automated_duplicate_eliminator.py
#================================================================================
def save_duplicate_tracker(csv_file, duplicates):
    """Save the duplicate tracker CSV file."""
    fieldnames = ['FunctionName', 'FileCount', 'FileList', 'ChosenPrimaryFile', 'Status', 'Notes']
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in duplicates:
            # Convert FileList back to semicolon-separated string
            row['FileList'] = ';'.join(row['FileList']) if isinstance(row['FileList'], list) else row['FileList']
            writer.writerow(row)