import os
import sys

print("Path test started")
print(f"Current working directory: {os.getcwd()}")
print(f"Script location: {os.path.abspath(__file__)}")
print(f"Python path: {sys.path}")

# Check if bldr_gui.py exists
gui_file = os.path.join(os.getcwd(), "bldr_gui.py")
print(f"bldr_gui.py exists: {os.path.exists(gui_file)}")
print(f"bldr_gui.py path: {gui_file}")

# Try to import and check the file
try:
    import bldr_gui
    print("bldr_gui imported successfully")
    print(f"bldr_gui file: {bldr_gui.__file__}")
except Exception as e:
    print(f"Error importing bldr_gui: {e}")
    import traceback
    traceback.print_exc()

print("Path test completed")