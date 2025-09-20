import tkinter as tk
import traceback

print("Testing GUI initialization...")

try:
    print("Importing bldr_gui...")
    import bldr_gui
    print("bldr_gui imported successfully")
    
    print("Creating root window...")
    root = tk.Tk()
    print("Root window created successfully")
    
    print("Initializing BldrEmpireGUI...")
    app = bldr_gui.BldrEmpireGUI(root)
    print("BldrEmpireGUI initialized successfully")
    
    print("Starting mainloop...")
    root.mainloop()
    print("Mainloop completed")
    
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()

print("GUI initialization test completed")