# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: load_duplicate_tracker
# Основной источник: C:\Bldr\full_automatic_duplicate_eliminator.py
# Дубликаты (для справки):
#   - C:\Bldr\batch_duplicate_processor.py
#   - C:\Bldr\duplicate_elimination_workflow.py
#   - C:\Bldr\semi_automated_duplicate_eliminator.py
#================================================================================
def load_duplicate_tracker(csv_file):
    """Load the duplicate tracker CSV file."""
    duplicates = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert FileList back to a list
            file_list = row['FileList'].split(';') if row['FileList'] else []
            row['FileList'] = file_list
            duplicates.append(row)
    return duplicates