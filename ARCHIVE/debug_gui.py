import sys
import traceback

try:
    import bldr_gui
    print("Successfully imported bldr_gui")
    bldr_gui.main()
except Exception as e:
    print(f"Error running GUI: {e}")
    traceback.print_exc()
    input("Press Enter to exit...")