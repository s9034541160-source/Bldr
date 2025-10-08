#!/usr/bin/env python3
"""
Main orchestration script for the complete duplicate elimination process.
This script provides a menu-driven interface to all duplicate elimination tools.
"""

import os
import sys
import subprocess
from datetime import datetime

def show_menu():
    """Display the main menu."""
    print("\n" + "="*60)
    print("🤖 BLDR EMPIRE - DUPLICATE ELIMINATION SYSTEM")
    print("="*60)
    print("1. Run Semi-Automated Duplicate Eliminator")
    print("2. Run Batch Processor (Analyze Multiple Functions)")
    print("3. Run Verification Suite")
    print("4. View Progress Report")
    print("5. Manual Function Processing")
    print("6. Help / Documentation")
    print("0. Exit")
    print("="*60)

def run_semi_automated_eliminator():
    """Run the semi-automated duplicate eliminator."""
    print("\n🚀 Launching Semi-Automated Duplicate Eliminator...")
    try:
        subprocess.run([sys.executable, "semi_automated_duplicate_eliminator.py"], 
                      cwd=r"C:\Bldr", check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running semi-automated eliminator: {e}")
    except FileNotFoundError:
        print("❌ semi_automated_duplicate_eliminator.py not found")

def run_batch_processor():
    """Run the batch processor."""
    print("\n🚀 Launching Batch Processor...")
    try:
        subprocess.run([sys.executable, "batch_duplicate_processor.py"], 
                      cwd=r"C:\Bldr", check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running batch processor: {e}")
    except FileNotFoundError:
        print("❌ batch_duplicate_processor.py not found")

def run_verification_suite():
    """Run the verification suite."""
    print("\n🚀 Launching Verification Suite...")
    try:
        subprocess.run([sys.executable, "verify_merged_functions.py"], 
                      cwd=r"C:\Bldr", check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running verification suite: {e}")
    except FileNotFoundError:
        print("❌ verify_merged_functions.py not found")

def view_progress_report():
    """View the current progress report."""
    print("\n📊 CURRENT PROGRESS REPORT")
    print("="*40)
    
    csv_file = "duplication_master_list_updated.csv"
    if not os.path.exists(csv_file):
        print("❌ Progress tracker not found")
        return
    
    # Import the workflow tool to get progress
    try:
        sys.path.append(r"C:\Bldr")
        from duplicate_elimination_workflow import load_duplicate_tracker
        
        duplicates = load_duplicate_tracker(csv_file)
        total = len(duplicates)
        pending = sum(1 for d in duplicates if d['Status'] == 'Pending')
        reviewed = sum(1 for d in duplicates if d['Status'] == 'Reviewed')
        merged = sum(1 for d in duplicates if d['Status'] == 'Merged')
        deleted = sum(1 for d in duplicates if d['Status'] == 'Deleted')
        verified = sum(1 for d in duplicates if d['Status'] == 'Verified')
        
        print(f"Total functions:      {total:3d}")
        print(f"Pending:             {pending:3d} ({pending/total*100:5.1f}%)")
        print(f"Reviewed:            {reviewed:3d} ({reviewed/total*100:5.1f}%)")
        print(f"Merged:              {merged:3d} ({merged/total*100:5.1f}%)")
        print(f"Deleted:             {deleted:3d} ({deleted/total*100:5.1f}%)")
        print(f"Verified:            {verified:3d} ({verified/total*100:5.1f}%)")
        
        # Show top priority functions
        pending_funcs = [d for d in duplicates if d['Status'] == 'Pending']
        pending_funcs.sort(key=lambda x: int(x['FileCount']), reverse=True)
        
        if pending_funcs:
            print(f"\n🔥 TOP PRIORITY FUNCTIONS:")
            for i, func in enumerate(pending_funcs[:5]):
                print(f"   {i+1}. {func['FunctionName']} ({func['FileCount']} duplicates)")
        
    except Exception as e:
        print(f"❌ Error loading progress report: {e}")

def manual_function_processing():
    """Manual function processing options."""
    while True:
        print("\n🔧 MANUAL FUNCTION PROCESSING")
        print("="*40)
        print("1. Compare Function Versions")
        print("2. Find Function References")
        print("3. Create Merge Template")
        print("4. Manage Duplicate Files")
        print("0. Back to Main Menu")
        
        choice = input("\nEnter your choice: ").strip()
        
        if choice == '1':
            compare_function_versions()
        elif choice == '2':
            find_function_references()
        elif choice == '3':
            create_merge_template()
        elif choice == '4':
            manage_duplicate_files()
        elif choice == '0':
            break
        else:
            print("❌ Invalid choice")

def compare_function_versions():
    """Manually compare function versions."""
    print("\n🔍 COMPARE FUNCTION VERSIONS")
    print("="*30)
    func_name = input("Enter function name: ").strip()
    if not func_name:
        print("❌ Function name required")
        return
    
    print("Note: You'll need to manually edit compare_function_versions.py")
    print("to add the function name and file paths, then run it.")
    
    # Offer to open the file for editing
    edit_choice = input("Open compare_function_versions.py for editing? (y/N): ").strip().lower()
    if edit_choice == 'y':
        try:
            os.startfile("compare_function_versions.py")
        except:
            print("❌ Could not open file for editing")

def find_function_references():
    """Manually find function references."""
    print("\n🔍 FIND FUNCTION REFERENCES")
    print("="*30)
    func_name = input("Enter function name: ").strip()
    if not func_name:
        print("❌ Function name required")
        return
    
    print("Note: You'll need to manually edit find_all_references.py")
    print("to add the function name, then run it.")
    
    # Offer to open the file for editing
    edit_choice = input("Open find_all_references.py for editing? (y/N): ").strip().lower()
    if edit_choice == 'y':
        try:
            os.startfile("find_all_references.py")
        except:
            print("❌ Could not open file for editing")

def create_merge_template():
    """Create a merge template."""
    print("\n🛠️  CREATE MERGE TEMPLATE")
    print("="*25)
    print("Note: You'll need to manually edit function_merger_helper.py")
    print("to add the function name and file paths, then run it.")
    
    # Offer to open the file for editing
    edit_choice = input("Open function_merger_helper.py for editing? (y/N): ").strip().lower()
    if edit_choice == 'y':
        try:
            os.startfile("function_merger_helper.py")
        except:
            print("❌ Could not open file for editing")

def manage_duplicate_files():
    """Manage duplicate files."""
    print("\n🗂️  MANAGE DUPLICATE FILES")
    print("="*25)
    print("Note: You'll need to manually edit duplicate_file_manager.py")
    print("to add the file paths, then run it.")
    
    # Offer to open the file for editing
    edit_choice = input("Open duplicate_file_manager.py for editing? (y/N): ").strip().lower()
    if edit_choice == 'y':
        try:
            os.startfile("duplicate_file_manager.py")
        except:
            print("❌ Could not open file for editing")

def show_help():
    """Show help documentation."""
    help_file = "DUPLICATE_ELIMINATION_README.md"
    if os.path.exists(help_file):
        print(f"\n📖 Opening {help_file}...")
        try:
            os.startfile(help_file)
        except:
            print("❌ Could not open help file")
            print("Please open DUPLICATE_ELIMINATION_README.md manually")
    else:
        print("❌ Help file not found")
        print("Please check that DUPLICATE_ELIMINATION_README.md exists")

def main():
    """Main orchestration function."""
    print("🤖 Bldr Empire Duplicate Elimination System")
    print("This system helps you eliminate 299 duplicate functions")
    print("across your codebase in a controlled, systematic way.")
    
    while True:
        show_menu()
        choice = input("\nEnter your choice: ").strip()
        
        if choice == '1':
            run_semi_automated_eliminator()
        elif choice == '2':
            run_batch_processor()
        elif choice == '3':
            run_verification_suite()
        elif choice == '4':
            view_progress_report()
        elif choice == '5':
            manual_function_processing()
        elif choice == '6':
            show_help()
        elif choice == '0':
            print("👋 Thank you for using the Bldr Empire Duplicate Elimination System!")
            break
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
