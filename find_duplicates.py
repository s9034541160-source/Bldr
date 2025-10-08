#!/usr/bin/env python3
"""
Script to find duplicate function definitions across all Python files in the Bldr project.
This script will:
1. List all files in the C:\Bldr folder and subfolders (excluding venv, archive, .git)
2. For each .py file, extract all function definitions
3. Identify and report duplicate function names across files
4. Save results to a report file
"""

import os
import ast
import sys
from collections import defaultdict
from datetime import datetime

def extract_functions_from_file(file_path):
    """
    Extract all function definitions from a Python file.
    
    Args:
        file_path (str): Path to the Python file
        
    Returns:
        list: List of function names defined in the file
    """
    functions = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Parse the Python code
        tree = ast.parse(content)
        
        # Extract function definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
                
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        
    return functions

def scan_directory(root_dir):
    """
    Scan directory and subdirectories for Python files and extract functions.
    
    Args:
        root_dir (str): Root directory to scan
        
    Returns:
        dict: Dictionary mapping file paths to lists of function names
    """
    file_functions = {}
    
    print(f"Scanning directory: {root_dir}")
    
    # Folders to exclude
    exclude_folders = {'venv', 'archive', '.git'}
    
    for root, dirs, files in os.walk(root_dir):
        # Remove excluded directories from dirs so os.walk doesn't traverse them
        dirs[:] = [d for d in dirs if d not in exclude_folders]
        
        # Check if current directory should be skipped
        should_skip = False
        for exclude in exclude_folders:
            if exclude in root.split(os.sep):
                should_skip = True
                break
                
        if should_skip:
            continue
            
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                functions = extract_functions_from_file(file_path)
                file_functions[file_path] = functions
                
                # Print progress
                if functions:
                    print(f"Found {len(functions)} functions in {file_path}")
                    
    return file_functions

def find_duplicates(file_functions):
    """
    Find duplicate function names across all files.
    
    Args:
        file_functions (dict): Dictionary mapping file paths to lists of function names
        
    Returns:
        dict: Dictionary mapping function names to lists of files where they're defined
    """
    function_locations = defaultdict(list)
    
    # Map each function to the files where it's defined
    for file_path, functions in file_functions.items():
        for function in functions:
            function_locations[function].append(file_path)
            
    # Filter to only include functions defined in multiple files (duplicates)
    duplicates = {func: files for func, files in function_locations.items() if len(files) > 1}
    
    return duplicates

def print_file_contents(file_functions):
    """
    Print all files and their function definitions.
    
    Args:
        file_functions (dict): Dictionary mapping file paths to lists of function names
    """
    print("\n" + "="*80)
    print("FILE CONTENTS REPORT")
    print("="*80)
    
    for file_path, functions in file_functions.items():
        print(f"\n📁 {file_path}")
        if functions:
            for func in sorted(functions):
                print(f"   def {func}()")
        else:
            print("   (No functions found)")

def save_file_contents(file_functions, output_file):
    """
    Save all files and their function definitions to a file.
    
    Args:
        file_functions (dict): Dictionary mapping file paths to lists of function names
        output_file (str): Path to the output file
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("FILE CONTENTS REPORT\n")
        f.write("="*80 + "\n")
        
        for file_path, functions in file_functions.items():
            f.write(f"\n📁 {file_path}\n")
            if functions:
                for func in sorted(functions):
                    f.write(f"   def {func}()\n")
            else:
                f.write("   (No functions found)\n")

def print_duplicate_report(duplicates):
    """
    Print a report of duplicate functions.
    
    Args:
        duplicates (dict): Dictionary mapping function names to lists of files
    """
    print("\n" + "="*80)
    print("DUPLICATE FUNCTIONS REPORT")
    print("="*80)
    
    if not duplicates:
        print("✅ No duplicate functions found!")
        return
        
    print(f"❌ Found {len(duplicates)} duplicate functions:")
    
    for func_name, files in duplicates.items():
        print(f"\n🔸 Function: {func_name}")
        print(f"   Defined in {len(files)} files:")
        for file in sorted(files):
            print(f"     - {file}")

def save_duplicate_report(duplicates, output_file):
    """
    Save a report of duplicate functions to a file.
    
    Args:
        duplicates (dict): Dictionary mapping function names to lists of files
        output_file (str): Path to the output file
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("DUPLICATE FUNCTIONS REPORT\n")
        f.write("="*80 + "\n")
        
        if not duplicates:
            f.write("✅ No duplicate functions found!\n")
            return
            
        f.write(f"❌ Found {len(duplicates)} duplicate functions:\n")
        
        for func_name, files in duplicates.items():
            f.write(f"\n🔸 Function: {func_name}\n")
            f.write(f"   Defined in {len(files)} files:\n")
            for file in sorted(files):
                f.write(f"     - {file}\n")

def main():
    """Main function to run the duplicate finder."""
    root_dir = r"C:\Bldr"
    
    if not os.path.exists(root_dir):
        print(f"Error: Directory {root_dir} does not exist!")
        sys.exit(1)
        
    print("🔍 Bldr Empire - Duplicate Function Finder")
    print("="*50)
    
    # Scan directory for Python files and extract functions
    file_functions = scan_directory(root_dir)
    
    # Print all file contents
    print_file_contents(file_functions)
    
    # Find duplicates
    duplicates = find_duplicates(file_functions)
    
    # Print duplicate report
    print_duplicate_report(duplicates)
    
    # Save reports to files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    contents_file = f"duplicate_report_contents_{timestamp}.txt"
    duplicates_file = f"duplicate_report_duplicates_{timestamp}.txt"
    
    save_file_contents(file_functions, contents_file)
    save_duplicate_report(duplicates, duplicates_file)
    
    # Summary
    total_files = len(file_functions)
    total_functions = sum(len(functions) for functions in file_functions.values())
    duplicate_functions = len(duplicates)
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total Python files scanned: {total_files}")
    print(f"Total function definitions: {total_functions}")
    print(f"Duplicate functions found: {duplicate_functions}")
    print(f"Full contents report saved to: {contents_file}")
    print(f"Duplicate report saved to: {duplicates_file}")
    
    if duplicate_functions > 0:
        print("\n⚠️  ACTION REQUIRED: Please review and resolve duplicate functions!")
    else:
        print("\n✅ No duplicates found. System is clean!")

if __name__ == "__main__":
    main()