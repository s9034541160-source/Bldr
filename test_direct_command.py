#!/usr/bin/env python3
"""
Test script to run command directly like bat file
"""

import subprocess
import os
from pathlib import Path

def test_direct_command():
    """Test running command directly"""
    project_root = Path("C:/Bldr")
    print(f"Project root: {project_root}")
    print(f"Project root exists: {project_root.exists()}")
    
    # Change to project directory
    os.chdir(project_root)
    print(f"Current directory: {os.getcwd()}")
    
    # Run command exactly like bat file
    cmd = ['cmd', '/c', 'start', '"FastAPI Backend"', 'cmd', '/k', '"python -m uvicorn core.bldr_api:app --host 127.0.0.1 --port 8000 --reload"']
    
    print(f"Command: {' '.join(cmd)}")
    
    try:
        process = subprocess.Popen(
            cmd,
            cwd=str(project_root),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
        print(f"Process started with PID: {process.pid}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_direct_command()