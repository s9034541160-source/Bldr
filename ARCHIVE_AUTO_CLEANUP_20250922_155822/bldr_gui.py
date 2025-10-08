from CANONICAL_FUNCTIONS.__init__ import __init__
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import time
import os
import json
from pathlib import Path
import psutil
import requests
import platform
from queue import Queue
import traceback

class BldrEmpireGUI:
    try:
        print("Creating Tk root...")
        root = tk.Tk()
        print("Root window created")
        print(f"Root window geometry: {root.winfo_geometry()}")
        print(f"Root window position: {root.winfo_x()}, {root.winfo_y()}")
        
        # Ensure window is visible and properly positioned
        root.title("Bldr Empire v2 - Service Manager")
        root.geometry("800x600")
        root.deiconify()
        root.lift()
        root.focus_force()
        
        # Set window attributes to ensure visibility
        root.attributes('-topmost', True)
        root.after_idle(root.attributes, '-topmost', False)
        
        print("Creating BldrEmpireGUI...")
        app = BldrEmpireGUI(root)
        print("BldrEmpireGUI created successfully")
        print("Starting mainloop...")
        print(f"Window title: {root.title()}")
        print(f"Window size: {root.winfo_width()}x{root.winfo_height()}")
        
        # Force window to be visible
        root.update()
        root.deiconify()
        root.lift()
        root.focus_force()
        
        try:
            root.mainloop()
            print("Mainloop finished normally")
        except Exception as e:
            print(f"Mainloop error: {e}")
            import traceback
            traceback.print_exc()
            with open('mainloop_error.log', 'w') as f:
                f.write(f"Mainloop error: {e}\n")
                f.write(traceback.format_exc())
        print("Exiting main function")
    except Exception as e:
        import traceback
        error_msg = f"GUI Error: {str(e)}\n\n{traceback.format_exc()}"
        print(error_msg)
        with open('gui_error.log', 'w', encoding='utf-8') as f:
            f.write(error_msg)
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()