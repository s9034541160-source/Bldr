#!/usr/bin/env python3
"""
Test script to start the backend without Neo4j dependency
"""

import os
import sys
import time
import subprocess

def main():
    """Test starting the backend without Neo4j"""
    print("==========================================")
    print("   Bldr Empire v2 - Backend Test")
    print("==========================================")
    print()
    
    # Change to project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Set environment variable to skip Neo4j
    os.environ["SKIP_NEO4J"] = "true"
    
    print("[INFO] Starting backend with Neo4j disabled...")
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
        time.sleep(10)
        
        # Check if process is still running
        if process.poll() is None:
            print("[SUCCESS] Backend started successfully without Neo4j!")
            print("[INFO] Press Ctrl+C to stop the backend")
            try:
                # Wait for the process to complete or be interrupted
                stdout, stderr = process.communicate(timeout=30)
                print("[STDOUT]:", stdout)
                if stderr:
                    print("[STDERR]:", stderr)
            except subprocess.TimeoutExpired:
                print("[INFO] Backend is running normally")
                process.terminate()
        else:
            # Process has exited
            stdout, stderr = process.communicate()
            print("[STDOUT]:", stdout)
            if stderr:
                print("[STDERR]:", stderr)
            print("[ERROR] Backend failed to start")
            
    except KeyboardInterrupt:
        print("[INFO] Stopping backend...")
        if process and process.poll() is None:
            process.terminate()
            process.wait()
        print("[INFO] Backend stopped")
    except Exception as e:
        print(f"[ERROR] Failed to start backend: {e}")
        if process and process.poll() is None:
            process.terminate()
            process.wait()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())