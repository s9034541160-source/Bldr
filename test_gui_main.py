import sys
import os
import traceback

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Testing bldr_gui main function...")
    import bldr_gui
    print("Import successful")
    
    # Test the main function
    print("Calling main()...")
    bldr_gui.main()
    print("Main function completed")
    
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
    with open('test_gui_main_error.log', 'w') as f:
        f.write(f"Error: {e}\n")
        f.write(traceback.format_exc())