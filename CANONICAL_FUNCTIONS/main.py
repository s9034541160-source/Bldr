# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: main
# Основной источник: C:\Bldr\system_launcher\main.py
# Дубликаты (для справки):
#   - C:\Bldr\analyze_duplicates.py
#   - C:\Bldr\batch_duplicate_processor.py
#   - C:\Bldr\bldr_gui.py
#   - C:\Bldr\bldr_system_launcher.py
#   - C:\Bldr\duplicate_elimination_workflow.py
#   - C:\Bldr\duplicate_file_manager.py
#   - C:\Bldr\emergency_full_reset.py
#   - C:\Bldr\find_duplicates.py
#   - C:\Bldr\full_automatic_duplicate_eliminator.py
#   - C:\Bldr\function_merger_helper.py
#   - C:\Bldr\interactive_rag_training.py
#   - C:\Bldr\monitor_training.py
#   - C:\Bldr\quick_status.py
#   - C:\Bldr\run_duplicate_elimination.py
#   - C:\Bldr\semi_automated_duplicate_eliminator.py
#   - C:\Bldr\verify_merged_functions.py
#   - C:\Bldr\scripts\generate_function_index.py
#   - C:\Bldr\system_launcher\gui_launcher.py
#================================================================================
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