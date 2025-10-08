import tkinter as tk
from tkinter import ttk
import time

def main():
    print("Creating root window...")
    root = tk.Tk()
    root.title("Tkinter Test")
    root.geometry("400x300")
    root.deiconify()
    root.lift()
    root.focus_force()
    
    # Add some content
    label = ttk.Label(root, text="Hello, Tkinter!", font=("Arial", 16))
    label.pack(pady=20)
    
    button = ttk.Button(root, text="Close", command=root.destroy)
    button.pack(pady=10)
    
    print("Window created, should be visible now")
    print(f"Window title: {root.title()}")
    print(f"Window geometry: {root.geometry()}")
    
    # Force update
    root.update()
    
    try:
        root.mainloop()
        print("Mainloop finished")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()