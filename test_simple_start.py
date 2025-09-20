#!/usr/bin/env python3
"""
Simple test to see what's happening with the start command
"""

import subprocess
import os
from pathlib import Path

def test_simple():
    """Test simple start command"""
    project_root = Path("C:/Bldr")
    print(f"Project root: {project_root}")
    print(f"Project root exists: {project_root.exists()}")
    print(f"Current directory: {os.getcwd()}")
    
    # Change to project directory
    os.chdir(project_root)
    print(f"After chdir, current directory: {os.getcwd()}")
    
    # Try the command that should work like the bat file
    try:
        # This is what the bat file does:
        # start "FastAPI Backend" cmd /k "python -m uvicorn core.bldr_api:app --host 127.0.0.1 --port 8000 --reload"
        process = subprocess.Popen(
            ['start', '"FastAPI Backend"', 'cmd', '/k', '"python -m uvicorn core.bldr_api:app --host 127.0.0.1 --port 8000 --reload"'],
            cwd=str(project_root),
            shell=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
        print(f"Process started with PID: {process.pid}")
    except Exception as e:
        print(f"Error starting process: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple()