#!/usr/bin/env python3
"""
Script to analyze and categorize duplicate functions in the Bldr project.
This will help identify patterns in the duplicates and prioritize cleanup efforts.
"""

import os
import ast
import sys
from collections import defaultdict, Counter
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
        # Silent fail for files that can't be parsed
        pass
        
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

def categorize_duplicates(duplicates):
    """
    Categorize duplicates by pattern to help with cleanup.
    
    Args:
        duplicates (dict): Dictionary mapping function names to lists of files
        
    Returns:
        dict: Categorized duplicates
    """
    categories = {
        'archive_duplicates': {},  # Duplicates involving archive files
        'plugin_duplicates': {},   # Duplicates in plugin system
        'agent_duplicates': {},    # Duplicates in agent system
        'tool_duplicates': {},     # Duplicates in tools system
        'trainer_duplicates': {},  # Duplicates in trainer scripts
        'integration_duplicates': {}, # Duplicates in integration files
        'core_duplicates': {},     # Duplicates in core modules
        'other_duplicates': {}     # Everything else
    }
    
    for func_name, files in duplicates.items():
        # Check for archive duplicates
        if any('archive' in f.lower() or 'backup' in f.lower() for f in files):
            categories['archive_duplicates'][func_name] = files
        # Check for plugin duplicates
        elif any('plugin' in f.lower() for f in files):
            categories['plugin_duplicates'][func_name] = files
        # Check for agent duplicates
        elif any('agent' in f.lower() for f in files):
            categories['agent_duplicates'][func_name] = files
        # Check for tool duplicates
        elif any('tool' in f.lower() for f in files):
            categories['tool_duplicates'][func_name] = files
        # Check for trainer duplicates
        elif any('trainer' in f.lower() or 'train' in f.lower() for f in files):
            categories['trainer_duplicates'][func_name] = files
        # Check for integration duplicates
        elif any('integration' in f.lower() or 'telegram' in f.lower() for f in files):
            categories['integration_duplicates'][func_name] = files
        # Check for core duplicates
        elif any('core' in f.lower() for f in files):
            categories['core_duplicates'][func_name] = files
        # Everything else
        else:
            categories['other_duplicates'][func_name] = files
            
    return categories

def print_categorized_report(categories):
    """
    Print a categorized report of duplicates.
    
    Args:
        categories (dict): Categorized duplicates
    """
    print("\n" + "="*80)
    print("CATEGORIZED DUPLICATE FUNCTIONS REPORT")
    print("="*80)
    
    category_names = {
        'archive_duplicates': 'ARCHIVE RELATED DUPLICATES',
        'plugin_duplicates': 'PLUGIN SYSTEM DUPLICATES',
        'agent_duplicates': 'AGENT SYSTEM DUPLICATES',
        'tool_duplicates': 'TOOLS SYSTEM DUPLICATES',
        'trainer_duplicates': 'TRAINER SCRIPT DUPLICATES',
        'integration_duplicates': 'INTEGRATION DUPLICATES',
        'core_duplicates': 'CORE MODULE DUPLICATES',
        'other_duplicates': 'OTHER DUPLICATES'
    }
    
    total_duplicates = 0
    
    for category_key, category_name in category_names.items():
        duplicates = categories[category_key]
        if duplicates:
            print(f"\n📂 {category_name} ({len(duplicates)} functions)")
            print("-" * 50)
            
            # Sort by number of duplicates (descending)
            sorted_duplicates = sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)
            
            for func_name, files in sorted_duplicates:
                print(f"\n🔸 {func_name} (in {len(files)} files)")
                for file in sorted(files):
                    # Highlight archive/backup files
                    if 'archive' in file.lower() or 'backup' in file.lower():
                        print(f"     📁 {file}")
                    else:
                        print(f"     📄 {file}")
                        
            total_duplicates += len(duplicates)
    
    return total_duplicates

def save_categorized_report(categories, output_file):
    """
    Save a categorized report of duplicates to a file.
    
    Args:
        categories (dict): Categorized duplicates
        output_file (str): Path to the output file
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("CATEGORIZED DUPLICATE FUNCTIONS REPORT\n")
        f.write("="*80 + "\n")
        
        category_names = {
            'archive_duplicates': 'ARCHIVE RELATED DUPLICATES',
            'plugin_duplicates': 'PLUGIN SYSTEM DUPLICATES',
            'agent_duplicates': 'AGENT SYSTEM DUPLICATES',
            'tool_duplicates': 'TOOLS SYSTEM DUPLICATES',
            'trainer_duplicates': 'TRAINER SCRIPT DUPLICATES',
            'integration_duplicates': 'INTEGRATION DUPLICATES',
            'core_duplicates': 'CORE MODULE DUPLICATES',
            'other_duplicates': 'OTHER DUPLICATES'
        }
        
        total_duplicates = 0
        
        for category_key, category_name in category_names.items():
            duplicates = categories[category_key]
            if duplicates:
                f.write(f"\n📂 {category_name} ({len(duplicates)} functions)\n")
                f.write("-" * 50 + "\n")
                
                # Sort by number of duplicates (descending)
                sorted_duplicates = sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)
                
                for func_name, files in sorted_duplicates:
                    f.write(f"\n🔸 {func_name} (in {len(files)} files)\n")
                    for file in sorted(files):
                        # Highlight archive/backup files
                        if 'archive' in file.lower() or 'backup' in file.lower():
                            f.write(f"     📁 {file}\n")
                        else:
                            f.write(f"     📄 {file}\n")
                            
                total_duplicates += len(duplicates)
        
        return total_duplicates

def main():
    """Main function to run the duplicate analyzer."""
    root_dir = r"C:\Bldr"
    
    if not os.path.exists(root_dir):
        print(f"Error: Directory {root_dir} does not exist!")
        sys.exit(1)
        
    print("🔍 Bldr Empire - Duplicate Function Analyzer")
    print("="*50)
    
    # Scan directory for Python files and extract functions
    file_functions = scan_directory(root_dir)
    
    # Find duplicates
    duplicates = find_duplicates(file_functions)
    
    # Categorize duplicates
    categories = categorize_duplicates(duplicates)
    
    # Print categorized report
    total_categorized = print_categorized_report(categories)
    
    # Save categorized report to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"duplicate_analysis_report_{timestamp}.txt"
    save_categorized_report(categories, report_file)
    
    # Summary
    total_files = len(file_functions)
    total_functions = sum(len(functions) for functions in file_functions.values())
    total_duplicates = len(duplicates)
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total Python files scanned: {total_files}")
    print(f"Total function definitions: {total_functions}")
    print(f"Total duplicate functions: {total_duplicates}")
    print(f"Categorized duplicates: {total_categorized}")
    print(f"Analysis report saved to: {report_file}")
    
    # Priority recommendations
    print("\n" + "="*80)
    print("CLEANUP PRIORITY RECOMMENDATIONS")
    print("="*80)
    print("1. 🔥 ARCHIVE RELATED DUPLICATES - Clean first as these are likely obsolete")
    print("2. 🔧 PLUGIN SYSTEM DUPLICATES - High priority for system stability")
    print("3. 🤖 AGENT SYSTEM DUPLICATES - High priority for coordinator functionality")
    print("4. 🛠️ TOOLS SYSTEM DUPLICATES - High priority for tool execution")
    print("5. 🏋️ TRAINER SCRIPT DUPLICATES - Medium priority")
    print("6. 🌐 INTEGRATION DUPLICATES - Medium priority")
    print("7. 📦 CORE MODULE DUPLICATES - High priority for system foundation")
    print("8. 📝 OTHER DUPLICATES - Low priority")

if __name__ == "__main__":
    main()