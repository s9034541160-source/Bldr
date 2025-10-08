# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: create_widgets
# Основной источник: C:\Bldr\bldr_gui.py
# Дубликаты (для справки):
#   - C:\Bldr\bldr_gui_manager.py
#================================================================================
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nesw")
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Bldr Empire v2 - Service Manager", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=3, pady=(0, 20), sticky="ew")
        
        self.start_button = ttk.Button(button_frame, text="▶ Start All Services", 
                                      command=self.start_all_services)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="⏹ Stop All Services", 
                                     command=self.stop_all_services)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.refresh_button = ttk.Button(button_frame, text="🔄 Refresh Status", 
                                        command=self.update_status)
        self.refresh_button.pack(side=tk.LEFT)
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Service Status", padding="10")
        status_frame.grid(row=2, column=0, columnspan=2, sticky="nesw", pady=(0, 10))
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(0, weight=1)
        
        # Status treeview
        self.status_tree = ttk.Treeview(status_frame, columns=("Status", "Port"), show="tree headings")
        self.status_tree.heading("#0", text="Service")
        self.status_tree.heading("Status", text="Status")
        self.status_tree.heading("Port", text="Port")
        self.status_tree.column("#0", width=150)
        self.status_tree.column("Status", width=150)
        self.status_tree.column("Port", width=100)
        
        # Scrollbar for treeview
        status_scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.status_tree.yview)
        self.status_tree.configure(yscrollcommand=status_scrollbar.set)
        
        self.status_tree.grid(row=0, column=0, sticky="nesw")
        status_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Populate initial status
        for service_name in self.services:
            port = self.services[service_name]["port"] if self.services[service_name]["port"] else "N/A"
            self.status_tree.insert("", "end", iid=service_name, text=service_name, 
                                   values=(self.services[service_name]["status"], port))
        
        # Log frame
        log_frame = ttk.LabelFrame(main_frame, text="Logs", padding="10")
        log_frame.grid(row=3, column=0, columnspan=2, sticky="nesw", pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, state=tk.DISABLED)
        self.log_text.grid(row=0, column=0, sticky="nesw")
        
        # Clear log button
        clear_log_button = ttk.Button(log_frame, text="Clear Logs", command=self.clear_logs)
        clear_log_button.grid(row=1, column=0, pady=(5, 0))