# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: create_merge_template
# Основной источник: C:\Bldr\run_duplicate_elimination.py
# Дубликаты (для справки):
#   - C:\Bldr\function_merger_helper.py
#================================================================================
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