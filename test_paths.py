#!/usr/bin/env python3
"""
Test script to verify paths
"""

import sys
from pathlib import Path

# Add system_launcher to path
sys.path.append(str(Path(__file__).parent))

from system_launcher.component_manager import SystemComponentManager

def test_paths():
    """Test paths"""
    print("Testing paths...")
    
    # Create component manager
    cm = SystemComponentManager()
    
    # Check project root
    project_root = Path(__file__).parent
    print(f"Current script path: {Path(__file__)}")
    print(f"Project root: {project_root}")
    print(f"Project root exists: {project_root.exists()}")
    
    # Check core directory
    core_path = project_root / 'core'
    print(f"Core path: {core_path}")
    print(f"Core path exists: {core_path.exists()}")
    
    # Check bldr_api.py
    api_file = core_path / 'bldr_api.py'
    print(f"API file: {api_file}")
    print(f"API file exists: {api_file.exists()}")

if __name__ == "__main__":
    test_paths()