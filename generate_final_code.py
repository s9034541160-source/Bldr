#!/usr/bin/env python3
"""
Script to generate a full code file with only final production-ready Python files
Excludes tests, debug files, backups, and temporary files
"""

import os
import fnmatch
from pathlib import Path

def should_include_file(file_path):
    """
    Determine if a file should be included in the final code dump
    Returns True if file should be included, False otherwise
    """
    filename = os.path.basename(file_path)
    
    # Exclude patterns
    exclude_patterns = [
        '*test*',
        '*debug*',
        '*fix*',
        '*bak*',
        '*copy*',
        '*temp*',
        '*tmp*',
        '*backup*',
        '*old*',
        '*draft*',
        '*example*',
        '*sample*',
        '*demo*',
        '*trial*',
        '*experiment*',
        '*playground*',
        '*scratch*',
        '*notes*',
        '*log*',
        '*cache*',
        '*pycache*',
        '.git*',
        '__pycache__',
        '*.pyc',
        '*.pyo',
        '*.pyd',
        '*.so',
        '*.dll',
        '*.exe',
        '*.bat',
        '*.sh',
        '*.md',
        '*.txt',
        '*.json',
        '*.yml',
        '*.yaml',
        '*.toml',
        '*.cfg',
        '*.ini',
        '*.log',
        '*.out',
        '*.err',
        '*.tmp',
        '*.swp',
        '*.swo',
        '*~',
        '*.bak',
        '*.orig',
        '*.rej',
        '*.patch',
        '*.diff'
    ]
    
    # Check if file matches any exclude pattern
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(filename.lower(), pattern.lower()):
            return False
    
    # Include only Python files for the final code
    if not filename.endswith('.py'):
        return False
    
    # Specific files to exclude
    exclude_files = [
        'generate_full_code.py',
        'generate_final_code.py',
        'setup.py',
        'pyproject.toml'
    ]
    
    if filename in exclude_files:
        return False
    
    return True

def should_include_directory(dir_path):
    """
    Determine if a directory should be included in the final code dump
    Returns True if directory should be included, False otherwise
    """
    dirname = os.path.basename(dir_path)
    
    # Exclude directories
    exclude_dirs = [
        '__pycache__',
        '.git',
        'venv',
        'env',
        'node_modules',
        'build',
        'dist',
        'tests',
        'test',
        'docs',
        'doc',
        'examples',
        'samples',
        'demos',
        'tmp',
        'temp',
        'logs',
        'backup',
        'backups'
    ]
    
    return dirname not in exclude_dirs

def collect_python_files(root_dir):
    """
    Collect all Python files that should be included in the final code
    """
    python_files = []
    
    for root, dirs, files in os.walk(root_dir):
        # Filter directories
        dirs[:] = [d for d in dirs if should_include_directory(os.path.join(root, d))]
        
        # Collect Python files
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith('.py') and should_include_file(file_path):
                python_files.append(file_path)
    
    return python_files

def generate_final_code():
    """Generate the final code structure file"""
    project_root = Path(__file__).parent
    output_file = project_root / "final_code.txt"
    
    # Collect all Python files
    python_files = collect_python_files(project_root)
    
    # Sort files for consistent output
    python_files.sort()
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Bldr Empire v2 - Final Production Code\n")
        f.write("# Generated on 2025-09-13\n\n")
        
        f.write("## Table of Contents\n")
        for i, file_path in enumerate(python_files, 1):
            relative_path = os.path.relpath(file_path, project_root)
            f.write(f"{i}. {relative_path}\n")
        f.write("\n")
        
        # Add each Python file
        for i, file_path in enumerate(python_files, 1):
            relative_path = os.path.relpath(file_path, project_root)
            f.write(f"## {i}. {relative_path}\n")
            f.write("```\n")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as py_file:
                    content = py_file.read()
                    f.write(content)
            except Exception as e:
                f.write(f"# Error reading file: {e}\n")
            
            f.write("\n```\n\n")
    
    print(f"Final code generated at {output_file}")
    print(f"Total files included: {len(python_files)}")

if __name__ == "__main__":
    generate_final_code()