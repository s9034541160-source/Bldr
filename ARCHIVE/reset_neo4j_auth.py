#!/usr/bin/env python3
"""
Script to help reset Neo4j authentication
"""

import os
import subprocess
import time
import psutil

def check_neo4j_processes():
    """Check if any Neo4j/Java processes are running"""
    java_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'java.exe' and 'neo4j' in ' '.join(proc.info['cmdline']).lower():
                java_processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return java_processes

def kill_neo4j_processes():
    """Kill all Neo4j/Java processes"""
    java_processes = check_neo4j_processes()
    if not java_processes:
        print("✅ No Neo4j processes found")
        return True
    
    print(f"⚠️ Found {len(java_processes)} Neo4j processes:")
    for proc in java_processes:
        try:
            print(f"   - PID {proc['pid']}: {' '.join(proc['cmdline'])}")
            # Kill the process
            p = psutil.Process(proc['pid'])
            p.terminate()
            print(f"     Terminated PID {proc['pid']}")
        except Exception as e:
            print(f"     ❌ Failed to terminate PID {proc['pid']}: {e}")
    
    # Wait a moment for processes to terminate
    time.sleep(5)
    
    # Check if any processes remain
    remaining = check_neo4j_processes()
    if remaining:
        print("⚠️ Some processes still running, forcing termination...")
        for proc in remaining:
            try:
                p = psutil.Process(proc['pid'])
                p.kill()
                print(f"     Force killed PID {proc['pid']}")
            except Exception as e:
                print(f"     ❌ Failed to force kill PID {proc['pid']}: {e}")
        
        time.sleep(3)
    
    # Final check
    final_check = check_neo4j_processes()
    if final_check:
        print("❌ Some Neo4j processes are still running:")
        for proc in final_check:
            print(f"   - PID {proc['pid']}: {' '.join(proc['cmdline'])}")
        return False
    else:
        print("✅ All Neo4j processes terminated successfully")
        return True

def main():
    print("Neo4j Authentication Reset Helper")
    print("=" * 40)
    print()
    
    print("Step 1: Checking for running Neo4j processes...")
    processes = check_neo4j_processes()
    if processes:
        print(f"⚠️ Found {len(processes)} Neo4j processes running")
        response = input("Do you want to stop all Neo4j processes? (y/N): ")
        if response.lower() == 'y':
            if kill_neo4j_processes():
                print("✅ Neo4j processes stopped. You can now reset authentication in Neo4j Desktop.")
            else:
                print("❌ Failed to stop all Neo4j processes. Please close Neo4j Desktop manually.")
        else:
            print("ℹ️ Please close Neo4j Desktop manually before proceeding with authentication reset.")
    else:
        print("✅ No Neo4j processes found. You can now reset authentication in Neo4j Desktop.")
    
    print()
    print("Next steps:")
    print("1. Open Neo4j Desktop")
    print("2. Find your database instance (Bldr2)")
    print("3. Click on the 'Manage' button for your instance")
    print("4. Go to the 'Settings' tab")
    print("5. Find the line that says 'dbms.security.auth_enabled=true'")
    print("6. Change it to 'dbms.security.auth_enabled=false'")
    print("7. Click 'Apply' and restart the database instance")
    print()
    print("After resetting authentication, test the connection with:")
    print("   python test_neo4j_connection_simple.py")

if __name__ == "__main__":
    main()