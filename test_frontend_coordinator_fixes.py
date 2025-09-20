#!/usr/bin/env python3
"""
Test script to verify frontend coordinator configuration fixes.
This script checks that the frontend components are properly configured
with the updated coordinator settings.
"""

import os
import sys
import json
import re

def check_app_tsx():
    """Check that App.tsx includes the coordinator fix component."""
    app_path = "web/bldr_dashboard/src/App.tsx"
    if not os.path.exists(app_path):
        print("❌ App.tsx not found")
        return False
    
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if CoordinatorConfigFix is imported
    if "import CoordinatorConfigFix from './components/CoordinatorConfigFix'" not in content:
        print("❌ CoordinatorConfigFix not imported in App.tsx")
        return False
    
    # Check if coordinator-fix route is handled
    if "case 'coordinator-fix':" not in content:
        print("❌ coordinator-fix route not handled in App.tsx")
        return False
    
    # Check if coordinator-fix menu item exists
    if "key: 'coordinator-fix'" not in content:
        print("❌ coordinator-fix menu item not found in App.tsx")
        return False
    
    print("✅ App.tsx correctly configured")
    return True

def check_coordinator_config_fix():
    """Check that CoordinatorConfigFix.tsx exists and has correct content."""
    component_path = "web/bldr_dashboard/src/components/CoordinatorConfigFix.tsx"
    if not os.path.exists(component_path):
        print("❌ CoordinatorConfigFix.tsx not found")
        return False
    
    with open(component_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for configuration details
    if "qwen/qwen2.5-vl-7b" not in content:
        print("❌ Correct model not mentioned in CoordinatorConfigFix.tsx")
        return False
    
    if "Max Iterations: 4" not in content:
        print("❌ Correct max iterations not mentioned in CoordinatorConfigFix.tsx")
        return False
    
    if "3600 seconds (1 hour)" not in content:
        print("❌ Correct max execution time not mentioned in CoordinatorConfigFix.tsx")
        return False
    
    print("✅ CoordinatorConfigFix.tsx correctly configured")
    return True

def check_ai_shell():
    """Check that AIShell.tsx has the updated coordinator information."""
    component_path = "web/bldr_dashboard/src/components/AIShell.tsx"
    if not os.path.exists(component_path):
        print("❌ AIShell.tsx not found")
        return False
    
    with open(component_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for updated coordinator description
    if "Координатор (Qwen2.5-VL-7B)" not in content:
        print("❌ Updated coordinator model not found in AIShell.tsx")
        return False
    
    if "Максимум 4 итерации, 1 час выполнения" not in content:
        print("❌ Updated coordinator configuration not mentioned in AIShell.tsx")
        return False
    
    print("✅ AIShell.tsx correctly configured")
    return True

def check_api_service():
    """Check that api.ts has the correct timeout configuration."""
    service_path = "web/bldr_dashboard/src/services/api.ts"
    if not os.path.exists(service_path):
        print("❌ api.ts not found")
        return False
    
    with open(service_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for updated timeout (3600000 ms = 1 hour)
    if "timeout: 3600000" not in content:
        print("❌ Correct timeout not found in api.ts")
        return False
    
    print("✅ api.ts correctly configured")
    return True

def main():
    """Main test function."""
    print("Testing frontend coordinator configuration fixes...\n")
    
    tests = [
        check_app_tsx,
        check_coordinator_config_fix,
        check_ai_shell,
        check_api_service
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All frontend coordinator fixes are correctly implemented!")
        return 0
    else:
        print("❌ Some frontend coordinator fixes need attention!")
        return 1

if __name__ == "__main__":
    sys.exit(main())