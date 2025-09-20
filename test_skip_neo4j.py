#!/usr/bin/env python3
"""
Test script to verify that the backend can start without Neo4j
"""

import os
import sys
import time
import subprocess

def main():
    """Test starting the backend with Neo4j skipped"""
    print("==========================================")
    print("   Bldr Empire v2 - Skip Neo4j Test")
    print("==========================================")
    print()
    
    # Change to project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Set environment variable to skip Neo4j
    os.environ["SKIP_NEO4J"] = "true"
    
    print("[INFO] Starting backend with Neo4j skipped...")
    print("[INFO] This will test if the backend can start without Neo4j")
    print()
    
    process = None
    
    try:
        # Start the backend
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "core.bldr_api:app", 
            "--host", "127.0.0.1", 
            "--port", "8000", 
            "--reload"
        ]
        
        print(f"[INFO] Running command: {' '.join(cmd)}")
        print()
        
        # Start the process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a bit to see if it starts
        time.sleep(15)
        
        # Check if process is still running
        if process.poll() is None:
            print("[SUCCESS] Backend started successfully with Neo4j skipped!")
            print("[INFO] The system is working without Neo4j dependency")
            # Kill the process
            process.terminate()
            process.wait()
            print("[INFO] Backend stopped")
        else:
            # Process has exited
            stdout, stderr = process.communicate()
            print("[STDOUT]:", stdout)
            if stderr:
                print("[STDERR]:", stderr)
            print("[ERROR] Backend failed to start")
            return 1
            
    except Exception as e:
        print(f"[ERROR] Failed to start backend: {e}")
        if process and process.poll() is None:
            process.terminate()
            process.wait()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())