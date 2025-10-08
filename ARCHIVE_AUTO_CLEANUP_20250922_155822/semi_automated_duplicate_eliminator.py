#!/usr/bin/env python3
"""
Semi-automated workflow for eliminating duplicates in the Bldr project.
This script guides you through the process while handling mechanical tasks.
"""

import csv
import os
import shutil
import sys
import subprocess
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
    # Sort by file count (descending) to process high-priority functions first
    pending = [d for d in duplicates if d['Status'] == 'Pending']
    pending.sort(key=lambda x: int(x['FileCount']), reverse=True)
    return pending[0] if pending else None

def backup_file(file_path):
    """Create a backup of a file before modifying it."""
    if not os.path.exists(file_path):
        return None
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{file_path}.backup_{timestamp}"
    shutil.copy2(file_path, backup_path)
    return backup_path

def compare_function_implementations(func_name, primary_file, duplicate_files):
    """Use the compare tool to show differences between implementations."""
    print(f"\n🔍 COMPARING IMPLEMENTATIONS FOR: {func_name}")
    print("=" * 60)
    
    # Create a temporary script to run the comparison
    temp_script = f"temp_compare_{func_name}.py"
    
    # Filter out the primary file from duplicates for comparison
    actual_duplicates = [f for f in duplicate_files if f != primary_file]
    
    if not actual_duplicates:
        print("No duplicate files to compare (only primary file exists)")
        return
    
    # Create comparison data
    comparison_code = f'''import sys
sys.path.append(r"C:\\\\Bldr")

# Import the comparison function
from compare_function_versions import compare_versions

# Function to compare: {func_name}
primary_version = r"{primary_file}"
duplicates = {actual_duplicates}

compare_versions(primary_version, duplicates, "{func_name}")
'''
    
    with open(temp_script, 'w', encoding='utf-8') as f:
        f.write(comparison_code)
    
    # Run the comparison
    try:
        result = subprocess.run(
            [sys.executable, temp_script], 
            capture_output=True, 
            text=True, 
            cwd=r"C:\Bldr",
            timeout=30
        )
        print(result.stdout)
        if result.stderr:
            print("Errors during comparison:")
            print(result.stderr)
    except subprocess.TimeoutExpired:
        print("Comparison timed out")
    except Exception as e:
        print(f"Error during comparison: {e}")
    finally:
        # Clean up temporary script
        if os.path.exists(temp_script):
            os.remove(temp_script)

def find_function_references(func_name):
    """Use the reference finder tool to show all references."""
    print(f"\n🔍 FINDING REFERENCES FOR: {func_name}")
    print("=" * 60)
    
    # Create a temporary script to run the reference finder
    temp_script = f"temp_find_refs_{func_name}.py"
    
    # Create reference finder code
    reference_code = f'''import sys
sys.path.append(r"C:\\\\Bldr")

# Import the reference finder function
from find_all_references import find_function_references

# Function to find: {func_name}
project_root = r"C:\\\\Bldr"
refs = find_function_references(project_root, "{func_name}")

if refs:
    print(f"Found {{len(refs)}} references to '{{func_name}}':")
    for ref in refs:
        print(f"  {{ref}}")
else:
    print(f"No references found to '{{func_name}}'")
'''
    
    with open(temp_script, 'w', encoding='utf-8') as f:
        f.write(reference_code)
    
    # Run the reference finder
    try:
        result = subprocess.run(
            [sys.executable, temp_script], 
            capture_output=True, 
            text=True, 
            cwd=r"C:\Bldr",
            timeout=60  # Longer timeout for reference finding
        )
        print(result.stdout)
        if result.stderr:
            print("Errors during reference finding:")
            print(result.stderr)
    except subprocess.TimeoutExpired:
        print("Reference finding timed out")
    except Exception as e:
        print(f"Error during reference finding: {e}")
    finally:
        # Clean up temporary script
        if os.path.exists(temp_script):
            os.remove(temp_script)

def mark_function_as_processed(duplicates, func_name, status, notes=""):
    """Mark a function as processed in the duplicates list."""
    for dup in duplicates:
        if dup['FunctionName'] == func_name:
            dup['Status'] = status
            if notes:
                dup['Notes'] = notes
            return True
    return False

def process_next_function(duplicates):
    """Process the next function in the queue."""
    next_func = get_next_function_to_process(duplicates)
    
    if not next_func:
        print("\n🎉 ALL FUNCTIONS HAVE BEEN PROCESSED!")
        return False
    
    func_name = next_func['FunctionName']
    file_count = int(next_func['FileCount'])
    primary_file = next_func['ChosenPrimaryFile']
    file_list = next_func['FileList']
    
    print(f"\n🚀 PROCESSING FUNCTION: {func_name}")
    print("=" * 60)
    print(f"Files with this function: {file_count}")
    print(f"Primary file: {primary_file}")
    print(f"Status: {next_func['Status']}")
    
    if not primary_file:
        print("⚠️  No primary file selected. Please review the CSV and select a primary file.")
        input("Press Enter to continue to the next function...")
        return True
    
    # Step 1: Compare implementations
    print(f"\n_STEP 1: COMPARING IMPLEMENTATIONS_")
    compare_function_implementations(func_name, primary_file, file_list)
    
    # Step 2: Show references
    print(f"\n_STEP 2: FINDING REFERENCES_")
    find_function_references(func_name)
    
    # Step 3: User decision
    print(f"\n_STEP 3: USER ACTION REQUIRED_")
    print("=" * 60)
    print("What would you like to do with this function?")
    print("1. Mark as Reviewed (I've manually compared and will merge later)")
    print("2. Mark as Merged (I've already merged the best code)")
    print("3. Skip for now (Move to next function)")
    print("4. Exit (Continue later)")
    
    while True:
        choice = input("\nEnter your choice (1-4): ").strip()
        if choice in ['1', '2', '3', '4']:
            break
        print("Please enter a valid choice (1-4)")
    
    if choice == '1':
        mark_function_as_processed(duplicates, func_name, 'Reviewed', 
                                 f"Reviewed on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"✅ Marked {func_name} as Reviewed")
    elif choice == '2':
        mark_function_as_processed(duplicates, func_name, 'Merged', 
                                 f"Merged on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"✅ Marked {func_name} as Merged")
    elif choice == '3':
        print(f"⏭️  Skipping {func_name} for now")
        return True
    elif choice == '4':
        print("👋 Exiting. Your progress has been saved.")
        return False
    
    return True

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

def main():
    """Main semi-automated workflow."""
    csv_file = "duplication_master_list_updated.csv"
    
    print("🤖 Bldr Empire - Semi-Automated Duplicate Eliminator")
    print("=" * 60)
    print("This tool will guide you through eliminating duplicates")
    print("while handling the mechanical parts automatically.")
    
    # Load the duplicate tracker
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        print("   Please run the duplicate elimination workflow first.")
        return
    
    duplicates = load_duplicate_tracker(csv_file)
    print(f"✅ Loaded {len(duplicates)} duplicate functions")
    
    # Show progress
    print_progress(duplicates)
    
    # Process functions one by one
    while True:
        try:
            should_continue = process_next_function(duplicates)
            if not should_continue:
                break
            
            # Save progress after each function
            save_duplicate_tracker(csv_file, duplicates)
            
            # Show updated progress
            print_progress(duplicates)
            
            # Ask if user wants to continue
            continue_choice = input("\nContinue to next function? (Y/n): ").strip().lower()
            if continue_choice in ['n', 'no']:
                break
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Error processing function: {e}")
            continue_choice = input("Continue to next function? (Y/n): ").strip().lower()
            if continue_choice in ['n', 'no']:
                break
    
    # Save final progress
    save_duplicate_tracker(csv_file, duplicates)
    print(f"\n✅ Progress saved to {csv_file}")
    print("👋 Thank you for using the Semi-Automated Duplicate Eliminator!")

if __name__ == "__main__":
    main()
