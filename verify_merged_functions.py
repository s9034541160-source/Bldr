#!/usr/bin/env python3
"""
Script to verify that merged functions work correctly after duplicate elimination.
This script helps ensure that the refactoring process didn't break anything.
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path

def test_import_file(file_path):
    """Test if a Python file can be imported without errors."""
    try:
        spec = importlib.util.spec_from_file_location("test_module", file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return True, "Import successful"
    except Exception as e:
        return False, str(e)
    return False, "Could not load module"

def test_function_exists(file_path, func_name):
    """Test if a function exists in a Python file."""
    try:
        spec = importlib.util.spec_from_file_location("test_module", file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return hasattr(module, func_name), f"Function '{func_name}' exists in module"
    except Exception as e:
        return False, str(e)
    return False, "Could not load module"

def run_basic_tests():
    """Run basic tests to verify system functionality."""
    tests = []
    
    # Test 1: Check if main GUI can be imported
    gui_file = r"C:\Bldr\bldr_gui.py"
    if os.path.exists(gui_file):
        success, msg = test_import_file(gui_file)
        tests.append(("GUI Import", success, msg))
    
    # Test 2: Check if core tools system can be imported
    tools_file = r"C:\Bldr\core\tools_system.py"
    if os.path.exists(tools_file):
        success, msg = test_import_file(tools_file)
        tests.append(("Tools System Import", success, msg))
    
    # Test 3: Check if coordinator can be imported
    coordinator_file = r"C:\Bldr\core\super_smart_coordinator.py"
    if os.path.exists(coordinator_file):
        success, msg = test_import_file(coordinator_file)
        tests.append(("Coordinator Import", success, msg))
    
    # Test 4: Check if backend can be imported
    backend_file = r"C:\Bldr\backend\main.py"
    if os.path.exists(backend_file):
        success, msg = test_import_file(backend_file)
        tests.append(("Backend Import", success, msg))
    
    return tests

def run_unit_tests():
    """Run existing unit tests if they exist."""
    test_files = [
        r"C:\Bldr\test_tools.py",
        r"C:\Bldr\core\test_main.py",
        r"C:\Bldr\tests\test_comprehensive.py"
    ]
    
    results = []
    
    for test_file in test_files:
        if os.path.exists(test_file):
            try:
                # Try to run the test file
                result = subprocess.run(
                    [sys.executable, test_file], 
                    capture_output=True, 
                    text=True, 
                    timeout=30
                )
                success = result.returncode == 0
                msg = f"Exit code: {result.returncode}"
                if result.stdout:
                    msg += f"\nStdout: {result.stdout[:200]}..."
                if result.stderr:
                    msg += f"\nStderr: {result.stderr[:200]}..."
                results.append((os.path.basename(test_file), success, msg))
            except subprocess.TimeoutExpired:
                results.append((os.path.basename(test_file), False, "Test timed out"))
            except Exception as e:
                results.append((os.path.basename(test_file), False, str(e)))
    
    return results

def check_file_references():
    """Check that files referenced in the CSV still exist."""
    import csv
    
    csv_files = [
        "duplication_master_list.csv",
        "duplication_master_list_updated.csv"
    ]
    
    missing_files = []
    
    for csv_file in csv_files:
        if not os.path.exists(csv_file):
            continue
            
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Check primary file
                if row['ChosenPrimaryFile'] and not os.path.exists(row['ChosenPrimaryFile']):
                    missing_files.append({
                        'function': row['FunctionName'],
                        'file': row['ChosenPrimaryFile'],
                        'type': 'primary'
                    })
                
                # Check files in FileList
                file_list = row['FileList'].split(';') if row['FileList'] else []
                for file_path in file_list:
                    if file_path and not os.path.exists(file_path):
                        missing_files.append({
                            'function': row['FunctionName'],
                            'file': file_path,
                            'type': 'duplicate'
                        })
    
    return missing_files

def main():
    """Main verification function."""
    print("🔍 Bldr Empire - Post-Merge Verification")
    print("=" * 50)
    
    # Run basic import tests
    print("\n🧪 Basic Import Tests:")
    print("-" * 30)
    import_tests = run_basic_tests()
    
    passed_imports = 0
    for test_name, success, msg in import_tests:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {msg}")
        if success:
            passed_imports += 1
    
    # Run unit tests
    print("\n📋 Unit Tests:")
    print("-" * 30)
    unit_tests = run_unit_tests()
    
    passed_unit = 0
    for test_name, success, msg in unit_tests:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {msg}")
        if success:
            passed_unit += 1
    
    # Check file references
    print("\n📁 File Reference Check:")
    print("-" * 30)
    missing_files = check_file_references()
    
    if missing_files:
        print(f"❌ Found {len(missing_files)} missing files:")
        for mf in missing_files:
            print(f"   - {mf['file']} (for function {mf['function']}, {mf['type']} file)")
    else:
        print("✅ All referenced files exist")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 50)
    print(f"Import Tests:     {passed_imports}/{len(import_tests)} passed")
    print(f"Unit Tests:       {passed_unit}/{len(unit_tests)} passed")
    print(f"Missing Files:    {len(missing_files)} files missing")
    
    overall_success = (
        passed_imports == len(import_tests) and 
        len(missing_files) == 0
    )
    
    if overall_success:
        print("\n🎉 Overall: System appears to be working correctly!")
        print("   You can proceed with confidence to the next functions.")
    else:
        print("\n⚠️  Overall: Some issues detected.")
        print("   Please review the errors above before proceeding.")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)