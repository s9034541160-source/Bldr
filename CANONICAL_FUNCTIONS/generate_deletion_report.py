# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: generate_deletion_report
# Основной источник: C:\Bldr\duplicate_file_manager.py
# Дубликаты (для справки):
#   - C:\Bldr\duplicate_elimination_workflow.py
#================================================================================
def generate_deletion_report(deleted_files, failed_deletions, report_file=None):
    """Generate a report of file deletions."""
    if not report_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"duplicate_deletion_report_{timestamp}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# DUPLICATE FILE DELETION REPORT\n")
        f.write("=" * 50 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        if not deleted_files and not failed_deletions:
            f.write("No files were processed.\n")
            return report_file
        
        if deleted_files:
            f.write(f"## ✅ SUCCESSFULLY DELETED ({len(deleted_files)} files)\n\n")
            for item in deleted_files:
                f.write(f"- **Deleted**: {item['file']}\n")
                if item['backup']:
                    f.write(f"  - 📦 Backup: {item['backup']}\n")
                f.write("\n")
        
        if failed_deletions:
            f.write(f"## ❌ FAILED DELETIONS ({len(failed_deletions)} files)\n\n")
            for item in failed_deletions:
                f.write(f"- **Failed**: {item['file']}\n")
                f.write(f"  - ❌ Error: {item['error']}\n\n")
    
    print(f"📄 Deletion report saved to: {report_file}")
    return report_file