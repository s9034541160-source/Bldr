#!/usr/bin/env python3
"""
GUI System Launcher
Графический интерфейс для управления компонентами системы Bldr Empire v2
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional
import webbrowser
import os
import sys
from pathlib import Path

# Добавляем путь к component_manager
sys.path.append(str(Path(__file__).parent))
from component_manager import SystemComponentManager, ComponentStatus, HealthStatus

class BldrSystemLauncherGUI:
    """Графический интерфейс для запуска системы Bldr Empire"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Bldr Empire v2 - System Launcher")
        self.root.geometry("1200x800")  # Уменьшаем размер окна
        self.root.configure(bg='#2c3e50')
        
        # Менеджер компонентов
        self.component_manager = SystemComponentManager()
        self.component_manager.add_status_callback(self._on_component_status_change)
        
        # GUI элементы
        self.component_frames = {}
        self.status_labels = {}
        self.control_buttons = {}
        self.log_text = None
        self.status_bar_label = None
        self.time_label = None
        
        # Состояние
        self.auto_refresh = True
        self.refresh_interval = 2  # секунды
        self.gui_update_thread = None
        self.is_running = True
        
        self.setup_ui()
        self.start_monitoring()
        
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
        
    def _create_header(self):
        """Создание заголовка"""
        title_frame = tk.Frame(self.root, bg='#2c3e50')
        title_frame.pack(fill='x', padx=20, pady=10)
        
        title_label = tk.Label(
            title_frame, 
            text="🏗️ Bldr Empire v2 - System Control Center",
            font=('Arial', 20, 'bold'),
            fg='#ecf0f1',
            bg='#2c3e50'
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame,
            text="Unified Construction Intelligence Platform",
            font=('Arial', 12),
            fg='#bdc3c7',
            bg='#2c3e50'
        )
        subtitle_label.pack()
        
    def _create_components_panel(self, parent):
        """Создание панели компонентов"""
        components_label = tk.Label(
            parent,
            text="🔧 System Components",
            font=('Arial', 14, 'bold'),
            fg='#ecf0f1',
            bg='#34495e'
        )
        components_label.pack(pady=10)
        
        # Глобальные кнопки управления
        global_control_frame = tk.Frame(parent, bg='#34495e')
        global_control_frame.pack(fill='x', padx=10, pady=10)
        
        start_all_btn = tk.Button(
            global_control_frame,
            text="🚀 Start All Systems",
            font=('Arial', 12, 'bold'),
            bg='#27ae60',
            fg='white',
            command=self._start_all_systems,
            relief='flat',
            padx=20,
            pady=10
        )
        start_all_btn.pack(fill='x', pady=5)
        
        stop_all_btn = tk.Button(
            global_control_frame,
            text="🛑 Stop All Systems",
            font=('Arial', 12, 'bold'),
            bg='#e74c3c',
            fg='white',
            command=self._stop_all_systems,
            relief='flat',
            padx=20,
            pady=10
        )
        stop_all_btn.pack(fill='x', pady=5)
        
        # Разделитель
        separator = tk.Frame(parent, height=2, bg='#2c3e50')
        separator.pack(fill='x', padx=10, pady=10)
        
        # Компоненты системы с прокруткой
        components_container = tk.Frame(parent, bg='#34495e')
        components_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Создаем Canvas и Scrollbar
        canvas = tk.Canvas(components_container, bg='#34495e', highlightthickness=0)
        scrollbar = tk.Scrollbar(components_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#34495e')
        
        # Настройка прокрутки
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Упаковка элементов прокрутки
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Создаем панели компонентов внутри scrollable_frame
        for component_id, component in self.component_manager.get_all_components().items():
            self._create_component_panel(scrollable_frame, component_id, component)
            
        # Добавляем прокрутку колесом мыши
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Обработка выхода из области прокрутки
        def _on_leave(event):
            canvas.unbind_all("<MouseWheel>")
            
        canvas.bind("<Leave>", _on_leave)
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        
    def _create_component_panel(self, parent, component_id: str, component):
        """Создание панели отдельного компонента"""
        
        frame = tk.Frame(parent, bg='#2c3e50', relief='raised', bd=1)
        frame.pack(fill='x', pady=3)  # Уменьшаем отступы
        
        self.component_frames[component_id] = frame
        
        # Заголовок и статус
        header_frame = tk.Frame(frame, bg='#2c3e50')
        header_frame.pack(fill='x', padx=5, pady=3)  # Уменьшаем отступы
        
        # Иконка компонента
        icon = self._get_component_icon(component.type)
        
        title_label = tk.Label(
            header_frame,
            text=f"{icon} {component.name}",
            font=('Arial', 10, 'bold'),  # Уменьшаем шрифт
            fg='#ecf0f1',
            bg='#2c3e50'
        )
        title_label.pack(side='left')
        
        # Статус индикатор
        status_label = tk.Label(
            header_frame,
            text="●",
            font=('Arial', 12),  # Уменьшаем шрифт
            fg=self._get_status_color(component.status),
            bg='#2c3e50'
        )
        status_label.pack(side='right')
        
        self.status_labels[component_id] = status_label
        
        # Информация о компоненте
        info_frame = tk.Frame(frame, bg='#2c3e50')
        info_frame.pack(fill='x', padx=5, pady=2)  # Уменьшаем отступы
        
        info_text = f"Type: {component.type}"
        if component.port:
            info_text += f" | Port: {component.port}"
        if component.dependencies:
            # Ограничиваем длину списка зависимостей
            deps = ', '.join(component.dependencies)
            if len(deps) > 30:
                deps = deps[:27] + "..."
            info_text += f" | Deps: {deps}"
            
        info_label = tk.Label(
            info_frame,
            text=info_text,
            font=('Arial', 8),  # Уменьшаем шрифт
            fg='#bdc3c7',
            bg='#2c3e50'
        )
        info_label.pack(side='left')
        
        # Кнопки управления
        buttons_frame = tk.Frame(frame, bg='#2c3e50')
        buttons_frame.pack(fill='x', padx=5, pady=3)  # Уменьшаем отступы
        
        start_btn = tk.Button(
            buttons_frame,
            text="▶️ Start",
            font=('Arial', 8),  # Уменьшаем шрифт
            bg='#27ae60',
            fg='white',
            command=lambda: self._start_component(component_id),
            relief='flat',
            padx=8  # Уменьшаем отступы
        )
        start_btn.pack(side='left', padx=(0, 3))
        
        stop_btn = tk.Button(
            buttons_frame,
            text="⏹️ Stop",
            font=('Arial', 8),  # Уменьшаем шрифт
            bg='#e74c3c',
            fg='white',
            command=lambda: self._stop_component(component_id),
            relief='flat',
            padx=8  # Уменьшаем отступы
        )
        stop_btn.pack(side='left', padx=3)
        
        restart_btn = tk.Button(
            buttons_frame,
            text="🔄 Restart",
            font=('Arial', 8),  # Уменьшаем шрифт
            bg='#f39c12',
            fg='white',
            command=lambda: self._restart_component(component_id),
            relief='flat',
            padx=8  # Уменьшаем отступы
        )
        restart_btn.pack(side='left', padx=3)
        
        # Кнопка открытия в браузере (для веб-сервисов)
        if component.port and component.port in [7474, 8000, 3005, 6333]:
            open_btn = tk.Button(
                buttons_frame,
                text="🌐 Open",
                font=('Arial', 8),  # Уменьшаем шрифт
                bg='#3498db',
                fg='white',
                command=lambda: self._open_in_browser(component.port),
                relief='flat',
                padx=8  # Уменьшаем отступы
            )
            open_btn.pack(side='right')
            
        self.control_buttons[component_id] = {
            'start': start_btn,
            'stop': stop_btn,
            'restart': restart_btn
        }
        
    def _create_monitoring_panel(self, parent):
        """Создание панели мониторинга"""
        logs_label = tk.Label(
            parent,
            text="📊 System Logs & Monitoring",
            font=('Arial', 14, 'bold'),
            fg='#ecf0f1',
            bg='#34495e'
        )
        logs_label.pack(pady=10)
        
        # Контролы мониторинга
        controls_frame = tk.Frame(parent, bg='#34495e')
        controls_frame.pack(fill='x', padx=10, pady=5)
        
        # Auto-refresh toggle
        auto_refresh_var = tk.BooleanVar(value=self.auto_refresh)
        auto_refresh_cb = tk.Checkbutton(
            controls_frame,
            text="Auto Refresh",
            variable=auto_refresh_var,
            command=lambda: setattr(self, 'auto_refresh', auto_refresh_var.get()),
            fg='#ecf0f1',
            bg='#34495e',
            selectcolor='#2c3e50'
        )
        auto_refresh_cb.pack(side='left', padx=5)
        
        # Refresh button
        refresh_btn = tk.Button(
            controls_frame,
            text="🔄 Refresh",
            font=('Arial', 9),
            bg='#3498db',
            fg='white',
            command=self._manual_refresh,
            relief='flat'
        )
        refresh_btn.pack(side='left', padx=5)
        
        # Export button
        export_btn = tk.Button(
            controls_frame,
            text="📄 Export Report",
            font=('Arial', 9),
            bg='#9b59b6',
            fg='white',
            command=self._export_report,
            relief='flat'
        )
        export_btn.pack(side='right', padx=5)
        
        # Clear logs button
        clear_btn = tk.Button(
            controls_frame,
            text="🗑️ Clear",
            font=('Arial', 9),
            bg='#95a5a6',
            fg='white',
            command=self._clear_logs,
            relief='flat'
        )
        clear_btn.pack(side='right', padx=5)
        
        # Область логов
        self.log_text = scrolledtext.ScrolledText(
            parent,
            height=25,
            bg='#2c3e50',
            fg='#ecf0f1',
            font=('Consolas', 10),
            insertbackground='#ecf0f1'
        )
        self.log_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Добавляем начальное сообщение
        self._log_message("System Launcher initialized", "INFO")
        
    def _create_status_bar(self):
        """Создание статус бара"""
        status_frame = tk.Frame(self.root, bg='#34495e', relief='sunken', bd=1)
        status_frame.pack(fill='x', side='bottom')
        
        self.status_bar_label = tk.Label(
            status_frame,
            text="System ready - Click 'Start All Systems' to begin",
            font=('Arial', 10),
            fg='#ecf0f1',
            bg='#34495e'
        )
        self.status_bar_label.pack(side='left', padx=10, pady=5)
        
        self.time_label = tk.Label(
            status_frame,
            text="",
            font=('Arial', 10),
            fg='#bdc3c7',
            bg='#34495e'
        )
        self.time_label.pack(side='right', padx=10, pady=5)
        
    def _get_component_icon(self, component_type: str) -> str:
        """Получение иконки для типа компонента"""
        icons = {
            'database': '🗄️',
            'service': '⚙️',
            'application': '🌐'
        }
        return icons.get(component_type, '📦')
        
    def _get_status_color(self, status: ComponentStatus) -> str:
        """Получение цвета для статуса компонента"""
        colors = {
            ComponentStatus.STOPPED: '#e74c3c',
            ComponentStatus.STARTING: '#f39c12',
            ComponentStatus.RUNNING: '#27ae60',
            ComponentStatus.ERROR: '#8e44ad',
            ComponentStatus.STOPPING: '#f39c12'
        }
        return colors.get(status, '#95a5a6')
        
    def _log_message(self, message: str, level: str = "INFO"):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        colors = {
            'INFO': '#ecf0f1',
            'SUCCESS': '#27ae60', 
            'WARNING': '#f39c12',
            'ERROR': '#e74c3c'
        }
        
        if self.log_text:
            self.log_text.insert('end', f"[{timestamp}] {level}: {message}\n")
            self.log_text.see('end')
            
        # Обновляем статус бар
        if self.status_bar_label:
            self.status_bar_label.config(text=message)
            
    def _update_time_label(self):
        """Обновление времени в статус баре"""
        if self.time_label:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.time_label.config(text=current_time)
            
    def _on_component_status_change(self, component_id: str, old_status: ComponentStatus, new_status: ComponentStatus):
        """Обработка изменения статуса компонента"""
        self._log_message(f"Component {component_id}: {old_status.value} -> {new_status.value}")
        
        # Обновляем GUI в главном потоке
        self.root.after(0, lambda: self._update_component_display(component_id))
        
    def _update_component_display(self, component_id: str):
        """Обновление отображения компонента"""
        if component_id in self.status_labels:
            component = self.component_manager.get_component_status(component_id)
            if component:
                color = self._get_status_color(component.status)
                self.status_labels[component_id].config(fg=color)
                
    def _start_component(self, component_id: str):
        """Запуск компонента"""
        self._log_message(f"Starting component: {component_id}")
        
        def start_thread():
            success = self.component_manager.start_component(component_id)
            if success:
                self._log_message(f"Component {component_id} started successfully", "SUCCESS")
            else:
                component = self.component_manager.get_component_status(component_id)
                error_msg = component.last_error if component else "Unknown error"
                self._log_message(f"Failed to start {component_id}: {error_msg}", "ERROR")
                
        threading.Thread(target=start_thread, daemon=True).start()
        
    def _stop_component(self, component_id: str):
        """Остановка компонента"""
        self._log_message(f"Stopping component: {component_id}")
        
        def stop_thread():
            success = self.component_manager.stop_component(component_id)
            if success:
                self._log_message(f"Component {component_id} stopped successfully", "SUCCESS")
            else:
                self._log_message(f"Failed to stop {component_id}", "ERROR")
                
        threading.Thread(target=stop_thread, daemon=True).start()
        
    def _restart_component(self, component_id: str):
        """Перезапуск компонента"""
        self._log_message(f"Restarting component: {component_id}")
        
        def restart_thread():
            success = self.component_manager.restart_component(component_id)
            if success:
                self._log_message(f"Component {component_id} restarted successfully", "SUCCESS")
            else:
                self._log_message(f"Failed to restart {component_id}", "ERROR")
                
        threading.Thread(target=restart_thread, daemon=True).start()
        
    def _start_all_systems(self):
        """Запуск всех систем"""
        result = messagebox.askyesno(
            "Start All Systems",
            "This will start all Bldr Empire components in the correct order.\n\nContinue?"
        )
        
        if result:
            self._log_message("Starting all systems...", "INFO")
            
            def start_all_thread():
                # Запускаем компоненты в правильном порядке
                components_to_start = ['redis', 'celery_worker', 'celery_beat', 'backend', 'frontend']
                
                for component_id in components_to_start:
                    if component_id in self.component_manager.components:
                        self._log_message(f"Starting {component_id}...", "INFO")
                        success = self.component_manager.start_component(component_id)
                        if success:
                            self._log_message(f"{component_id} started successfully", "SUCCESS")
                        else:
                            component = self.component_manager.get_component_status(component_id)
                            error_msg = component.last_error if component else "Unknown error"
                            self._log_message(f"Failed to start {component_id}: {error_msg}", "ERROR")
                            return  # Прерываем запуск, если какой-то компонент не запустился
                        time.sleep(3)  # Ждем между запусками
                
                self._log_message("All systems started successfully!", "SUCCESS")
                    
            threading.Thread(target=start_all_thread, daemon=True).start()
            
    def _stop_all_systems(self):
        """Остановка всех систем"""
        result = messagebox.askyesno(
            "Stop All Systems",
            "This will stop all running Bldr Empire components.\n\nContinue?"
        )
        
        if result:
            self._log_message("Stopping all systems...", "INFO")
            
            def stop_all_thread():
                success = self.component_manager.stop_all_components()
                self._log_message("All systems stopped", "SUCCESS")
                
            threading.Thread(target=stop_all_thread, daemon=True).start()
            
    def _open_in_browser(self, port: int):
        """Открытие сервиса в браузере"""
        url = f"http://localhost:{port}"
        try:
            webbrowser.open(url)
            self._log_message(f"Opened {url} in browser")
        except Exception as e:
            self._log_message(f"Failed to open browser: {e}", "ERROR")
            
    def _manual_refresh(self):
        """Ручное обновление статуса"""
        self._log_message("Refreshing component status...")
        
        for component_id in self.component_manager.get_all_components():
            self._update_component_display(component_id)
            
        # Получаем системный статус
        system_status = self.component_manager.get_system_status()
        self._log_message(f"System status: {system_status['overall_status']} "
                         f"({system_status['running_components']}/{system_status['total_components']} running)")
        
    def _clear_logs(self):
        """Очистка логов"""
        if self.log_text:
            self.log_text.delete(1.0, 'end')
            self._log_message("Logs cleared")
            
    def _export_report(self):
        """Экспорт отчета о системе"""
        try:
            report = self.component_manager.export_status_report()
            
            # Сохраняем в файл
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"bldr_system_report_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
                
            self._log_message(f"System report exported to {filename}", "SUCCESS")
            
            # Показываем диалог с информацией
            messagebox.showinfo(
                "Report Exported",
                f"System status report has been exported to:\n{filename}"
            )
            
        except Exception as e:
            self._log_message(f"Failed to export report: {e}", "ERROR")
            messagebox.showerror("Export Error", f"Failed to export report:\n{e}")
            
    def start_monitoring(self):
        """Запуск мониторинга"""
        self.component_manager.start_monitoring()
        
        # Запускаем поток обновления GUI
        self.gui_update_thread = threading.Thread(target=self._gui_update_loop, daemon=True)
        self.gui_update_thread.start()
        
    def _gui_update_loop(self):
        """Цикл обновления GUI"""
        while self.is_running:
            try:
                if self.auto_refresh:
                    # Обновляем время
                    self.root.after(0, self._update_time_label)
                    
                    # Обновляем статусы компонентов
                    for component_id in self.component_manager.get_all_components():
                        self.root.after(0, lambda cid=component_id: self._update_component_display(cid))
                        
                time.sleep(self.refresh_interval)
                
            except Exception as e:
                print(f"Error in GUI update loop: {e}")
                time.sleep(5)
                
    def run(self):
        """Запуск GUI"""
        try:
            # Обработка закрытия окна
            self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
            
            # Запуск главного цикла
            self.root.mainloop()
            
        except KeyboardInterrupt:
            self._on_closing()
            
    def _on_closing(self):
        """Обработка закрытия приложения"""
        result = messagebox.askyesno(
            "Exit System Launcher",
            "Do you want to stop all running components before exit?"
        )
        
        if result:
            self._log_message("Stopping all components before exit...")
            self.component_manager.stop_all_components()
            
        self.is_running = False
        self.component_manager.stop_monitoring()
        
        self.root.quit()
        self.root.destroy()


def main():
    """Главная функция"""
    try:
        # Проверяем зависимости
        import requests
        import psutil
        
        # Создаем и запускаем GUI
        launcher = BldrSystemLauncherGUI()
        launcher.run()
        
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please install required packages:")
        print("pip install requests psutil")
        sys.exit(1)
        
    except Exception as e:
        print(f"Error starting System Launcher: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()