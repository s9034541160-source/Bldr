import tkinter as tk
from tkinter import ttk

def main():
    print("Creating root window...")
    root = tk.Tk()
    root.title("Minimal Test")
    root.geometry("300x200")
    
    label = ttk.Label(root, text="Hello, World!")
    label.pack(expand=True)
    
    print("Starting mainloop...")
    root.mainloop()
    print("Mainloop finished")

if __name__ == "__main__":
    main()