#!/usr/bin/env python3
"""
Bldr Empire v2 System Launcher
Главный файл для запуска системного лаунчера
"""

import sys
import os
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

try:
    from gui_launcher import BldrSystemLauncherGUI
    
    def main():
        """Главная функция запуска"""
        print("🏗️ Starting Bldr Empire v2 System Launcher...")
        
        try:
            launcher = BldrSystemLauncherGUI()
            launcher.run()
        except KeyboardInterrupt:
            print("\n👋 System Launcher stopped by user")
        except Exception as e:
            print(f"❌ Error starting System Launcher: {e}")
            sys.exit(1)
            
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("Please install required packages:")
    print("pip install requests psutil tkinter")
    sys.exit(1)