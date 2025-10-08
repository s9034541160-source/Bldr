#!/usr/bin/env python3
"""
Helper tool for merging duplicate function implementations.
This tool extracts function code and shows differences to help with manual merging.
"""

import ast
import difflib
import os
import sys
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

def show_function_differences(func_name, primary_file, duplicate_files):
    """Show differences between function implementations."""
    print(f"\n🔍 FUNCTION DIFFERENCES FOR: {func_name}")
    print("=" * 80)
    
    # Extract primary implementation
    primary_code, _, _ = extract_function_code(primary_file, func_name)
    
    print(f"\n📍 PRIMARY IMPLEMENTATION ({os.path.basename(primary_file)}):")
    print("-" * 50)
    print(primary_code)
    
    # Compare with each duplicate
    for i, dup_file in enumerate(duplicate_files):
        if dup_file == primary_file:
            continue
            
        dup_code, _, _ = extract_function_code(dup_file, func_name)
        
        print(f"\n📄 DUPLICATE #{i+1} ({os.path.basename(dup_file)}):")
        print("-" * 50)
        
        # Show differences
        primary_lines = primary_code.splitlines()
        dup_lines = dup_code.splitlines()
        
        differ = difflib.unified_diff(
            primary_lines, 
            dup_lines, 
            fromfile=f'primary ({os.path.basename(primary_file)})',
            tofile=f'duplicate ({os.path.basename(dup_file)})',
            lineterm=''
        )
        
        diff_lines = list(differ)
        if diff_lines:
            for line in diff_lines:
                if line.startswith('+'):
                    print(f"➕ {line}")
                elif line.startswith('-'):
                    print(f"➖ {line}")
                elif line.startswith('@'):
                    print(f"🔍 {line}")
                else:
                    print(f"  {line}")
        else:
            print("  🔁 Identical to primary implementation")

def create_merge_template(func_name, primary_file, duplicate_files):
    """Create a template for merging implementations."""
    print(f"\n🛠️  MERGE TEMPLATE FOR: {func_name}")
    print("=" * 80)
    
    # Extract all implementations
    implementations = []
    
    # Primary implementation
    primary_code, _, _ = extract_function_code(primary_file, func_name)
    implementations.append({
        'file': primary_file,
        'code': primary_code,
        'type': 'primary'
    })
    
    # Duplicate implementations
    for dup_file in duplicate_files:
        if dup_file == primary_file:
            continue
            
        dup_code, _, _ = extract_function_code(dup_file, func_name)
        implementations.append({
            'file': dup_file,
            'code': dup_code,
            'type': 'duplicate'
        })
    
    # Create merge template
    template = f'''# 🛠️ MERGE TEMPLATE FOR FUNCTION: {func_name}
# =============================================================================

"""
This is a merge template for the function '{func_name}'.
Review all implementations and create the best combined version.

Original files:
'''
    
    for impl in implementations:
        file_type = "PRIMARY" if impl['type'] == 'primary' else "DUPLICATE"
        template += f"  {file_type}: {impl['file']}\n"
    
    template += '''
TODO:
1. Review all implementations below
2. Combine the best features from each
3. Ensure proper error handling
4. Add/update docstrings if needed
5. Copy the final merged version to the primary file
"""

'''
    
    # Add each implementation
    for i, impl in enumerate(implementations):
        file_type = "PRIMARY" if impl['type'] == 'primary' else "DUPLICATE"
        template += f"\n# {file_type} IMPLEMENTATION FROM: {impl['file']}\n"
        template += "# " + "="*70 + "\n"
        template += impl['code']
        template += "\n\n"
    
    template += f'''# 🎯 RECOMMENDED MERGED VERSION (WORK HERE)
# =============================================================================

def {func_name}():
    """
    TODO: Add/update docstring
    """
    # TODO: Implement the merged version here
    # Combine the best features from all implementations above
    pass

# 🔚 END OF MERGE TEMPLATE
'''
    
    # Save template to file
    template_file = f"merge_template_{func_name}.py"
    with open(template_file, 'w', encoding='utf-8') as f:
        f.write(template)
    
    print(f"✅ Merge template saved to: {template_file}")
    print("📝 Instructions:")
    print("   1. Open the template file")
    print("   2. Review all implementations")
    print("   3. Create the best merged version in the recommended section")
    print("   4. Copy the final version to your primary file")
    
    return template_file

def main():
    """Main function merger helper."""
    print("🔧 Bldr Empire - Function Merger Helper")
    print("=" * 50)
    print("This tool helps you merge duplicate function implementations.")
    
    # Example usage - in practice, you would call this from another script
    # with actual function names and file paths from your CSV
    """
    func_name = "example_function"
    primary_file = r"C:\Bldr\example_primary.py"
    duplicate_files = [
        r"C:\Bldr\example_duplicate1.py",
        r"C:\Bldr\example_duplicate2.py"
    ]
    
    # Show differences
    show_function_differences(func_name, primary_file, duplicate_files)
    
    # Create merge template
    template_file = create_merge_template(func_name, primary_file, duplicate_files)
    """

if __name__ == "__main__":
    main()