# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: delete_duplicate_files
# Основной источник: C:\Bldr\full_automatic_duplicate_eliminator.py
# Дубликаты (для справки):
#   - C:\Bldr\duplicate_elimination_workflow.py
#   - C:\Bldr\duplicate_file_manager.py
#================================================================================
def delete_duplicate_files(func_name, primary_file, duplicate_files):
    """Delete duplicate files after merging."""
    deleted_files = []
    failed_deletions = []
    
    print(f"   🗑️  Deleting duplicate files for: {func_name}")
    
    for dup_file in duplicate_files:
        # Skip the primary file
        if dup_file == primary_file:
            continue
            
        # Check if file exists
        if not os.path.exists(dup_file):
            continue
        
        try:
            # Create backup
            backup_path = backup_file(dup_file)
            
            # Delete the duplicate
            os.remove(dup_file)
            deleted_files.append({
                'file': dup_file,
                'backup': backup_path
            })
            print(f"      ✅ Deleted: {os.path.basename(dup_file)}")
            
        except Exception as e:
            failed_deletions.append({
                'file': dup_file,
                'error': str(e)
            })
            print(f"      ❌ Failed to delete {os.path.basename(dup_file)}: {e}")
    
    return deleted_files, failed_deletions