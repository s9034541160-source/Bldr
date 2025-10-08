import ast
import os
import shutil
from pathlib import Path

def extract_function_code(file_path, func_name):
    """Extract the complete source code of a function from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                lines = source.splitlines()
                start_line = node.lineno - 1
                end_line = getattr(node, 'end_lineno', len(lines))
                func_code = "\n".join(lines[start_line:end_line])
                return func_code, start_line, end_line
    except Exception as e:
        return f"# ERROR extracting function: {e}", 0, 0
    
    return f"# Function '{func_name}' not found in {file_path}", 0, 0

def replace_function_in_file(file_path, func_name, new_code):
    """Replace a function in a file with new code."""
    try:
        # Read the entire file
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Extract the function to find its location
        source = ''.join(lines)
        tree = ast.parse(source)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                start_line = node.lineno - 1
                end_line = getattr(node, 'end_lineno', len(lines))
                
                # Replace the function
                new_lines = new_code.split('\n')
                # Remove the last empty line if it exists
                if new_lines and new_lines[-1] == '':
                    new_lines = new_lines[:-1]
                
                # Replace the old function with the new one
                lines[start_line:end_line] = [line + '\n' for line in new_lines]
                
                # Write the updated file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                
                return True
    except Exception as e:
        print(f"Error replacing function: {e}")
        return False
    
    return False

def backup_file(file_path):
    """Create a backup of a file before modifying it."""
    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    return backup_path

def merge_function_implementations(primary_file, duplicate_files, func_name):
    """
    Merge the best implementations from duplicate files into the primary file.
    This is a simplified version - in practice, you'd want to do a more sophisticated
    comparison and merging of the code.
    """
    print(f"\n🔄 Merging implementations for function: {func_name}")
    print(f"📍 Primary file: {primary_file}")
    print(f"📚 Duplicate files: {len(duplicate_files)}")
    
    # Extract code from primary file
    primary_code, _, _ = extract_function_code(primary_file, func_name)
    print(f"\n📄 Primary implementation:")
    print("-" * 40)
    print(primary_code[:200] + "..." if len(primary_code) > 200 else primary_code)
    
    # For now, we'll just show what's in the duplicates
    # In a real implementation, you'd want to do a detailed comparison
    for i, dup_file in enumerate(duplicate_files):
        if dup_file == primary_file:
            continue
            
        dup_code, _, _ = extract_function_code(dup_file, func_name)
        print(f"\n📄 Duplicate #{i+1} ({os.path.basename(dup_file)}):")
        print("-" * 40)
        print(dup_code[:200] + "..." if len(dup_code) > 200 else dup_code)
    
    print(f"\n⚠️  Manual merging required!")
    print(f"   Please review the implementations above and manually merge the best parts")
    print(f"   from duplicates into the primary file: {primary_file}")

def update_csv_status(csv_file, func_name, status, notes=""):
    """Update the status of a function in the CSV file."""
    import csv
    
    rows = []
    updated = False
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['FunctionName'] == func_name:
                row['Status'] = status
                if notes:
                    row['Notes'] = notes
                updated = True
            rows.append(row)
    
    if updated:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        
        print(f"✅ Updated status for {func_name} to '{status}' in {csv_file}")

# Example usage
if __name__ == "__main__":
    from datetime import datetime
    
    # Example of how to use this script
    print("🔧 Duplicate Merger Tool")
    print("=" * 40)
    print("This script helps merge duplicate function implementations.")
    print("For each function, it will:")
    print("1. Show the primary implementation")
    print("2. Show all duplicate implementations")
    print("3. Allow you to manually merge the best parts")
    print("4. Update the CSV status tracker")
    print("\n📝 Note: This is a helper tool. Actual merging requires manual work.")
    
    # Example for a specific function (you would replace these with actual values from your CSV)
    """
    func_name = "main"
    primary_file = r"C:\Bldr\bldr_gui.py"
    duplicate_files = [
        r"C:\Bldr\bldr_gui_manager.py",
        r"C:\Bldr\core\test_main.py",
        # ... add all duplicates from CSV
    ]
    
    merge_function_implementations(primary_file, duplicate_files, func_name)
    """