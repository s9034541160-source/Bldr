import bldr_gui
import tkinter as tk

print("Starting GUI test...")
try:
    root = tk.Tk()
    app = bldr_gui.BldrEmpireGUI(root)
    print("GUI initialized successfully")
    # Run for a short time then exit
    root.after(3000, root.destroy)  # Close after 3 seconds
    root.mainloop()
    print("GUI test completed")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()