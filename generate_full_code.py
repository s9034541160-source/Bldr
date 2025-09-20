#!/usr/bin/env python3
"""
Script to generate the full_code_130925.txt file quickly
"""

import os
from pathlib import Path

def generate_full_code():
    """Generate the full code structure file"""
    project_root = Path(__file__).parent
    output_file = project_root / "full_code_130925.txt"
    
    # Get directory structure
    dir_structure = []
    for root, dirs, files in os.walk(project_root):
        # Skip __pycache__ directories and .git directories
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv']]
        
        level = root.replace(str(project_root), '').count(os.sep)
        indent = '│   ' * (level - 1) + '├── ' if level > 0 else ''
        dir_structure.append(f"{indent}{os.path.basename(root)}/")
        
        subindent = '│   ' * level + '├── '
        for file in files:
            # Skip the output file itself
            if file != "full_code_130925.txt" and file != "generate_full_code.py":
                dir_structure.append(f"{subindent}{file}")
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# SuperBuilder Project Structure and Code Dump\n")
        f.write("# Generated on 2025-09-13\n\n")
        f.write("## Directory Structure\n")
        f.write("```\n")
        f.write("ss_v1/\n")
        
        # Write the directory structure
        for line in dir_structure[1:]:  # Skip the root directory
            f.write(f"{line}\n")
        
        f.write("```\n\n")
        
        # Add some key configuration files
        config_files = [
            ".env.example",
            "requirements.txt",
            "requirements-dev.txt",
            "requirements-enhanced.txt"
        ]
        
        f.write("## Configuration Files\n\n")
        
        for config_file in config_files:
            config_path = project_root / config_file
            if config_path.exists():
                f.write(f"### {config_file}\n")
                f.write("```\n")
                with open(config_path, 'r', encoding='utf-8') as cf:
                    f.write(cf.read())
                f.write("```\n\n")
    
    print(f"Full code structure generated at {output_file}")

if __name__ == "__main__":
    generate_full_code()