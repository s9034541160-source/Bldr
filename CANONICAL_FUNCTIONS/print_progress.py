# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: print_progress
# Основной источник: C:\Bldr\semi_automated_duplicate_eliminator.py
# Дубликаты (для справки):
#   - C:\Bldr\background_rag_training.py
#================================================================================
def print_progress(duplicates):
    """Print current progress."""
    total = len(duplicates)
    pending = sum(1 for d in duplicates if d['Status'] == 'Pending')
    reviewed = sum(1 for d in duplicates if d['Status'] == 'Reviewed')
    merged = sum(1 for d in duplicates if d['Status'] == 'Merged')
    deleted = sum(1 for d in duplicates if d['Status'] == 'Deleted')
    verified = sum(1 for d in duplicates if d['Status'] == 'Verified')
    
    print("\n📊 PROGRESS REPORT")
    print("=" * 40)
    print(f"Total functions:      {total:3d}")
    print(f"Pending:              {pending:3d} ({pending/total*100:5.1f}%)")
    print(f"Reviewed:             {reviewed:3d} ({reviewed/total*100:5.1f}%)")
    print(f"Merged:               {merged:3d} ({merged/total*100:5.1f}%)")
    print(f"Deleted:              {deleted:3d} ({deleted/total*100:5.1f}%)")
    print(f"Verified:             {verified:3d} ({verified/total*100:5.1f}%)")