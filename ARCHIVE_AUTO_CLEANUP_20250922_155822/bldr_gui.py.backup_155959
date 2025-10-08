import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import time
import os
import json
from pathlib import Path
import psutil
import requests
import platform
from queue import Queue
import traceback

class BldrEmpireGUI:
    def __init__(self, root):
        print("Initializing BldrEmpireGUI...")
        self.root = root
        print("Setting root properties...")
        self.root.title("Bldr Empire v2 - Service Manager")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Ensure window is visible and properly positioned
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        
        # Set window attributes to ensure visibility
        self.root.attributes('-topmost', True)
        self.root.after(100, lambda: self.root.attributes('-topmost', False))
        
        # Center the window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        print("Root properties set")
        print(f"Window position: {x}, {y}")
        
        # Thread-safe log queue
        print("Initializing log queue...")
        self.log_queue = Queue()
        self._process_log_queue()  # Start main thread processor
        print("Log queue initialized")
        
        # Service status tracking
        print("Initializing service status tracking...")
        self.services = {
            "Redis": {"port": 6379, "status": "Unknown", "process": None},
            "Neo4j": {"port": 7474, "status": "Unknown", "process": None},
            "Qdrant": {"port": 6333, "status": "Unknown", "process": None},
            "Celery": {"port": None, "status": "Unknown", "process": None},
            "Backend": {"port": 8000, "status": "Unknown", "process": None},
            "Frontend": {"port": 3001, "status": "Unknown", "process": None},
            "Telegram Bot": {"port": None, "status": "Unknown", "process": None}
        }
        print("Service status tracking initialized")
        
        self.processes = []
        self.start_thread = None
        self.stop_thread = None
        self.is_windows = platform.system() == "Windows"
        print("Creating widgets...")
        self.create_widgets()
        print("Widgets created")
        print("Updating status...")
        self.update_status()
        print("Status updated")
        
        # Auto-update thread (safe)
        print("Starting auto-update thread...")
        self.auto_update_thread = threading.Thread(target=self.auto_update_status, daemon=True)
        self.auto_update_thread.start()
        print("Auto-update thread started")
    
    def _process_log_queue(self):
        """Main thread: Process log queue safely"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self._log_impl(message)
        except:
            pass  # No more messages
        self.root.after(100, self._process_log_queue)  # Poll every 100ms
    
    def _log_impl(self, message):
        """Safe log insert (main thread only)"""
        self.log_text.config(state=tk.NORMAL)
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def log_message(self, message):
        """Thread-safe log: Queue if not main thread"""
        if threading.current_thread() is threading.main_thread():
            self._log_impl(message)
        else:
            self.log_queue.put(message)
    
    def on_closing(self):
        """Handle window closing (main thread)"""
        self.log_message("Window closing event triggered")
        try:
            result = messagebox.askokcancel("Quit", "Do you want to quit? This will not stop running services.")
            self.log_message(f"Message box result: {result}")
            if result:
                self.log_message("User confirmed closing, destroying root")
                self.root.destroy()
            else:
                self.log_message("User cancelled closing")
        except Exception as e:
            self.log_message(f"Error in on_closing: {e}")
            self.log_message(f"on_closing error traceback: {traceback.format_exc()}")
    
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
    
    def clear_logs(self):
        """Clear the log area"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def is_port_in_use(self, port):
        """Check if a port is in use"""
        try:
            for conn in psutil.net_connections():
                # Check if laddr is a proper address object with port attribute
                if hasattr(conn, 'laddr') and conn.laddr:
                    # Handle both tuple and object formats
                    if isinstance(conn.laddr, tuple) and len(conn.laddr) > 1:
                        if conn.laddr[1] == port and conn.status == psutil.CONN_LISTEN:
                            return True
                    elif hasattr(conn.laddr, 'port'):
                        if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                            return True
            return False
        except:
            # Fallback method if psutil fails
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(('localhost', port)) == 0
    
    def get_process_by_port(self, port):
        """Get process ID by port"""
        try:
            for conn in psutil.net_connections():
                # Check if laddr is a proper address object with port attribute
                if hasattr(conn, 'laddr') and conn.laddr:
                    # Handle both tuple and object formats
                    if isinstance(conn.laddr, tuple) and len(conn.laddr) > 1:
                        if conn.laddr[1] == port and conn.status == psutil.CONN_LISTEN:
                            return conn.pid
                    elif hasattr(conn.laddr, 'port'):
                        if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                            return conn.pid
            return None
        except:
            return None
    
    def update_status(self):
        """Update the status of all services"""
        for service_name, service_info in self.services.items():
            port = service_info["port"]
            if port:
                if self.is_port_in_use(port):
                    service_info["status"] = "Running"
                else:
                    service_info["status"] = "Stopped"
            else:
                # For services without specific ports, check by process name or other means
                if service_name == "Celery":
                    # Check if celery processes are running
                    celery_running = False
                    for proc in psutil.process_iter(['name']):
                        try:
                            if 'celery' in proc.info['name'].lower():
                                celery_running = True
                                break
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                    service_info["status"] = "Running" if celery_running else "Stopped"
                else:
                    service_info["status"] = "Unknown"
            
            # Update treeview
            port_display = str(port) if port else "N/A"
            self.status_tree.item(service_name, values=(service_info["status"], port_display))
        
        # Update status colors
        for service_name in self.services:
            status = self.services[service_name]["status"]
            tag = "running" if status == "Running" else "stopped" if status == "Stopped" else "unknown"
            self.status_tree.item(service_name, tags=(tag,))
        
        # Configure tags for colors
        self.status_tree.tag_configure("running", foreground="green")
        self.status_tree.tag_configure("stopped", foreground="red")
        self.status_tree.tag_configure("unknown", foreground="orange")
    
    def auto_update_status(self):
        """Automatically update status every 2 minutes"""
        self.log_message("Auto-update status thread started")
        try:
            count = 0
            while True:
                self.log_message(f"Auto-update status thread sleeping for 120 seconds (cycle {count})")
                time.sleep(120)  # 2 minutes
                self.log_message(f"Auto-update status thread waking up, updating status (cycle {count})")
                self.root.after(0, self.update_status)
                count += 1
        except Exception as e:
            self.log_message(f"Error in auto_update_status: {e}")
            self.log_message(f"auto_update_status error traceback: {traceback.format_exc()}")
    
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
    
    def _start_services_thread(self):
        """Thread function to start services"""
        original_dir = os.getcwd()  # Initialize at the beginning
        project_dir = os.path.dirname(os.path.abspath(__file__))
        self.log_message(f"Start services thread started. Original dir: {original_dir}, Project dir: {project_dir}")
        try:
            # Change to the project directory
            os.chdir(project_dir)
            self.log_message("Changed to project directory successfully")
            
            # Kill any existing processes first (safer approach)
            self.log_message("Cleaning up existing processes...")
            try:
                killed_count = 0
                # Only kill specific processes related to Bldr Empire
                target_processes = ["redis-server.exe", "java.exe", "docker.exe", "node.exe", "uvicorn.exe", "celery.exe", "npm.exe"]
                
                # Use psutil for more precise process management
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        proc_name = proc.info['name'].lower()
                        # Check if this is a target process
                        for target in target_processes:
                            if target in proc_name:
                                # Additional check to avoid killing system processes
                                proc_obj = psutil.Process(proc.info['pid'])
                                # Only kill processes that are likely ours
                                if "bldr" in ' '.join(proc_obj.cmdline()).lower() or "empire" in ' '.join(proc_obj.cmdline()).lower():
                                    proc_obj.terminate()
                                    killed_count += 1
                                    self.log_message(f"Terminated process: {proc_name} (PID: {proc.info['pid']})")
                                    break
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        # Skip processes we can't access
                        pass
                
                self.log_message(f"Cleanup completed. Killed {killed_count} processes.")
                if killed_count == 0:
                    self.log_message("No old processes found to terminate.")
            except Exception as e:
                self.log_message(f"Warning: Cleanup encountered an error: {e}")
                self.log_message("Continuing with service startup...")
            
            time.sleep(3)
            
            # 1. Start Redis
            self.log_message("Starting Redis server...")
            redis_dir = os.path.join(os.getcwd(), "redis")
            self.log_message(f"Redis directory: {redis_dir}")
            self.log_message(f"Redis directory exists: {os.path.exists(redis_dir)}")
            if os.path.exists(redis_dir):
                os.chdir(redis_dir)
                self.log_message(f"Changed to Redis directory: {os.getcwd()}")
                try:
                    # Start Redis in background without blocking
                    self.log_message("Attempting to start Redis process...")
                    # Use CREATE_NEW_CONSOLE to ensure Redis runs in a separate console
                    creation_flags = subprocess.CREATE_NEW_CONSOLE if self.is_windows else 0
                    redis_process = subprocess.Popen(["redis-server.exe", "redis.windows.conf"], 
                                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                                   creationflags=creation_flags)
                    self.processes.append(redis_process)
                    self.log_message(f"Redis server started successfully with PID: {redis_process.pid}")
                except Exception as e:
                    self.log_message(f"Error starting Redis: {e}")
                    import traceback
                    self.log_message(f"Redis error traceback: {traceback.format_exc()}")
                os.chdir(project_dir)
                self.log_message(f"Returned to project directory: {os.getcwd()}")
            
            time.sleep(5)
            
            # 2. Start Neo4j
            self.log_message("Starting Neo4j database...")
            neo4j_path = r"C:\Users\papa\AppData\Local\Programs\neo4j-desktop"  # Updated path
            self.log_message(f"Neo4j path: {neo4j_path}")
            self.log_message(f"Neo4j path exists: {os.path.exists(neo4j_path)}")
            if os.path.exists(neo4j_path):
                # Look for the bin directory within Neo4j
                neo4j_bin_path = None
                for root, dirs, files in os.walk(neo4j_path):
                    if "bin" in dirs and "neo4j.bat" in os.listdir(os.path.join(root, "bin")):
                        neo4j_bin_path = os.path.join(root, "bin")
                        break
                
                if neo4j_bin_path and os.path.exists(neo4j_bin_path):
                    os.chdir(neo4j_bin_path)
                    self.log_message(f"Changed to Neo4j directory: {os.getcwd()}")
                    try:
                        # Start Neo4j in background without blocking
                        self.log_message("Attempting to start Neo4j process...")
                        # Use CREATE_NEW_CONSOLE to ensure Neo4j runs in a separate console
                        creation_flags = subprocess.CREATE_NEW_CONSOLE if self.is_windows else 0
                        neo4j_process = subprocess.Popen(["neo4j.bat", "start"], 
                                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                                       creationflags=creation_flags)
                        self.processes.append(neo4j_process)
                        self.log_message(f"Neo4j database started successfully with PID: {neo4j_process.pid}")
                    except Exception as e:
                        self.log_message(f"Error starting Neo4j: {e}")
                        import traceback
                        self.log_message(f"Neo4j error traceback: {traceback.format_exc()}")
                    os.chdir(project_dir)
                    self.log_message(f"Returned to project directory: {os.getcwd()}")
                else:
                    self.log_message("Could not find Neo4j bin directory")
            else:
                self.log_message("Neo4j path does not exist")
            
            time.sleep(10)
            
            # 3. Start Qdrant
            self.log_message("Starting Qdrant vector database...")
            try:
                result = subprocess.run(["docker", "start", "qdrant-bldr"], 
                                      capture_output=True, text=True)
                if result.returncode != 0:
                    self.log_message("Creating new Qdrant container...")
                    subprocess.run(["docker", "run", "-d", "-p", "6333:6333", "-p", "6334:6334", 
                                  "--name", "qdrant-bldr", "qdrant/qdrant:v1.7.0"], 
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self.log_message("Qdrant container created and started")
                else:
                    self.log_message("Qdrant container started successfully")
            except Exception as e:
                self.log_message(f"Error starting Qdrant: {e}")
            
            time.sleep(5)
            
            # 4. Start Celery worker and beat
            self.log_message("Starting Celery services...")
            try:
                # Start Celery worker
                creation_flags = subprocess.CREATE_NEW_CONSOLE if self.is_windows else 0
                celery_worker_process = subprocess.Popen([
                    "celery", "-A", "core.celery_app", "worker", "--loglevel=info", "--concurrency=2"
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                creationflags=creation_flags)
                self.processes.append(celery_worker_process)
                
                # Start Celery beat
                celery_beat_process = subprocess.Popen([
                    "celery", "-A", "core.celery_app", "beat", "--loglevel=info"
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                creationflags=creation_flags)
                self.processes.append(celery_beat_process)
                
                self.log_message("Celery services started successfully")
            except Exception as e:
                self.log_message(f"Error starting Celery: {e}")
            
            time.sleep(3)
            
            # 5. Start FastAPI backend
            self.log_message("Starting FastAPI backend...")
            try:
                creation_flags = subprocess.CREATE_NEW_CONSOLE if self.is_windows else 0
                backend_process = subprocess.Popen([
                    "uvicorn", "core.bldr_api:app", "--host", "0.0.0.0", "--port", "8000"
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                creationflags=creation_flags)
                self.processes.append(backend_process)
                self.log_message("FastAPI backend started successfully")
            except Exception as e:
                self.log_message(f"Error starting Backend: {e}")
            
            time.sleep(5)
            
            # 6. Start Telegram Bot
            self.log_message("Starting Telegram Bot...")
            try:
                creation_flags = subprocess.CREATE_NEW_CONSOLE if self.is_windows else 0
                telegram_process = subprocess.Popen([
                    "python", "integrations/telegram_bot.py"
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                creationflags=creation_flags)
                self.processes.append(telegram_process)
                self.log_message("Telegram Bot started successfully")
            except Exception as e:
                self.log_message(f"Error starting Telegram Bot: {e}")
            
            time.sleep(2)
            
            # 7. Start Frontend
            self.log_message("Starting Frontend Dashboard...")
            frontend_dir = os.path.join(os.getcwd(), "web", "bldr_dashboard")
            if os.path.exists(frontend_dir):
                os.chdir(frontend_dir)
                try:
                    creation_flags = subprocess.CREATE_NEW_CONSOLE if self.is_windows else 0
                    frontend_process = subprocess.Popen([
                        "npm", "run", "dev"
                    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    creationflags=creation_flags)
                    self.processes.append(frontend_process)
                    self.log_message("Frontend Dashboard started successfully")
                except Exception as e:
                    self.log_message(f"Error starting Frontend: {e}")
                os.chdir(project_dir)
                self.log_message(f"Returned to project directory: {os.getcwd()}")
            
            time.sleep(10)
            
            # Check if backend is responding
            self.log_message("Checking backend status...")
            try:
                response = requests.get("http://localhost:8000/health", timeout=5)
                if response.status_code == 200:
                    self.log_message("Backend is responding successfully")
                else:
                    self.log_message("Backend may not be ready")
            except:
                self.log_message("Backend not responding yet")
            
            self.log_message("All services started successfully!")
            self.log_message("Frontend Dashboard: http://localhost:3001")
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.log_message(f"Error starting services: {e}")
            self.log_message(f"Error details: {error_details}")
        finally:
            # Always re-enable the start button
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
            self.root.after(0, self.update_status)
            # Return to original directory
            try:
                os.chdir(original_dir)
                self.log_message("Returned to original directory successfully")
            except Exception as e:
                self.log_message(f"Error returning to original directory: {e}")
                pass
    
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
    
    def _stop_services_thread(self):
        """Thread function to stop services"""
        original_dir = os.getcwd()  # Initialize at the beginning
        project_dir = os.path.dirname(os.path.abspath(__file__))
        self.log_message(f"Stop services thread started. Original dir: {original_dir}, Project dir: {project_dir}")
        try:
            # Change to the project directory
            os.chdir(project_dir)
            self.log_message(f"Changed to project directory: {os.getcwd()}")
            
            # Kill processes by port (safer approach)
            ports = [8000, 3001, 6379, 7474, 6333]
            killed_ports = []
            for port in ports:
                self.log_message(f"Checking for processes on port {port}...")
                try:
                    # Find and kill processes on this port
                    for conn in psutil.net_connections():
                        # Check if laddr is a proper address object with port attribute
                        if hasattr(conn, 'laddr') and conn.laddr:
                            # Handle both tuple and object formats
                            if isinstance(conn.laddr, tuple) and len(conn.laddr) > 1:
                                if conn.laddr[1] == port and conn.status == psutil.CONN_LISTEN:
                                    try:
                                        process = psutil.Process(conn.pid)
                                        # Check if this is likely a Bldr process
                                        cmdline = ' '.join(process.cmdline()).lower()
                                        if "bldr" in cmdline or "empire" in cmdline or "redis" in cmdline or "neo4j" in cmdline or "qdrant" in cmdline:
                                            process.terminate()
                                            try:
                                                process.wait(timeout=5)
                                                self.log_message(f"Terminated process {conn.pid} on port {port}")
                                                killed_ports.append(port)
                                            except:
                                                process.kill()
                                                self.log_message(f"Force killed process {conn.pid} on port {port}")
                                                killed_ports.append(port)
                                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                                        self.log_message(f"Could not terminate process {conn.pid} on port {port} (access denied or process gone)")
                            elif hasattr(conn.laddr, 'port'):
                                if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                                    try:
                                        process = psutil.Process(conn.pid)
                                        # Check if this is likely a Bldr process
                                        cmdline = ' '.join(process.cmdline()).lower()
                                        if "bldr" in cmdline or "empire" in cmdline or "redis" in cmdline or "neo4j" in cmdline or "qdrant" in cmdline:
                                            process.terminate()
                                            try:
                                                process.wait(timeout=5)
                                                self.log_message(f"Terminated process {conn.pid} on port {port}")
                                                killed_ports.append(port)
                                            except:
                                                process.kill()
                                                self.log_message(f"Force killed process {conn.pid} on port {port}")
                                                killed_ports.append(port)
                                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                                        self.log_message(f"Could not terminate process {conn.pid} on port {port} (access denied or process gone)")
                except Exception as e:
                    self.log_message(f"Error checking processes on port {port}: {e}")
            
            self.log_message(f"Finished stopping services on ports. Killed processes on ports: {killed_ports}")
            
            # Kill by process name as fallback (safer approach)
            self.log_message("Killing remaining Bldr-related processes...")
            killed_by_name = []
            process_names = ["redis-server.exe", "uvicorn.exe", "celery.exe", "npm.exe"]
            for proc_name in process_names:
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if proc_name.lower() in proc.info['name'].lower():
                            # Check if this is likely a Bldr process
                            cmdline = ' '.join(proc.info['cmdline']).lower()
                            if "bldr" in cmdline or "empire" in cmdline:
                                process = psutil.Process(proc.pid)
                                process.terminate()
                                self.log_message(f"Terminated {proc_name} process {proc.pid}")
                                killed_by_name.append(proc_name)
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
            
            self.log_message(f"Finished killing processes by name. Killed: {killed_by_name}")
            
            # Stop Neo4j service properly
            self.log_message("Stopping Neo4j service...")
            neo4j_path = r"C:\Users\papa\AppData\Local\Programs\neo4j-desktop"  # Updated path
            if os.path.exists(neo4j_path):
                # Look for the bin directory within Neo4j
                neo4j_bin_path = None
                for root, dirs, files in os.walk(neo4j_path):
                    if "bin" in dirs and "neo4j.bat" in os.listdir(os.path.join(root, "bin")):
                        neo4j_bin_path = os.path.join(root, "bin")
                        break
                
                if neo4j_bin_path and os.path.exists(neo4j_bin_path):
                    os.chdir(neo4j_bin_path)
                    try:
                        subprocess.run(["neo4j.bat", "stop"], 
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        self.log_message("Neo4j service stopped successfully")
                    except:
                        pass
                    os.chdir(original_dir)
            
            # Stop Docker containers
            self.log_message("Stopping Docker containers...")
            try:
                subprocess.run(["docker", "stop", "qdrant-bldr"], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.log_message("Qdrant container stopped successfully")
            except:
                pass
            
            self.log_message("All services stopped successfully!")
            
        except Exception as e:
            self.log_message(f"Error stopping services: {e}")
        finally:
            # Always re-enable the stop button
            self.root.after(0, lambda: self.stop_button.config(state=tk.NORMAL))
            self.root.after(0, self.update_status)
            # Return to original directory
            try:
                os.chdir(original_dir)
            except:
                pass

def main():
    try:
        print("Creating Tk root...")
        root = tk.Tk()
        print("Root window created")
        print(f"Root window geometry: {root.winfo_geometry()}")
        print(f"Root window position: {root.winfo_x()}, {root.winfo_y()}")
        
        # Ensure window is visible and properly positioned
        root.title("Bldr Empire v2 - Service Manager")
        root.geometry("800x600")
        root.deiconify()
        root.lift()
        root.focus_force()
        
        # Set window attributes to ensure visibility
        root.attributes('-topmost', True)
        root.after_idle(root.attributes, '-topmost', False)
        
        print("Creating BldrEmpireGUI...")
        app = BldrEmpireGUI(root)
        print("BldrEmpireGUI created successfully")
        print("Starting mainloop...")
        print(f"Window title: {root.title()}")
        print(f"Window size: {root.winfo_width()}x{root.winfo_height()}")
        
        # Force window to be visible
        root.update()
        root.deiconify()
        root.lift()
        root.focus_force()
        
        try:
            root.mainloop()
            print("Mainloop finished normally")
        except Exception as e:
            print(f"Mainloop error: {e}")
            import traceback
            traceback.print_exc()
            with open('mainloop_error.log', 'w') as f:
                f.write(f"Mainloop error: {e}\n")
                f.write(traceback.format_exc())
        print("Exiting main function")
    except Exception as e:
        import traceback
        error_msg = f"GUI Error: {str(e)}\n\n{traceback.format_exc()}"
        print(error_msg)
        with open('gui_error.log', 'w', encoding='utf-8') as f:
            f.write(error_msg)
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()