#!/usr/bin/env python3
from system_launcher.component_manager import SystemComponentManager
import time

cm = SystemComponentManager()
print("Waiting for components to start...")
time.sleep(15)

print("Checking component statuses...")
components = cm.get_all_components()
for comp_id, comp in components.items():
    print(f"{comp_id}: {comp.status.value}")
    if comp.last_error:
        print(f"  Error: {comp.last_error}")


"""
Bldr Empire v2 - Service Status Checker
Checks if all required services are running properly
"""

import requests
import subprocess
import sys
import time
from pathlib import Path

def check_api_status():
    """Check if the API server is running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return True, data.get("status", "unknown")
        else:
            return False, f"HTTP {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Connection refused"
    except Exception as e:
        return False, str(e)

def check_dashboard_status():
    """Check if the dashboard is running"""
    try:
        # Try both common Vite ports
        for port in [5173, 3000]:
            try:
                response = requests.get(f"http://localhost:{port}", timeout=5)
                if response.status_code in [200, 404]:  # 404 is OK for Vite dev server
                    return True, f"Running on port {port}"
            except:
                continue
        return False, "Connection refused"
    except Exception as e:
        return False, str(e)

def check_python_processes():
    """Check if Python processes are running"""
    try:
        # This is Windows-specific
        result = subprocess.run(["tasklist", "/fi", "imagename eq python.exe"], 
                              capture_output=True, text=True, timeout=10)
        # Count how many python processes are running
        lines = result.stdout.strip().split("\n")
        python_count = len([line for line in lines if "python.exe" in line and "===" not in line])
        if python_count > 1:  # More than just the tasklist command itself
            return True, f"Python processes found ({python_count-1} Bldr services)"
        else:
            return False, "No Bldr Python processes found"
    except Exception as e:
        return False, str(e)

def check_node_processes():
    """Check if Node.js processes are running"""
    try:
        # This is Windows-specific
        result = subprocess.run(["tasklist", "/fi", "imagename eq node.exe"], 
                              capture_output=True, text=True, timeout=10)
        # Count how many node processes are running
        lines = result.stdout.strip().split("\n")
        node_count = len([line for line in lines if "node.exe" in line and "===" not in line])
        if node_count >= 1:
            return True, f"Node.js processes found ({node_count} dashboard service)"
        else:
            return False, "No Node.js processes found"
    except Exception as e:
        return False, str(e)

def main():
    print("🔍 Bldr Empire v2 - Service Status Checker")
    print("=" * 50)
    
    # Check API status
    print("Checking API server...")
    api_ok, api_status = check_api_status()
    print(f"  API Server: {'✅' if api_ok else '❌'} {api_status}")
    
    # Check Dashboard status
    print("Checking Dashboard...")
    dashboard_ok, dashboard_status = check_dashboard_status()
    print(f"  Dashboard:  {'✅' if dashboard_ok else '❌'} {dashboard_status}")
    
    # Check Python processes
    print("Checking Python processes...")
    python_ok, python_status = check_python_processes()
    print(f"  Python:     {'✅' if python_ok else '❌'} {python_status}")
    
    # Check Node processes
    print("Checking Node.js processes...")
    node_ok, node_status = check_node_processes()
    print(f"  Node.js:    {'✅' if node_ok else '❌'} {node_status}")
    
    print("\n" + "=" * 50)
    
    # Overall status
    all_ok = api_ok and dashboard_ok and python_ok and node_ok
    if all_ok:
        print("🎉 All Bldr Empire v2 services are running properly!")
        print("\nAccess your services at:")
        print("  API Server:      http://localhost:8000")
        print("  Dashboard:       http://localhost:5173")
    else:
        print("⚠️  Some services are not running properly.")
        print("   Please check the status details above.")
        print("   Try restarting the services with one_click_start.bat")

if __name__ == "__main__":
    main()