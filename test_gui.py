import tkinter as tk
from tkinter import messagebox

def main():
    root = tk.Tk()
    root.title("Test GUI")
    root.geometry("300x200")
    
    label = tk.Label(root, text="Test GUI is running")
    label.pack(pady=20)
    
    def on_closing():
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()