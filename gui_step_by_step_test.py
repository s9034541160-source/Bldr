import tkinter as tk
import traceback
import sys

def main():
    try:
        print("Step 1: Importing bldr_gui...")
        import bldr_gui
        print("Step 1: SUCCESS - bldr_gui imported")
        
        print("Step 2: Creating root window...")
        root = tk.Tk()
        print("Step 2: SUCCESS - Root window created")
        
        print("Step 3: Initializing BldrEmpireGUI...")
        app = bldr_gui.BldrEmpireGUI(root)
        print("Step 3: SUCCESS - BldrEmpireGUI initialized")
        
        print("Step 4: Starting mainloop...")
        root.mainloop()
        print("Step 4: SUCCESS - Mainloop completed")
        
    except Exception as e:
        print(f"Error at step: {e}")
        traceback.print_exc()
        # Also write to a file
        with open('gui_step_error.log', 'w', encoding='utf-8') as f:
            f.write(f"Error: {e}\n")
            f.write(traceback.format_exc())

if __name__ == "__main__":
    print("Starting GUI step-by-step test...")
    main()
    print("GUI step-by-step test completed")