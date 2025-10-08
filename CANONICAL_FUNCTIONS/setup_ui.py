# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: setup_ui
# Основной источник: C:\Bldr\system_launcher\gui_launcher.py
# Дубликаты (для справки):
#   - C:\Bldr\bldr_system_launcher.py
#================================================================================
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        
        # Заголовок
        self._create_header()
        
        # Основной контейнер
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Левая панель - компоненты
        left_frame = tk.Frame(main_frame, bg='#34495e', relief='raised', bd=2)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        self._create_components_panel(left_frame)
        
        # Правая панель - логи и мониторинг
        right_frame = tk.Frame(main_frame, bg='#34495e', relief='raised', bd=2)
        right_frame.pack(side='right', fill='both', expand=True)
        
        self._create_monitoring_panel(right_frame)
        
        # Статус бар
        self._create_status_bar()