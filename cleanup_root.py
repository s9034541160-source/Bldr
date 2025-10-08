import os
import glob
import shutil

def cleanup_temporary_files():
    """Remove temporary, log, and backup files"""
    to_delete = []
    
    # Log files
    to_delete += glob.glob("*.log")
    
    # Backup files
    to_delete += glob.glob("*.bak")
    to_delete += glob.glob("*.dat")
    to_delete += glob.glob("*.dir")
    to_delete += glob.glob("*.lock")
    
    # Redis dump file
    to_delete += glob.glob("dump.rdb")
    
    # Celery beat schedule files
    to_delete += glob.glob("celerybeat-schedule.*")
    
    # Old reports
    to_delete += glob.glob("duplicate_report_*")
    to_delete += glob.glob("FINAL_*_REPORT.md")
    to_delete += glob.glob("PATCH_14_*")
    to_delete += glob.glob("IMPROVED_*_REPORT.md")
    to_delete += glob.glob("COMPLETE_*_GUIDE.md")
    to_delete += glob.glob("DUPLICATE_*_README.md")
    to_delete += glob.glob("DUPLICATE_*_SUMMARY.md")
    to_delete += glob.glob("RAG_*_ANALYSIS.md")
    to_delete += glob.glob("WEBSOCKET_*_REPORT.md")
    to_delete += glob.glob("TWO_*_ARCHITECTURE_DIAGRAM.md")
    to_delete += glob.glob("TOOL_*_STANDARDS.md")
    to_delete += glob.glob("PARSER_*_REPORT.md")
    to_delete += glob.glob("MODEL_*_SETUP.md")
    
    # Test files
    to_delete += glob.glob("test_*.json")
    to_delete += glob.glob("test_*.xlsx")
    to_delete += glob.glob("test_*.txt")
    
    # Large model files (should not be in git)
    to_delete += glob.glob("*.pt")
    to_delete += glob.glob("*.pkl")
    to_delete += glob.glob("*.gguf")
    to_delete += glob.glob("*.bin")
    
    # Delete files
    for f in to_delete:
        if os.path.isfile(f):
            print(f"Удаляю: {f}")
            os.remove(f)

def cleanup_duplicate_scripts():
    """Remove duplicate script files"""
    to_delete = []
    
    # Duplicate PowerShell scripts
    to_delete += glob.glob("start_bldr.ps1.backup")
    to_delete += glob.glob("start_bldr.ps1.txt")
    
    # Duplicate batch files
    to_delete += glob.glob("start_*.bat")
    to_delete += glob.glob("start_*.ps1")
    
    # Keep only the main ones
    keep_files = ["start_bldr.bat", "start_bldr.ps1"]
    to_delete = [f for f in to_delete if f not in keep_files]
    
    # Delete files
    for f in to_delete:
        if os.path.isfile(f):
            print(f"Удаляю: {f}")
            os.remove(f)

def cleanup_duplicate_python_files():
    """Remove duplicate Python files"""
    to_delete = []
    
    # Duplicate VLM processor files
    vlm_files = glob.glob("vlm_processor*.py")
    keep_vlm = ["vlm_processor.py"]
    to_delete += [f for f in vlm_files if f not in keep_vlm]
    
    # Duplicate migrate files
    migrate_files = glob.glob("migrate_*/*.py")
    keep_migrate = ["migrate_models_simple.py", "migrate_models_to_disk_i.py"]
    to_delete += [f for f in migrate_files if os.path.basename(f) not in keep_migrate]
    
    # Delete files
    for f in to_delete:
        if os.path.isfile(f):
            print(f"Удаляю: {f}")
            os.remove(f)

def organize_files():
    """Organize remaining files into proper directories"""
    # Create directories if they don't exist
    dirs_to_create = ["tests", "scripts", "docs", "configs"]
    for directory in dirs_to_create:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Создал директорию: {directory}")
    
    # Move test files
    test_files = glob.glob("test_*.py")
    for f in test_files:
        if os.path.isfile(f):
            destination = os.path.join("tests", f)
            if not os.path.exists(destination):
                shutil.move(f, destination)
                print(f"Переместил: {f} → tests/")
    
    # Move script files
    script_files = glob.glob("start_*.bat") + glob.glob("start_*.ps1")
    for f in script_files:
        if os.path.isfile(f):
            destination = os.path.join("scripts", f)
            if not os.path.exists(destination):
                shutil.move(f, destination)
                print(f"Переместил: {f} → scripts/")
    
    # Move documentation files
    doc_patterns = [
        "README_*.md", "*_GUIDE.md", "*_REPORT.md", 
        "FINAL_*_SUMMARY.md", "*_INTEGRATION_PLAN.md"
    ]
    for pattern in doc_patterns:
        doc_files = glob.glob(pattern)
        for f in doc_files:
            if os.path.isfile(f):
                destination = os.path.join("docs", f)
                if not os.path.exists(destination):
                    shutil.move(f, destination)
                    print(f"Переместил: {f} → docs/")

if __name__ == "__main__":
    print("Начинаю очистку репозитория...")
    
    # Cleanup temporary files
    cleanup_temporary_files()
    
    # Cleanup duplicate scripts
    cleanup_duplicate_scripts()
    
    # Cleanup duplicate Python files
    cleanup_duplicate_python_files()
    
    # Organize remaining files
    organize_files()
    
    print("Очистка завершена!")