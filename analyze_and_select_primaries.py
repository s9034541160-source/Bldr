import csv
import os
from datetime import datetime
from pathlib import Path

def get_file_modification_time(file_path):
    """Get file modification time."""
    try:
        return os.path.getmtime(file_path)
    except:
        return 0

def count_lines_in_file(file_path):
    """Count lines in a file as a simple measure of code size."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return len(f.readlines())
    except:
        return 0

def analyze_function_duplicates(csv_file):
    """Analyze duplicates and suggest primary files."""
    duplicates = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert FileList back to a list
            file_list = row['FileList'].split(';') if row['FileList'] else []
            row['FileList'] = file_list
            duplicates.append(row)
    
    # Sort by file count (descending) to focus on most duplicated functions first
    duplicates.sort(key=lambda x: int(x['FileCount']), reverse=True)
    
    return duplicates

def suggest_primary_file(file_list, func_name):
    """Suggest the best primary file based on modification time and code size."""
    file_info = []
    
    for file_path in file_list:
        if not os.path.exists(file_path):
            continue
            
        mod_time = get_file_modification_time(file_path)
        line_count = count_lines_in_file(file_path)
        
        # Prefer files that are:
        # 1. More recently modified
        # 2. Have more lines (more complete implementation)
        # 3. Not in archive directories
        is_archive = 'archive' in file_path.lower() or 'backup' in file_path.lower()
        
        file_info.append({
            'path': file_path,
            'mod_time': mod_time,
            'line_count': line_count,
            'is_archive': is_archive,
            'score': (mod_time / 1000000) + line_count - (100000 if is_archive else 0)
        })
    
    # Sort by score (descending)
    if file_info:
        file_info.sort(key=lambda x: x['score'], reverse=True)
        return file_info[0]['path']
    
    # Fallback to first file if no scoring worked
    return file_list[0] if file_list else ''

def update_csv_with_suggestions(csv_file, output_file):
    """Update CSV with suggested primary files."""
    duplicates = analyze_function_duplicates(csv_file)
    
    # Update rows with suggested primary files
    for row in duplicates:
        if not row['ChosenPrimaryFile']:  # Only update if not already set
            suggested = suggest_primary_file(row['FileList'], row['FunctionName'])
            row['ChosenPrimaryFile'] = suggested
            if suggested:
                row['Notes'] = f"Suggested automatically based on recency and completeness"
    
    # Write updated data back to CSV
    fieldnames = ['FunctionName', 'FileCount', 'FileList', 'ChosenPrimaryFile', 'Status', 'Notes']
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in duplicates:
            # Convert FileList back to semicolon-separated string
            row['FileList'] = ';'.join(row['FileList']) if isinstance(row['FileList'], list) else row['FileList']
            writer.writerow(row)
    
    return duplicates

def print_top_duplicates(duplicates, count=20):
    """Print the top duplicates for review."""
    print(f"\n📊 Top {count} Most Duplicated Functions:")
    print("="*80)
    
    for i, dup in enumerate(duplicates[:count]):
        print(f"{i+1:2d}. {dup['FunctionName']:<30} ({dup['FileCount']:<3} duplicates)")
        if dup['ChosenPrimaryFile']:
            print(f"     📌 Primary: {dup['ChosenPrimaryFile']}")
        else:
            print(f"     ⚠️  No primary selected")
        print()

if __name__ == "__main__":
    input_csv = "duplication_master_list.csv"
    output_csv = "duplication_master_list_updated.csv"
    
    print("🔍 Analyzing duplicates and suggesting primary files...")
    
    # Update CSV with suggestions
    duplicates = update_csv_with_suggestions(input_csv, output_csv)
    
    # Print top duplicates for review
    print_top_duplicates(duplicates)
    
    print(f"✅ Updated CSV saved to: {output_csv}")
    print(f"📋 Next steps:")
    print(f"   1. Review the suggested primary files in {output_csv}")
    print(f"   2. Manually adjust selections if needed")
    print(f"   3. Use compare_function_versions.py to compare implementations")
    print(f"   4. Begin merging the best code from duplicates into primary files")