import tkinter as tk
from tkinter import ttk, scrolledtext
import subprocess
import threading
import os
import time
import psutil

class BldrServiceManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Bldr Empire v2 Service Manager")
        self.root.geometry("800x600")
        
        # Service processes
        self.processes = {}
        
        # Create UI
        self.create_widgets()
        
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nesw")
        
        # Service control buttons
        btn_frame = ttk.LabelFrame(main_frame, text="Service Control", padding="10")
        btn_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        self.start_btn = ttk.Button(btn_frame, text="Start All Services", command=self.start_all_services)
        self.start_btn.grid(row=0, column=0, padx=(0, 5))
        
        self.stop_btn = ttk.Button(btn_frame, text="Stop All Services", command=self.stop_all_services)
        self.stop_btn.grid(row=0, column=1, padx=(5, 5))
        
        self.refresh_btn = ttk.Button(btn_frame, text="Refresh Status", command=self.refresh_status)
        self.refresh_btn.grid(row=0, column=2, padx=(5, 0))
        
        # Note about Neo4j
        note_frame = ttk.Frame(main_frame)
        note_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        ttk.Label(note_frame, text="[NOTE] Neo4j is NOT managed by this tool - please start/stop it manually", 
                 foreground="red", font=("Arial", 9, "bold")).pack()
        
        # Individual service controls
        services_frame = ttk.LabelFrame(main_frame, text="Individual Services", padding="10")
        services_frame.grid(row=2, column=0, sticky="nesw", pady=(0, 10))
        
        # Redis
        ttk.Label(services_frame, text="Redis:").grid(row=0, column=0, sticky="w")
        self.redis_status = ttk.Label(services_frame, text="Stopped")
        self.redis_status.grid(row=0, column=1, padx=(10, 0))
        ttk.Button(services_frame, text="Start", command=lambda: self.start_service("redis")).grid(row=0, column=2, padx=(10, 5))
        ttk.Button(services_frame, text="Stop", command=lambda: self.stop_service("redis")).grid(row=0, column=3, padx=(5, 0))
        
        # Qdrant
        ttk.Label(services_frame, text="Qdrant:").grid(row=1, column=0, sticky="w")
        self.qdrant_status = ttk.Label(services_frame, text="Stopped")
        self.qdrant_status.grid(row=1, column=1, padx=(10, 0))
        ttk.Button(services_frame, text="Start", command=lambda: self.start_service("qdrant")).grid(row=1, column=2, padx=(10, 5))
        ttk.Button(services_frame, text="Stop", command=lambda: self.stop_service("qdrant")).grid(row=1, column=3, padx=(5, 0))
        
        # FastAPI Backend
        ttk.Label(services_frame, text="FastAPI Backend:").grid(row=2, column=0, sticky="w")
        self.backend_status = ttk.Label(services_frame, text="Stopped")
        self.backend_status.grid(row=2, column=1, padx=(10, 0))
        ttk.Button(services_frame, text="Start", command=lambda: self.start_service("backend")).grid(row=2, column=2, padx=(10, 5))
        ttk.Button(services_frame, text="Stop", command=lambda: self.stop_service("backend")).grid(row=2, column=3, padx=(5, 0))
        
        # Frontend
        ttk.Label(services_frame, text="Frontend:").grid(row=3, column=0, sticky="w")
        self.frontend_status = ttk.Label(services_frame, text="Stopped")
        self.frontend_status.grid(row=3, column=1, padx=(10, 0))
        ttk.Button(services_frame, text="Start", command=lambda: self.start_service("frontend")).grid(row=3, column=2, padx=(10, 5))
        ttk.Button(services_frame, text="Stop", command=lambda: self.stop_service("frontend")).grid(row=3, column=3, padx=(5, 0))
        
        # Log output
        log_frame = ttk.LabelFrame(main_frame, text="Service Logs", padding="10")
        log_frame.grid(row=2, column=0, columnspan=2, sticky="nesw", pady=(0, 10))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=80, height=15)
        self.log_text.grid(row=0, column=0, sticky="nesw")
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
    def log_message(self, message):
        self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see(tk.END)
        
    def start_service(self, service_name):
        try:
            if service_name == "redis":
                self.log_message("Starting Redis server...")
                # Start Redis in a separate process
                redis_path = os.path.join("redis", "redis-server.exe")
                if os.path.exists(redis_path):
                    process = subprocess.Popen([redis_path, "redis.windows.conf"], cwd="redis")
                    self.processes["redis"] = process
                    self.redis_status.config(text="Running")
                    self.log_message("Redis server started")
                else:
                    self.log_message("ERROR: Redis server executable not found")
                    
            elif service_name == "qdrant":
                self.log_message("Starting Qdrant container...")
                # Try to start existing container
                result = subprocess.run(["docker", "start", "qdrant-bldr"], capture_output=True, text=True)
                if result.returncode != 0:
                    # Try to create new container
                    result = subprocess.run([
                        "docker", "run", "-d", "-p", "6333:6333", "-p", "6334:6334", 
                        "--name", "qdrant-bldr", "qdrant/qdrant:v1.7.0"
                    ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.qdrant_status.config(text="Running")
                    self.log_message("Qdrant container started")
                else:
                    self.log_message(f"ERROR: Failed to start Qdrant: {result.stderr}")
                    
            elif service_name == "backend":
                self.log_message("Starting FastAPI backend...")
                # Start FastAPI backend
                process = subprocess.Popen([
                    "python", "-m", "uvicorn", "core.bldr_api:app", 
                    "--host", "127.0.0.1", "--port", "8000", "--reload"
                ])
                self.processes["backend"] = process
                self.backend_status.config(text="Running")
                self.log_message("FastAPI backend started")
                
            elif service_name == "frontend":
                self.log_message("Starting Frontend Dashboard...")
                # Kill any existing process on port 3001
                for proc in psutil.process_iter(['pid', 'name', 'connections']):
                    try:
                        if proc.info['connections']:
                            for conn in proc.info['connections']:
                                if conn.laddr.port == 3001:
                                    proc.kill()
                                    self.log_message(f"Killed existing process on port 3001 (PID: {proc.info['pid']})")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # Start frontend
                process = subprocess.Popen(["npm", "run", "dev"], cwd="web/bldr_dashboard")
                self.processes["frontend"] = process
                self.frontend_status.config(text="Running")
                self.log_message("Frontend Dashboard started")
                
        except Exception as e:
            self.log_message(f"ERROR starting {service_name}: {str(e)}")
            
    def stop_service(self, service_name):
        try:
            if service_name in self.processes:
                process = self.processes[service_name]
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                del self.processes[service_name]
                
            # Special handling for Docker containers
            if service_name == "qdrant":
                subprocess.run(["docker", "stop", "qdrant-bldr"], capture_output=True)
                
            # Update status
            if service_name == "redis":
                self.redis_status.config(text="Stopped")
            elif service_name == "qdrant":
                self.qdrant_status.config(text="Stopped")
            elif service_name == "backend":
                self.backend_status.config(text="Stopped")
            elif service_name == "frontend":
                self.frontend_status.config(text="Stopped")
                
            self.log_message(f"{service_name.capitalize()} stopped")
            
        except Exception as e:
            self.log_message(f"ERROR stopping {service_name}: {str(e)}")
            
    def start_all_services(self):
        # Start services in order (EXCEPT Neo4j which is managed manually)
        self.start_service("redis")
        time.sleep(2)
        self.start_service("qdrant")
        time.sleep(2)
        self.start_service("backend")
        time.sleep(5)
        self.start_service("frontend")
        self.log_message("All services started (except Neo4j which is managed manually)")
        
    def stop_all_services(self):
        # Stop services in reverse order (EXCEPT Neo4j which is managed manually)
        for service in ["frontend", "backend", "qdrant", "redis"]:
            self.stop_service(service)
        self.log_message("All services stopped (except Neo4j which is managed manually)")
        
    def refresh_status(self):
        self.log_message("Refreshing service status...")
        # Check actual service status by making health check requests
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                if health_data.get("status") == "ok":
                    self.log_message("✅ All services are running normally")
                else:
                    self.log_message("⚠️ Some services may have issues")
            else:
                self.log_message("❌ API service is not responding")
        except Exception as e:
            self.log_message(f"❌ Error checking service status: {str(e)}")
        self.log_message("Status refresh complete")

if __name__ == "__main__":
    root = tk.Tk()
    app = BldrServiceManager(root)
    root.mainloop()