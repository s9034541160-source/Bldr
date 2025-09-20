import tkinter as tk
from tkinter import messagebox

def main():
    print("Creating root window...")
    root = tk.Tk()
    root.title("Test")
    root.geometry("300x200")
    
    label = tk.Label(root, text="Test GUI")
    label.pack(pady=20)
    
    print("GUI created successfully")
    root.mainloop()
    print("GUI closed")

if __name__ == "__main__":
    print("Starting simple GUI test...")
    main()
    print("Simple GUI test completed")