#!/usr/bin/env python3
"""
Comprehensive workflow for eliminating duplicates in the Bldr project.
This script orchestrates the entire process from analysis to cleanup.
"""

import csv
import os
import shutil
from datetime import datetime
from pathlib import Path

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

def get_next_function_to_process(duplicates):
    """Get the next function that needs to be processed (status = Pending)."""
    for dup in duplicates:
        if dup['Status'] == 'Pending':
            return dup
    return None

def mark_function_as_processed(duplicates, func_name, status, notes=""):
    """Mark a function as processed in the duplicates list."""
    for dup in duplicates:
        if dup['FunctionName'] == func_name:
            dup['Status'] = status
            if notes:
                dup['Notes'] = notes
            return True
    return False

def backup_file(file_path):
    """Create a backup of a file before modifying it."""
    if not os.path.exists(file_path):
        return None
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{file_path}.backup_{timestamp}"
    shutil.copy2(file_path, backup_path)
    return backup_path

def delete_duplicate_files(primary_file, duplicate_files):
    """Delete duplicate files, keeping only the primary implementation."""
    deleted_files = []
    
    for dup_file in duplicate_files:
        # Don't delete the primary file
        if dup_file == primary_file:
            continue
            
        # Don't delete files that don't exist
        if not os.path.exists(dup_file):
            continue
            
        try:
            # Create a backup before deletion
            backup_path = f"{dup_file}.deleted_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(dup_file, backup_path)
            
            # Delete the duplicate file
            os.remove(dup_file)
            deleted_files.append({
                'file': dup_file,
                'backup': backup_path
            })
            print(f"🗑️  Deleted duplicate: {dup_file}")
            print(f"   Backup saved to: {backup_path}")
        except Exception as e:
            print(f"❌ Error deleting {dup_file}: {e}")
    
    return deleted_files

def generate_deletion_report(deleted_files, report_file):
    """Generate a report of deleted files."""
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("DUPLICATE FILE DELETION REPORT\n")
        f.write("=" * 50 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        if not deleted_files:
            f.write("No files were deleted.\n")
            return
            
        f.write(f"Deleted {len(deleted_files)} duplicate files:\n\n")
        
        for item in deleted_files:
            f.write(f"❌ {item['file']}\n")
            f.write(f"   📦 Backup: {item['backup']}\n\n")
    
    print(f"📄 Deletion report saved to: {report_file}")

def print_workflow_status(duplicates):
    """Print the current status of the duplicate elimination workflow."""
    total = len(duplicates)
    pending = sum(1 for d in duplicates if d['Status'] == 'Pending')
    reviewed = sum(1 for d in duplicates if d['Status'] == 'Reviewed')
    merged = sum(1 for d in duplicates if d['Status'] == 'Merged')
    deleted = sum(1 for d in duplicates if d['Status'] == 'Deleted')
    verified = sum(1 for d in duplicates if d['Status'] == 'Verified')
    
    print("\n📊 DUPLICATE ELIMINATION WORKFLOW STATUS")
    print("=" * 50)
    print(f"Total functions with duplicates: {total}")
    print(f"Pending analysis:     {pending:3d} ({pending/total*100:5.1f}%)")
    print(f"Reviewed:             {reviewed:3d} ({reviewed/total*100:5.1f}%)")
    print(f"Merged:               {merged:3d} ({merged/total*100:5.1f}%)")
    print(f"Deleted duplicates:   {deleted:3d} ({deleted/total*100:5.1f}%)")
    print(f"Verified:             {verified:3d} ({verified/total*100:5.1f}%)")
    print("=" * 50)

def main():
    """Main workflow for duplicate elimination."""
    csv_file = "duplication_master_list_updated.csv"
    
    print("🚀 Bldr Empire - Duplicate Elimination Workflow")
    print("=" * 50)
    
    # Load the duplicate tracker
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        print("   Please run generate_duplication_tracker.py first.")
        return
    
    duplicates = load_duplicate_tracker(csv_file)
    print(f"✅ Loaded {len(duplicates)} duplicate functions from {csv_file}")
    
    # Print current status
    print_workflow_status(duplicates)
    
    # Show the next function to process
    next_func = get_next_function_to_process(duplicates)
    if next_func:
        print(f"\n⏭️  Next function to process: {next_func['FunctionName']}")
        print(f"   Found in {next_func['FileCount']} files")
        print(f"   Primary file: {next_func['ChosenPrimaryFile']}")
        print(f"   Files: {', '.join([os.path.basename(f) for f in next_func['FileList']])}")
    else:
        print("\n✅ All functions have been processed!")
        print("   You can now run the verification step to ensure everything works correctly.")
    
    # Save the updated tracker
    save_duplicate_tracker(csv_file, duplicates)
    
    print(f"\n📋 WORKFLOW INSTRUCTIONS:")
    print(f"   1. Review the CSV file: {csv_file}")
    print(f"   2. For each function with Status='Pending':")
    print(f"      a. Use compare_function_versions.py to compare implementations")
    print(f"      b. Manually merge the best code into the primary file")
    print(f"      c. Update the CSV status to 'Merged'")
    print(f"      d. Use find_all_references.py to check for broken imports/calls")
    print(f"      e. Update the CSV status to 'Verified'")
    print(f"      f. Delete duplicate files and update status to 'Deleted'")
    print(f"   3. Run this script again to check progress")

if __name__ == "__main__":
    main()