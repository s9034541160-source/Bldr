import os
import glob
import shutil

def remove_archive_directories():
    """Remove archive directories that contain old files"""
    archive_dirs = [
        "ARCHIVE",
        "ARCHIVE_AUTO_CLEANUP_20250922_155822",
        "ARCHIVE_DEAD_CODE_20250922_161724",
        "ARCHIVE_OLD_VERSIONS",
        "BUILD_REPORT",
        "backup_rag_20250929_190822",
        "backup_rag_20250929_194808"
    ]
    
    for directory in archive_dirs:
        if os.path.exists(directory):
            print(f"Удаляю директорию: {directory}")
            shutil.rmtree(directory)

def remove_backup_files():
    """Remove backup and duplicate files"""
    # Backup files in core directory
    backup_files = [
        "core/bldr_api.py.backup",
        "core/bldr_api.py.backup2",
        "core/tools_system.py.bak"
    ]
    
    for f in backup_files:
        if os.path.exists(f):
            print(f"Удаляю: {f}")
            os.remove(f)
    
    # Backup files in tools/custom directory
    tool_backup_files = [
        "tools/custom/auto_budget_v2.py.backup",
        "tools/custom/auto_budget.py.backup",
        "tools/custom/auto_budget.py.old",
        "tools/custom/auto_budget.py.txt",
        "tools/custom/generate_letter_v2.py.backup",
        "tools/custom/generate_letter.py.backup",
        "tools/custom/generate_letter.py.txt",
        "tools/custom/search_rag_database.py.txt.backup"
    ]
    
    for f in tool_backup_files:
        if os.path.exists(f):
            print(f"Удаляю: {f}")
            os.remove(f)

def remove_old_canonical_functions():
    """Remove old canonical function files"""
    # Remove old canonical function files that are no longer needed
    old_canonical_files = [
        "CANONICAL_FUNCTIONS/_stage3_local_scan_and_copy.py",
        "CANONICAL_FUNCTIONS/backup_file.py"
    ]
    
    for f in old_canonical_files:
        if os.path.exists(f):
            print(f"Удаляю: {f}")
            os.remove(f)

def remove_unnecessary_scripts():
    """Remove unnecessary script files"""
    unnecessary_scripts = [
        "cleanup_old_cache.py",
        "cleanup_remaining_cache.py",
        "cleanup_duplicate_tools.md"
    ]
    
    for f in unnecessary_scripts:
        if os.path.exists(f):
            print(f"Удаляю: {f}")
            if os.path.isfile(f):
                os.remove(f)
            elif os.path.isdir(f):
                shutil.rmtree(f)

def remove_large_unnecessary_files():
    """Remove large files that shouldn't be in git"""
    large_files = [
        "bldr_structure.txt"  # This is a very large file
    ]
    
    for f in large_files:
        if os.path.exists(f):
            print(f"Удаляю: {f}")
            os.remove(f)

def clean_node_modules():
    """Clean up unnecessary node_modules directories"""
    # Remove the entire web/bldr_dashboard/node_modules directory as it's not needed in git
    node_modules_dir = "web/bldr_dashboard/node_modules"
    if os.path.exists(node_modules_dir):
        print(f"Удаляю директорию: {node_modules_dir}")
        shutil.rmtree(node_modules_dir)

if __name__ == "__main__":
    print("Начинаю комплексную очистку репозитория...")
    
    # Remove archive directories
    remove_archive_directories()
    
    # Remove backup files
    remove_backup_files()
    
    # Remove old canonical functions
    remove_old_canonical_functions()
    
    # Remove unnecessary scripts
    remove_unnecessary_scripts()
    
    # Remove large unnecessary files
    remove_large_unnecessary_files()
    
    # Clean node_modules
    clean_node_modules()
    
    print("Комплексная очистка завершена!")