import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import traceback

def main():
    try:
        print("Creating root window...")
        root = tk.Tk()
        root.title("Simple Test")
        root.geometry("400x300")
        
        # Create a simple label
        label = ttk.Label(root, text="Simple Tkinter Test")
        label.pack(pady=20)
        
        # Create a text area
        text_area = scrolledtext.ScrolledText(root, height=10)
        text_area.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        text_area.insert(tk.END, "This is a test\n")
        text_area.config(state=tk.DISABLED)
        
        # Create a button
        def on_button_click():
            print("Button clicked")
            text_area.config(state=tk.NORMAL)
            text_area.insert(tk.END, "Button clicked\n")
            text_area.config(state=tk.DISABLED)
            text_area.see(tk.END)
        
        button = ttk.Button(root, text="Click Me", command=on_button_click)
        button.pack(pady=10)
        
        def on_closing():
            print("Window closing event")
            if messagebox.askokcancel("Quit", "Do you want to quit?"):
                print("User confirmed quit")
                root.destroy()
            else:
                print("User cancelled quit")
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        print("Starting mainloop...")
        root.mainloop()
        print("Mainloop finished")
        
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting simple Tkinter test...")
    main()
    print("Simple Tkinter test finished")