from CANONICAL_FUNCTIONS.__init__ import __init__
#!/usr/bin/env python3
"""
Bldr System Launcher
Элегантное GUI-решение для запуска всей системы Bldr Empire
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import time
import json
import requests
import psutil
from pathlib import Path
import queue
import os
from datetime import datetime

class BldrSystemLauncher:
    """Главный лаунчер системы Bldr Empire"""
    
    """Главная функция"""
    launcher = BldrSystemLauncher()
    launcher.run()

if __name__ == "__main__":
    main()