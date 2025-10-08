# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: stop_all_services
# Основной источник: C:\Bldr\bldr_gui.py
# Дубликаты (для справки):
#   - C:\Bldr\bldr_gui_manager.py
#================================================================================
    def stop_all_services(self):
        """Stop all Bldr Empire services"""
        try:
            self.log_message("Stop All button clicked")
            if self.stop_thread and self.stop_thread.is_alive():
                self.log_message("Services are already stopping. Please wait.")
                return
                
            self.log_message("Stopping all Bldr Empire services...")
            self.root.after(0, lambda: self.stop_button.config(state=tk.DISABLED))
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
            
            # Run the stop script in a separate thread
            self.stop_thread = threading.Thread(target=self._stop_services_thread, daemon=True)
            self.stop_thread.start()
        except Exception as e:
            self.log_message(f"Error in stop_all_services: {e}")
            self.log_message(f"stop_all_services error traceback: {traceback.format_exc()}")
            self.root.after(0, lambda: self.stop_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))