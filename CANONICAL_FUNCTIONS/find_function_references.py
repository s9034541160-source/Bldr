# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: find_function_references
# Основной источник: C:\Bldr\run_duplicate_elimination.py
# Дубликаты (для справки):
#   - C:\Bldr\find_all_references.py
#   - C:\Bldr\semi_automated_duplicate_eliminator.py
#================================================================================
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