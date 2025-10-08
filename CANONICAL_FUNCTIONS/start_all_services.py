# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: start_all_services
# Основной источник: C:\Bldr\bldr_gui.py
# Дубликаты (для справки):
#   - C:\Bldr\bldr_gui_manager.py
#================================================================================
    def start_all_services(self):
        """Start all Bldr Empire services"""
        try:
            self.log_message("Start All button clicked")
            if self.start_thread and self.start_thread.is_alive():
                self.log_message("Services are already starting. Please wait.")
                return
                
            self.log_message("Starting all Bldr Empire services...")
            self.root.after(0, lambda: self.start_button.config(state=tk.DISABLED))
            self.root.after(0, lambda: self.stop_button.config(state=tk.NORMAL))
            
            # Run the start script in a separate thread
            self.start_thread = threading.Thread(target=self._start_services_thread, daemon=True)
            self.start_thread.start()
            self.log_message("Start thread initiated successfully")
        except Exception as e:
            self.log_message(f"Error in start_all_services: {e}")
            self.log_message(f"start_all_services error traceback: {traceback.format_exc()}")
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_button.config(state=tk.NORMAL))