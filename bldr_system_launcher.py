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
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🏗️ Bldr Empire v2 - System Launcher")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Состояние компонентов
        self.components = {
            'neo4j': {'status': 'stopped', 'pid': None, 'port': 7474},
            'qdrant': {'status': 'stopped', 'pid': None, 'port': 6333},
            'backend': {'status': 'stopped', 'pid': None, 'port': 8000},
            'frontend': {'status': 'stopped', 'pid': None, 'port': 5173},
            'rag_training': {'status': 'stopped', 'pid': None, 'progress': 0}
        }
        
        # Процессы
        self.processes = {}
        
        # Очередь для логов
        self.log_queue = queue.Queue()
        
        self.setup_ui()
        self.start_monitoring()

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        
        # Главный фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="🏗️ Bldr Empire v2 - System Control Center", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Левая панель - компоненты
        self.setup_components_panel(main_frame)
        
        # Центральная панель - логи
        self.setup_logs_panel(main_frame)
        
        # Правая панель - управление
        self.setup_control_panel(main_frame)
        
        # Нижняя панель - статус
        self.setup_status_panel(main_frame)

    def setup_components_panel(self, parent):
        """Панель состояния компонентов"""
        
        components_frame = ttk.LabelFrame(parent, text="📊 System Components", padding="10")
        components_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        self.component_labels = {}
        self.component_buttons = {}
        
        row = 0
        for component, info in self.components.items():
            # Название компонента
            name_label = ttk.Label(components_frame, text=f"🔧 {component.upper()}", 
                                  font=('Arial', 10, 'bold'))
            name_label.grid(row=row, column=0, sticky=tk.W, pady=2)
            
            # Статус
            status_label = ttk.Label(components_frame, text="⚫ STOPPED", 
                                   foreground='red')
            status_label.grid(row=row, column=1, sticky=tk.W, padx=(10, 0), pady=2)
            self.component_labels[component] = status_label
            
            # Кнопка управления
            btn_frame = ttk.Frame(components_frame)
            btn_frame.grid(row=row, column=2, sticky=tk.E, padx=(10, 0), pady=2)
            
            start_btn = ttk.Button(btn_frame, text="▶️ Start", width=8,
                                  command=lambda c=component: self.start_component(c))
            start_btn.pack(side=tk.LEFT, padx=(0, 5))
            
            stop_btn = ttk.Button(btn_frame, text="⏹️ Stop", width=8,
                                 command=lambda c=component: self.stop_component(c))
            stop_btn.pack(side=tk.LEFT)
            
            self.component_buttons[component] = {'start': start_btn, 'stop': stop_btn}
            
            row += 1
        
        # Кнопки массового управления
        ttk.Separator(components_frame, orient='horizontal').grid(row=row, column=0, columnspan=3, 
                                                                 sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        mass_frame = ttk.Frame(components_frame)
        mass_frame.grid(row=row, column=0, columnspan=3, pady=5)
        
        ttk.Button(mass_frame, text="🚀 Start All", 
                  command=self.start_all_components).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(mass_frame, text="⏹️ Stop All", 
                  command=self.stop_all_components).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(mass_frame, text="🔄 Restart All", 
                  command=self.restart_all_components).pack(side=tk.LEFT)

    def setup_logs_panel(self, parent):
        """Панель логов"""
        
        logs_frame = ttk.LabelFrame(parent, text="📝 System Logs", padding="10")
        logs_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Текстовое поле для логов
        self.log_text = scrolledtext.ScrolledText(logs_frame, width=60, height=25, 
                                                 font=('Consolas', 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Кнопки управления логами
        log_buttons_frame = ttk.Frame(logs_frame)
        log_buttons_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Button(log_buttons_frame, text="🗑️ Clear", 
                  command=self.clear_logs).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(log_buttons_frame, text="💾 Save", 
                  command=self.save_logs).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(log_buttons_frame, text="🔄 Auto-scroll", 
                  command=self.toggle_autoscroll).pack(side=tk.LEFT)
        
        self.autoscroll = True

    def setup_control_panel(self, parent):
        """Панель управления"""
        
        control_frame = ttk.LabelFrame(parent, text="🎛️ Control Panel", padding="10")
        control_frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # RAG Training Control
        rag_frame = ttk.LabelFrame(control_frame, text="🧠 RAG Training", padding="10")
        rag_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.rag_progress = ttk.Progressbar(rag_frame, mode='determinate')
        self.rag_progress.pack(fill=tk.X, pady=(0, 10))
        
        self.rag_status_label = ttk.Label(rag_frame, text="Status: Idle")
        self.rag_status_label.pack(anchor=tk.W)
        
        rag_buttons_frame = ttk.Frame(rag_frame)
        rag_buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(rag_buttons_frame, text="🚀 Start Training", 
                  command=self.start_rag_training).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(rag_buttons_frame, text="⏸️ Pause", 
                  command=self.pause_rag_training).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(rag_buttons_frame, text="⏹️ Stop", 
                  command=self.stop_rag_training).pack(side=tk.LEFT)
        
        # Quick Actions
        actions_frame = ttk.LabelFrame(control_frame, text="⚡ Quick Actions", padding="10")
        actions_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(actions_frame, text="🌐 Open Frontend", 
                  command=lambda: self.open_url("http://localhost:5173")).pack(fill=tk.X, pady=2)
        ttk.Button(actions_frame, text="🔧 Open Backend API", 
                  command=lambda: self.open_url("http://localhost:8000/docs")).pack(fill=tk.X, pady=2)
        ttk.Button(actions_frame, text="🗄️ Open Neo4j Browser", 
                  command=lambda: self.open_url("http://localhost:7474")).pack(fill=tk.X, pady=2)
        ttk.Button(actions_frame, text="📊 Open Qdrant Dashboard", 
                  command=lambda: self.open_url("http://localhost:6333/dashboard")).pack(fill=tk.X, pady=2)
        
        # System Actions
        system_frame = ttk.LabelFrame(control_frame, text="🛠️ System Actions", padding="10")
        system_frame.pack(fill=tk.X)
        
        ttk.Button(system_frame, text="☢️ Nuclear Reset", 
                  command=self.nuclear_reset).pack(fill=tk.X, pady=2)
        ttk.Button(system_frame, text="📁 Open File Manager", 
                  command=self.open_file_manager).pack(fill=tk.X, pady=2)
        ttk.Button(system_frame, text="📋 System Report", 
                  command=self.generate_system_report).pack(fill=tk.X, pady=2)

    def setup_status_panel(self, parent):
        """Панель статуса"""
        
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.status_label = ttk.Label(status_frame, text="🔴 System Idle", 
                                     font=('Arial', 10, 'bold'))
        self.status_label.pack(side=tk.LEFT)
        
        self.time_label = ttk.Label(status_frame, text="")
        self.time_label.pack(side=tk.RIGHT)
        
        # Обновляем время каждую секунду
        self.update_time()

    def log(self, message: str, level: str = "INFO"):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        self.log_queue.put(log_entry)
        
        # Обновляем UI в главном потоке
        self.root.after(0, self.update_log_display)

    def update_log_display(self):
        """Обновление отображения логов"""
        try:
            while True:
                log_entry = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, log_entry)
                
                if self.autoscroll:
                    self.log_text.see(tk.END)
                    
        except queue.Empty:
            pass

    def update_time(self):
        """Обновление времени"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)

    def start_monitoring(self):
        """Запуск мониторинга компонентов"""
        def monitor():
            while True:
                self.check_components_status()
                time.sleep(5)
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()

    def check_components_status(self):
        """Проверка статуса всех компонентов"""
        
        # Проверяем Neo4j
        try:
            response = requests.get("http://localhost:7474", timeout=2)
            if response.status_code == 200:
                self.update_component_status('neo4j', 'running', '🟢 RUNNING')
            else:
                self.update_component_status('neo4j', 'error', '🟡 ERROR')
        except:
            self.update_component_status('neo4j', 'stopped', '🔴 STOPPED')
        
        # Проверяем Qdrant
        try:
            response = requests.get("http://localhost:6333/health", timeout=2)
            if response.status_code == 200:
                self.update_component_status('qdrant', 'running', '🟢 RUNNING')
            else:
                self.update_component_status('qdrant', 'error', '🟡 ERROR')
        except:
            self.update_component_status('qdrant', 'stopped', '🔴 STOPPED')
        
        # Проверяем Backend
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                self.update_component_status('backend', 'running', '🟢 RUNNING')
            else:
                self.update_component_status('backend', 'error', '🟡 ERROR')
        except:
            self.update_component_status('backend', 'stopped', '🔴 STOPPED')
        
        # Проверяем Frontend
        try:
            response = requests.get("http://localhost:5173", timeout=2)
            if response.status_code == 200:
                self.update_component_status('frontend', 'running', '🟢 RUNNING')
            else:
                self.update_component_status('frontend', 'error', '🟡 ERROR')
        except:
            self.update_component_status('frontend', 'stopped', '🔴 STOPPED')

    def update_component_status(self, component: str, status: str, display_text: str):
        """Обновление статуса компонента"""
        if component in self.component_labels:
            self.component_labels[component].config(text=display_text)
            
            # Обновляем цвет
            if 'RUNNING' in display_text:
                self.component_labels[component].config(foreground='green')
            elif 'ERROR' in display_text:
                self.component_labels[component].config(foreground='orange')
            else:
                self.component_labels[component].config(foreground='red')
        
        self.components[component]['status'] = status

    def start_component(self, component: str):
        """Запуск компонента"""
        self.log(f"Starting {component}...")
        
        def start_in_thread():
            try:
                if component == 'neo4j':
                    self.start_neo4j()
                elif component == 'qdrant':
                    self.start_qdrant()
                elif component == 'backend':
                    self.start_backend()
                elif component == 'frontend':
                    self.start_frontend()
                elif component == 'rag_training':
                    self.start_rag_training()
            except Exception as e:
                self.log(f"Error starting {component}: {e}", "ERROR")
        
        threading.Thread(target=start_in_thread, daemon=True).start()

    def stop_component(self, component: str):
        """Остановка компонента"""
        self.log(f"Stopping {component}...")
        
        if component in self.processes and self.processes[component]:
            try:
                self.processes[component].terminate()
                self.processes[component] = None
                self.log(f"{component} stopped")
            except Exception as e:
                self.log(f"Error stopping {component}: {e}", "ERROR")

    def start_neo4j(self):
        """Запуск Neo4j"""
        neo4j_paths = [
            r"C:\Users\%USERNAME%\AppData\Local\Programs\Neo4j Desktop\Neo4j Desktop.exe",
            r"C:\Program Files\Neo4j Desktop\Neo4j Desktop.exe"
        ]
        
        for path in neo4j_paths:
            expanded_path = os.path.expandvars(path)
            if os.path.exists(expanded_path):
                subprocess.Popen([expanded_path], shell=True)
                self.log("Neo4j Desktop started")
                return
        
        self.log("Neo4j Desktop not found", "ERROR")

    def start_qdrant(self):
        """Запуск Qdrant"""
        try:
            # Пытаемся запустить Qdrant через Docker или прямо
            process = subprocess.Popen(
                ["qdrant", "--config-path", "./qdrant_config.yaml"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            self.processes['qdrant'] = process
            self.log("Qdrant started")
        except Exception as e:
            self.log(f"Failed to start Qdrant: {e}", "ERROR")

    def start_backend(self):
        """Запуск Backend"""
        try:
            process = subprocess.Popen(
                ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            self.processes['backend'] = process
            self.log("Backend started on port 8000")
        except Exception as e:
            self.log(f"Failed to start backend: {e}", "ERROR")

    def start_frontend(self):
        """Запуск Frontend"""
        try:
            frontend_dir = Path("web/bldr_dashboard")
            if frontend_dir.exists():
                process = subprocess.Popen(
                    ["npm", "run", "dev"],
                    cwd=str(frontend_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                self.processes['frontend'] = process
                self.log("Frontend started on port 5173")
            else:
                self.log("Frontend directory not found", "ERROR")
        except Exception as e:
            self.log(f"Failed to start frontend: {e}", "ERROR")

    def start_rag_training(self):
        """Запуск RAG обучения"""
        try:
            process = subprocess.Popen(
                ["python", "enterprise_rag_trainer_safe.py", "--custom_dir", "I:/docs/downloaded", "--fast_mode"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            self.processes['rag_training'] = process
            self.log("RAG Training started")
        except Exception as e:
            self.log(f"Failed to start RAG training: {e}", "ERROR")

    def start_all_components(self):
        """Запуск всех компонентов"""
        self.log("Starting all components...", "INFO")
        
        # Запускаем в правильном порядке
        components_order = ['neo4j', 'qdrant', 'backend', 'frontend']
        
        for component in components_order:
            self.start_component(component)
            time.sleep(2)  # Небольшая задержка между запусками

    def stop_all_components(self):
        """Остановка всех компонентов"""
        self.log("Stopping all components...", "INFO")
        
        for component in self.components.keys():
            self.stop_component(component)

    def restart_all_components(self):
        """Перезапуск всех компонентов"""
        self.log("Restarting all components...", "INFO")
        self.stop_all_components()
        time.sleep(5)
        self.start_all_components()

    def nuclear_reset(self):
        """Ядерный сброс системы"""
        result = messagebox.askyesno(
            "Nuclear Reset", 
            "⚠️ WARNING: This will delete ALL trained data!\n\n"
            "Are you sure you want to perform a nuclear reset?"
        )
        
        if result:
            self.log("NUCLEAR RESET INITIATED", "WARNING")
            
            def reset_in_thread():
                try:
                    subprocess.run(["python", "emergency_full_reset.py"], check=True)
                    self.log("Nuclear reset completed", "INFO")
                except Exception as e:
                    self.log(f"Nuclear reset failed: {e}", "ERROR")
            
            threading.Thread(target=reset_in_thread, daemon=True).start()

    def open_url(self, url: str):
        """Открытие URL в браузере"""
        import webbrowser
        webbrowser.open(url)
        self.log(f"Opened: {url}")

    def open_file_manager(self):
        """Открытие файлового менеджера"""
        os.startfile("I:/docs")
        self.log("File manager opened")

    def generate_system_report(self):
        """Генерация отчета о системе"""
        self.log("Generating system report...")
        
        def generate_in_thread():
            try:
                subprocess.run(["python", "database_reset_report.py"], check=True)
                self.log("System report generated")
            except Exception as e:
                self.log(f"Failed to generate report: {e}", "ERROR")
        
        threading.Thread(target=generate_in_thread, daemon=True).start()

    def clear_logs(self):
        """Очистка логов"""
        self.log_text.delete(1.0, tk.END)

    def save_logs(self):
        """Сохранение логов"""
        logs_content = self.log_text.get(1.0, tk.END)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"bldr_system_logs_{timestamp}.txt"
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(logs_content)
        
        self.log(f"Logs saved to: {log_file}")

    def toggle_autoscroll(self):
        """Переключение автопрокрутки"""
        self.autoscroll = not self.autoscroll
        self.log(f"Autoscroll: {'ON' if self.autoscroll else 'OFF'}")

    def run(self):
        """Запуск лаунчера"""
        self.log("🏗️ Bldr Empire v2 System Launcher started")
        self.log("Monitoring system components...")
        
        self.root.mainloop()

def main():
    """Главная функция"""
    launcher = BldrSystemLauncher()
    launcher.run()

if __name__ == "__main__":
    main()