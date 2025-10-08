import tkinter as tk
from tkinter import messagebox
import traceback

def main():
    try:
        print("Creating root window...")
        root = tk.Tk()
        root.title("Test")
        root.geometry("300x200")
        
        def on_closing():
            print("Window closing event triggered")
            try:
                result = messagebox.askokcancel("Quit", "Do you want to quit?")
                print(f"Message box result: {result}")
                if result:
                    print("User confirmed closing, destroying root")
                    root.destroy()
                else:
                    print("User cancelled closing")
            except Exception as e:
                print(f"Error in on_closing: {e}")
                traceback.print_exc()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        label = tk.Label(root, text="Test GUI")
        label.pack(pady=20)
        
        print("GUI created successfully")
        root.mainloop()
        print("GUI closed")
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting simple GUI test...")
    main()
    print("Simple GUI test completed")