#!/usr/bin/env python3
"""
Test GUI Launcher
Тестирование обновленного GUI launcher
"""

import sys
from pathlib import Path

# Добавляем путь к system_launcher
sys.path.insert(0, str(Path(__file__).parent / 'system_launcher'))

try:
    from gui_launcher import BldrSystemLauncherGUI
    
    def main():
        """Тестовый запуск GUI launcher"""
        print("🏗️ Testing Bldr Empire v2 System Launcher...")
        print("Components that will be managed:")
        
        # Создаем экземпляр для проверки компонентов
        from component_manager import SystemComponentManager
        manager = SystemComponentManager()
        
        components = manager.get_all_components()
        for comp_id, component in components.items():
            deps = ', '.join(component.dependencies) if component.dependencies else 'None'
            port_info = f":{component.port}" if component.port else ""
            print(f"  - {component.name}{port_info} (deps: {deps})")
        
        print(f"\nTotal components: {len(components)}")
        print("\nStarting GUI...")
        
        try:
            launcher = BldrSystemLauncherGUI()
            launcher.run()
        except KeyboardInterrupt:
            print("\n👋 GUI stopped by user")
        except Exception as e:
            print(f"❌ Error running GUI: {e}")
            
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("Please install required packages:")
    print("pip install requests psutil tkinter")
    sys.exit(1)