print("Testing imports...")

try:
    import tkinter as tk
    print("tkinter imported successfully")
except Exception as e:
    print(f"Error importing tkinter: {e}")

try:
    from tkinter import ttk, scrolledtext, messagebox
    print("ttk, scrolledtext, messagebox imported successfully")
except Exception as e:
    print(f"Error importing ttk, scrolledtext, messagebox: {e}")

try:
    import subprocess
    print("subprocess imported successfully")
except Exception as e:
    print(f"Error importing subprocess: {e}")

try:
    import threading
    print("threading imported successfully")
except Exception as e:
    print(f"Error importing threading: {e}")

try:
    import time
    print("time imported successfully")
except Exception as e:
    print(f"Error importing time: {e}")

try:
    import os
    print("os imported successfully")
except Exception as e:
    print(f"Error importing os: {e}")

try:
    import json
    print("json imported successfully")
except Exception as e:
    print(f"Error importing json: {e}")

try:
    from pathlib import Path
    print("Path imported successfully")
except Exception as e:
    print(f"Error importing Path: {e}")

try:
    import psutil
    print("psutil imported successfully")
except Exception as e:
    print(f"Error importing psutil: {e}")

try:
    import requests
    print("requests imported successfully")
except Exception as e:
    print(f"Error importing requests: {e}")

print("Import test completed")