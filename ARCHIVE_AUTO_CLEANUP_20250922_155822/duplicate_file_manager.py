#!/usr/bin/env python3
"""
Utility for managing duplicate files after merging.
This tool helps backup and delete duplicate files safely.
"""

import os
import shutil
import csv
from datetime import datetime
from pathlib import Path

def backup_file(file_path):
    """Create a backup of a file before deletion."""
    if not os.path.exists(file_path):
        return None
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{file_path}.backup_{timestamp}"
    shutil.copy2(file_path, backup_path)
    return backup_path

def delete_duplicate_files(primary_file, duplicate_files, backup=True):
    """Delete duplicate files after ensuring the primary exists."""
    if not os.path.exists(primary_file):
        print(f"❌ Primary file does not exist: {primary_file}")
        return []
    
    deleted_files = []
    failed_deletions = []
    
    print(f"\n🗑️  DELETING DUPLICATE FILES")
    print("=" * 50)
    print(f"Primary file: {primary_file}")
    print(f"Keeping: {os.path.basename(primary_file)}")
    
    for dup_file in duplicate_files:
        # Skip the primary file
        if dup_file == primary_file:
            continue
            
        # Check if duplicate file exists
        if not os.path.exists(dup_file):
            print(f"⚠️  File not found (already deleted?): {os.path.basename(dup_file)}")
            continue
        
        try:
            # Create backup if requested
            backup_path = None
            if backup:
                backup_path = backup_file(dup_file)
                if backup_path:
                    print(f"📦 Backed up: {os.path.basename(dup_file)} → {os.path.basename(backup_path)}")
                else:
                    print(f"⚠️  Failed to backup: {os.path.basename(dup_file)}")
            
            # Delete the duplicate file
            os.remove(dup_file)
            deleted_files.append({
                'file': dup_file,
                'backup': backup_path
            })
            print(f"✅ Deleted: {os.path.basename(dup_file)}")
            
        except Exception as e:
            failed_deletions.append({
                'file': dup_file,
                'error': str(e)
            })
            print(f"❌ Failed to delete {os.path.basename(dup_file)}: {e}")
    
    # Summary
    print(f"\n📊 DELETION SUMMARY")
    print("=" * 30)
    print(f"Successfully deleted: {len(deleted_files)}")
    print(f"Failed to delete:     {len(failed_deletions)}")
    
    if failed_deletions:
        print("\n❌ FAILED DELETIONS:")
        for item in failed_deletions:
            print(f"   {item['file']}: {item['error']}")
    
    return deleted_files, failed_deletions

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

def update_csv_after_deletion(csv_file, func_name, deleted_files):
    """Update the CSV tracker after deleting duplicate files."""
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return False
    
    # Read current data
    rows = []
    updated = False
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['FunctionName'] == func_name:
                # Update status and notes
                row['Status'] = 'Deleted'
                current_notes = row.get('Notes', '')
                deletion_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                new_notes = f"{current_notes}; Deleted duplicates on {deletion_time}" if current_notes else f"Deleted duplicates on {deletion_time}"
                row['Notes'] = new_notes
                updated = True
            rows.append(row)
    
    # Write updated data
    if updated:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        
        print(f"✅ Updated CSV status for {func_name} to 'Deleted'")
        return True
    else:
        print(f"⚠️  Function {func_name} not found in CSV")
        return False

def main():
    """Main duplicate file manager."""
    print("🗂️  Bldr Empire - Duplicate File Manager")
    print("=" * 50)
    print("This tool helps manage duplicate files after merging.")
    
    # Example usage - in practice, you would call this from another script
    # with actual file paths from your CSV
    """
    primary_file = r"C:\Bldr\primary_example.py"
    duplicate_files = [
        r"C:\Bldr\duplicate1_example.py",
        r"C:\Bldr\duplicate2_example.py"
    ]
    
    # Delete duplicate files
    deleted_files, failed_deletions = delete_duplicate_files(primary_file, duplicate_files)
    
    # Generate report
    report_file = generate_deletion_report(deleted_files, failed_deletions)
    
    # Update CSV
    update_csv_after_deletion("duplication_master_list_updated.csv", "example_function", deleted_files)
    """

if __name__ == "__main__":
    main()
