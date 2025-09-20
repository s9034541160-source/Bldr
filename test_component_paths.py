#!/usr/bin/env python3
"""
Test script to verify component manager paths
"""

import sys
from pathlib import Path

# Add system_launcher to path
sys.path.append(str(Path(__file__).parent))

from system_launcher.component_manager import SystemComponentManager

def test_component_paths():
    """Test component manager paths"""
    print("Testing component manager paths...")
    
    # Create component manager
    cm = SystemComponentManager()
    
    # Check backend component config
    backend = cm.get_component_status('backend')
    if backend:
        print(f"Backend config: {backend.config}")
        print(f"Backend working dir: {backend.config.get('working_dir', 'Not set')}")
        
        # Check project root calculation
        project_root = Path(__file__).parent.parent
        print(f"Calculated project root: {project_root}")
        print(f"Project root exists: {project_root.exists()}")

if __name__ == "__main__":
    test_component_paths()