#!/usr/bin/env python3
"""
System Component Manager
Управление компонентами системы Bldr Empire v2
"""

import os
import sys
import time
import psutil
import requests
import subprocess
import threading
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import logging
import socket

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComponentStatus(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"
    STOPPING = "stopping"

class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class ComponentMetrics:
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    response_time: Optional[float] = None
    error_rate: Optional[float] = None
    uptime: Optional[int] = None
    
@dataclass
class ComponentInfo:
    id: str
    name: str
    type: str  # service, database, application
    status: ComponentStatus = ComponentStatus.STOPPED
    health: HealthStatus = HealthStatus.UNKNOWN
    port: Optional[int] = None
    dependencies: List[str] = field(default_factory=list)
    process: Optional[subprocess.Popen] = None
    pid: Optional[int] = None
    start_time: Optional[datetime] = None
    last_error: Optional[str] = None
    metrics: ComponentMetrics = field(default_factory=ComponentMetrics)
    config: Dict[str, Any] = field(default_factory=dict)

class SystemComponentManager:
    """Менеджер компонентов системы Bldr Empire"""
    
    def __init__(self):
        self.components: Dict[str, ComponentInfo] = {}
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.status_callbacks: List[Callable] = []
        
        # Инициализация компонентов
        self._initialize_components()
        
    def _load_env_variables(self):
        """Загрузка переменных окружения из .env файла"""
        # Проверяем .env файл в текущей директории
        env_file = Path('.env')
        if not env_file.exists():
            # Проверяем .env файл в родительской директории (корневой папке проекта)
            env_file = Path(__file__).parent.parent / '.env'
            
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value.strip('"').strip("'")  # Remove quotes if present
            logger.info(f"Environment variables loaded from {env_file}")
        else:
            logger.warning(".env file not found, using default values")
        
    def _initialize_components(self):
        """Инициализация конфигурации компонентов на основе start_bldr.bat"""
        
        # Загружаем переменные окружения из .env файла
        self._load_env_variables()
        
        # Определяем корневую директорию проекта
        project_root = Path(__file__).parent.parent
        
        # Neo4j Database (управляется вручную)
        self.components['neo4j'] = ComponentInfo(
            id='neo4j',
            name='Neo4j Database',
            type='database',
            port=7474,
            dependencies=[],
            config={
                'health_url': 'http://localhost:7474',
                'start_command': None,  # Управляется через Neo4j Desktop
                'check_script': str(project_root / 'check_neo4j_status.py')
            }
        )
        
        # Redis Server
        self.components['redis'] = ComponentInfo(
            id='redis',
            name='Redis Server',
            type='database',
            port=6379,
            dependencies=[],
            config={
                'start_command': [str(project_root / 'redis' / 'redis-server.exe'), str(project_root / 'redis' / 'redis.windows.conf')],
                'health_url': None,
                'working_dir': project_root,
                'window_title': 'Redis Server'
            }
        )
        
        # Qdrant Vector Database
        self.components['qdrant'] = ComponentInfo(
            id='qdrant',
            name='Qdrant Vector Database',
            type='database',
            port=6333,
            dependencies=[],
            config={
                'start_command': ['docker', 'start', 'qdrant-bldr'],
                'fallback_command': ['docker', 'run', '-d', '-p', '6333:6333', '-p', '6334:6334', 
                                   '--name', 'qdrant-bldr', 'qdrant/qdrant:v1.7.0'],
                'health_url': 'http://localhost:6333',
                'requires_docker': True
            }
        )
        
        # Celery Worker
        self.components['celery_worker'] = ComponentInfo(
            id='celery_worker',
            name='Celery Worker',
            type='service',
            port=None,
            dependencies=['redis'],
            config={
                'start_command': ['celery', '-A', 'core.celery_app', 'worker', '--loglevel=info', '--concurrency=2'],
                'working_dir': project_root,
                'window_title': 'Celery Worker'
            }
        )
        
        # Celery Beat
        self.components['celery_beat'] = ComponentInfo(
            id='celery_beat',
            name='Celery Beat Scheduler',
            type='service',
            port=None,
            dependencies=['redis'],
            config={
                'start_command': ['celery', '-A', 'core.celery_app', 'beat', '--loglevel=info'],
                'working_dir': project_root,
                'window_title': 'Celery Beat'
            }
        )
        
        # FastAPI Backend
        self.components['backend'] = ComponentInfo(
            id='backend',
            name='FastAPI Backend',
            type='service',
            port=8000,
            dependencies=['neo4j', 'redis', 'celery_worker'],
            config={
                'start_command': ['python', '-m', 'uvicorn', 'core.bldr_api:app', 
                                '--host', '127.0.0.1', '--port', '8000', '--reload'],
                'health_url': 'http://localhost:8000',
                'working_dir': project_root,
                'window_title': 'FastAPI Backend',
                'env_vars': {
                    'NEO4J_USER': os.environ.get('NEO4J_USER', 'neo4j'),
                    'NEO4J_PASSWORD': os.environ.get('NEO4J_PASSWORD', 'neopassword'),
                    'NEO4J_URI': os.environ.get('NEO4J_URI', 'neo4j://localhost:7687'),
                    'REDIS_URL': os.environ.get('REDIS_URL', 'redis://localhost:6379')
                }
            }
        )
        
        # Frontend Dashboard
        self.components['frontend'] = ComponentInfo(
            id='frontend',
            name='Frontend Dashboard',
            type='application',
            port=3001,  # Fixed port to match documentation and avoid constant changes
            dependencies=['backend'],
            config={
                'start_command': ['npm', 'run', 'dev'],
                'health_url': 'http://localhost:3001',  # Fixed port to match
                'working_dir': project_root / 'web' / 'bldr_dashboard',
                'window_title': 'Frontend Dashboard'
            }
        )
        
    def add_status_callback(self, callback: Callable):
        """Добавление callback для уведомлений о изменении статуса"""
        self.status_callbacks.append(callback)
        
    def _is_port_in_use(self, port: int) -> bool:
        """Проверка использования порта"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
            
    def _notify_status_change(self, component_id: str, old_status: ComponentStatus, new_status: ComponentStatus):
        """Уведомление о изменении статуса компонента"""
        for callback in self.status_callbacks:
            try:
                callback(component_id, old_status, new_status)
            except Exception as e:
                logger.error(f"Error in status callback: {e}")
                
    def get_component_status(self, component_id: str) -> Optional[ComponentInfo]:
        """Получение статуса компонента"""
        return self.components.get(component_id)
        
    def get_all_components(self) -> Dict[str, ComponentInfo]:
        """Получение всех компонентов"""
        return self.components.copy()
        
    def start_component(self, component_id: str) -> bool:
        """Запуск компонента"""
        if component_id not in self.components:
            logger.error(f"Component {component_id} not found")
            return False
            
        component = self.components[component_id]
        
        if component.status == ComponentStatus.RUNNING:
            logger.info(f"Component {component_id} is already running")
            return True
            
        # Проверка зависимостей (только для уже запущенных компонентов)
        for dep_id in component.dependencies:
            dep_component = self.components.get(dep_id)
            if dep_id == 'neo4j':
                # Для Neo4j проверяем доступность через HTTP
                try:
                    response = requests.get('http://localhost:7474', timeout=5)
                    if response.status_code != 200:
                        logger.warning(f"Neo4j dependency check failed, but continuing...")
                except requests.exceptions.RequestException:
                    logger.warning(f"Neo4j dependency not available, but continuing...")
            elif dep_id == 'redis':
                # Для Redis проверяем, запущен ли он на порту
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    result = sock.connect_ex(('localhost', 6379))
                    sock.close()
                    if result != 0:
                        logger.error(f"Redis dependency is not running for component {component_id}")
                        return False
                except Exception as e:
                    logger.error(f"Error checking Redis dependency: {e}")
                    return False
            elif dep_id in ['celery_worker', 'celery_beat']:
                # Для Celery проверяем, запущен ли соответствующий процесс
                # В GUI мы можем не видеть статус из другого экземпляра, поэтому проверяем по портам или процессам
                if dep_component and dep_component.status == ComponentStatus.RUNNING:
                    continue
                else:
                    # Проверяем, запущен ли процесс Celery
                    try:
                        # Простая проверка - если мы можем запустить Celery, значит он доступен
                        result = subprocess.run(['celery', '--version'], 
                                              capture_output=True, text=True, timeout=5)
                        if result.returncode == 0:
                            logger.info(f"Celery {dep_id} is available")
                            continue
                        else:
                            logger.error(f"Celery {dep_id} is not available")
                            return False
                    except Exception as e:
                        logger.error(f"Error checking Celery {dep_id} availability: {e}")
                        return False
            elif dep_id == 'backend':
                # Для backend проверяем, запущен ли он на порту 8000 и отвечает ли он
                try:
                    # First check if port is in use
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    result = sock.connect_ex(('localhost', 8000))
                    sock.close()
                    if result != 0:
                        logger.error(f"Backend dependency is not running for component {component_id}")
                        return False
                    
                    # Then check if it responds properly
                    response = requests.get('http://localhost:8000', timeout=5)
                    if response.status_code == 200:
                        logger.info("Backend is available and responding on port 8000")
                        continue
                    else:
                        logger.error(f"Backend dependency is not responding properly for component {component_id}")
                        return False
                except requests.exceptions.RequestException:
                    logger.error(f"Backend dependency is not responding for component {component_id}")
                    return False
                except Exception as e:
                    logger.error(f"Error checking Backend dependency: {e}")
                    return False
            elif not dep_component or dep_component.status != ComponentStatus.RUNNING:
                logger.error(f"Dependency {dep_id} is not running for component {component_id}")
                return False
                
        old_status = component.status
        component.status = ComponentStatus.STARTING
        self._notify_status_change(component_id, old_status, component.status)
        
        try:
            if component_id == 'neo4j':
                return self._start_neo4j(component)
            elif component_id == 'redis':
                return self._start_redis(component)
            elif component_id == 'qdrant':
                return self._start_qdrant(component)
            elif component_id == 'celery_worker':
                return self._start_celery_worker(component)
            elif component_id == 'celery_beat':
                return self._start_celery_beat(component)
            elif component_id == 'backend':
                return self._start_backend(component)
            elif component_id == 'frontend':
                return self._start_frontend(component)
            else:
                logger.error(f"Unknown component type: {component_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error starting component {component_id}: {e}")
            component.status = ComponentStatus.ERROR
            component.last_error = str(e)
            self._notify_status_change(component_id, ComponentStatus.STARTING, component.status)
            return False
            
    def stop_component(self, component_id: str) -> bool:
        """Остановка компонента"""
        if component_id not in self.components:
            logger.error(f"Component {component_id} not found")
            return False
            
        component = self.components[component_id]
        
        if component.status == ComponentStatus.STOPPED:
            logger.info(f"Component {component_id} is already stopped")
            return True
            
        old_status = component.status
        component.status = ComponentStatus.STOPPING
        self._notify_status_change(component_id, old_status, component.status)
        
        try:
            success = self._stop_component_process(component)
            
            if success:
                component.status = ComponentStatus.STOPPED
                component.process = None
                component.pid = None
                component.start_time = None
            else:
                component.status = ComponentStatus.ERROR
                component.last_error = "Failed to stop component"
                
            self._notify_status_change(component_id, ComponentStatus.STOPPING, component.status)
            return success
            
        except Exception as e:
            logger.error(f"Error stopping component {component_id}: {e}")
            component.status = ComponentStatus.ERROR
            component.last_error = str(e)
            self._notify_status_change(component_id, ComponentStatus.STOPPING, component.status)
            return False
            
    def restart_component(self, component_id: str) -> bool:
        """Перезапуск компонента"""
        logger.info(f"Restarting component {component_id}")
        
        if not self.stop_component(component_id):
            return False
            
        # Ждем полной остановки
        time.sleep(2)
        
        return self.start_component(component_id)
        
    def start_all_components(self) -> bool:
        """Запуск всех компонентов в правильном порядке"""
        logger.info("Starting all components...")
        
        # Определяем порядок запуска на основе зависимостей
        start_order = self._get_start_order()
        
        for component_id in start_order:
            logger.info(f"Starting component: {component_id}")
            if not self.start_component(component_id):
                logger.error(f"Failed to start component {component_id}")
                return False
            
            # Ждем стабилизации перед запуском следующего
            # Увеличиваем время ожидания для более надежного запуска
            if component_id in ['redis', 'celery_worker', 'backend']:
                time.sleep(5)  # Больше времени для критических компонентов
            else:
                time.sleep(3)
            
        logger.info("All components started successfully")
        return True
        
    def stop_all_components(self) -> bool:
        """Остановка всех компонентов в обратном порядке"""
        logger.info("Stopping all components...")
        
        # Определяем порядок остановки (обратный порядку запуска)
        stop_order = list(reversed(self._get_start_order()))
        
        for component_id in stop_order:
            if self.components[component_id].status == ComponentStatus.RUNNING:
                logger.info(f"Stopping component: {component_id}")
                self.stop_component(component_id)
                time.sleep(1)
                
        logger.info("All components stopped")
        return True
        
    def _get_start_order(self) -> List[str]:
        """Определение порядка запуска компонентов на основе зависимостей"""
        order = []
        visited = set()
        
        def visit(component_id: str):
            if component_id in visited:
                return
            visited.add(component_id)
            
            component = self.components[component_id]
            for dep_id in component.dependencies:
                if dep_id in self.components:
                    visit(dep_id)
                    
            order.append(component_id)
            
        for component_id in self.components:
            visit(component_id)
            
        return order
        
    def _start_neo4j(self, component: ComponentInfo) -> bool:
        """Проверка Neo4j (управляется вручную)"""
        # Сначала запускаем скрипт проверки
        try:
            check_script = component.config.get('check_script')
            if check_script and Path(check_script).exists():
                result = subprocess.run([sys.executable, check_script], 
                                      capture_output=True, text=True, timeout=10)
                logger.info(f"Neo4j check result: {result.stdout}")
        except Exception as e:
            logger.warning(f"Neo4j check script failed: {e}")
            
        # Проверяем доступность
        try:
            response = requests.get(component.config['health_url'], timeout=5)
            if response.status_code == 200:
                component.status = ComponentStatus.RUNNING
                component.start_time = datetime.now()
                component.health = HealthStatus.HEALTHY
                logger.info("Neo4j is running")
                return True
        except requests.exceptions.RequestException:
            pass
            
        component.status = ComponentStatus.ERROR
        component.last_error = "Neo4j is not available. Please start Neo4j Desktop manually with neo4j/neopassword credentials."
        logger.error("Neo4j not available. Please start Neo4j Desktop manually.")
        return False
        
    def _start_redis(self, component: ComponentInfo) -> bool:
        """Запуск Redis Server"""
        try:
            # Проверяем, не запущен ли уже
            if component.port and self._is_port_in_use(component.port):
                component.status = ComponentStatus.RUNNING
                component.start_time = datetime.now()
                component.health = HealthStatus.HEALTHY
                logger.info("Redis is already running")
                return True
                
            # Проверяем наличие Redis
            project_root = Path(__file__).parent.parent
            redis_dir = project_root / 'redis'
            redis_exe = redis_dir / 'redis-server.exe'
            
            if not redis_exe.exists():
                # Проверяем альтернативный путь
                redis_exe = project_root / 'redis' / 'redis-server.exe'
                redis_dir = project_root / 'redis'
                
            if not redis_exe.exists():
                component.status = ComponentStatus.ERROR
                component.last_error = "Redis server executable not found"
                logger.error("Redis directory or executable not found")
                return False
            
            # Запускаем Redis в отдельном окне как в bat файле
            if sys.platform == "win32":
                # Exactly match bat file behavior: start /MIN "title" cmd /c "command"
                cmd_str = f"redis-server.exe redis.windows.conf"
                process = subprocess.Popen(
                    ['start', '/MIN', f'"{component.config["window_title"]}"', 'cmd', '/c', f'"{cmd_str}"'],
                    cwd=str(redis_dir),
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
                    shell=True  # Required for 'start' command
                )
            else:
                process = subprocess.Popen(
                    [str(redis_exe), str(redis_dir / 'redis.windows.conf')],
                    cwd=str(redis_dir),
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
                )
            
            component.process = process
            component.pid = process.pid
            component.start_time = datetime.now()
            
            # Ждем запуска
            if component.port:
                for _ in range(15):  # Увеличиваем время ожидания
                    if self._is_port_in_use(component.port):
                        component.status = ComponentStatus.RUNNING
                        component.health = HealthStatus.HEALTHY
                        logger.info("Redis started successfully")
                        return True
                    time.sleep(1)
                
            component.status = ComponentStatus.ERROR
            component.last_error = "Redis failed to start within timeout"
            return False
            
        except Exception as e:
            component.status = ComponentStatus.ERROR
            component.last_error = f"Failed to start Redis: {e}"
            logger.error(f"Error starting Redis: {e}")
            return False
            
    def _start_qdrant(self, component: ComponentInfo) -> bool:
        """Запуск Qdrant Vector Database"""
        try:
            # Проверяем Docker
            try:
                subprocess.run(['docker', 'version'], check=True, capture_output=True, timeout=5)
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                component.status = ComponentStatus.ERROR
                component.last_error = "Docker not available. Qdrant will not be started."
                logger.warning("Docker not available. System will use in-memory storage as fallback.")
                return False
            
            # Пытаемся запустить существующий контейнер
            try:
                result = subprocess.run(['docker', 'start', 'qdrant-bldr'], 
                                      check=True, capture_output=True, timeout=10)
                logger.info("Qdrant container started")
            except subprocess.CalledProcessError:
                # Создаем новый контейнер
                try:
                    subprocess.run(component.config['fallback_command'], 
                                 check=True, capture_output=True, timeout=30)
                    logger.info("Qdrant container created and started")
                except subprocess.CalledProcessError as e:
                    component.status = ComponentStatus.ERROR
                    component.last_error = f"Failed to create Qdrant container: {e}"
                    return False
            
            # Ждем готовности
            for _ in range(15):
                try:
                    response = requests.get(component.config['health_url'], timeout=2)
                    if response.status_code == 200:
                        component.status = ComponentStatus.RUNNING
                        component.start_time = datetime.now()
                        component.health = HealthStatus.HEALTHY
                        logger.info("Qdrant is ready")
                        return True
                except requests.exceptions.RequestException:
                    pass
                time.sleep(1)
                
            component.status = ComponentStatus.ERROR
            component.last_error = "Qdrant failed to become ready"
            return False
            
        except Exception as e:
            component.status = ComponentStatus.ERROR
            component.last_error = f"Failed to start Qdrant: {e}"
            logger.error(f"Error starting Qdrant: {e}")
            return False
        
    def _start_celery_worker(self, component: ComponentInfo) -> bool:
        """Запуск Celery Worker"""
        try:
            # Проверяем наличие core директории
            project_root = Path(__file__).parent.parent
            core_path = project_root / 'core'
            if not core_path.exists():
                component.status = ComponentStatus.ERROR
                component.last_error = "Core directory not found"
                return False
            
            # Запускаем в отдельном окне как в bat файле
            if sys.platform == "win32":
                # Exactly match bat file behavior: start /MIN "title" cmd /c "command"
                cmd_str = "celery -A core.celery_app worker --loglevel=info --concurrency=2"
                process = subprocess.Popen(
                    ['start', '/MIN', f'"{component.config["window_title"]}"', 'cmd', '/c', f'"{cmd_str}"'],
                    cwd=str(project_root),
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                    shell=True  # Required for 'start' command
                )
            else:
                process = subprocess.Popen(
                    component.config['start_command'],
                    cwd=str(project_root)
                )
            
            component.process = process
            component.pid = process.pid
            component.start_time = datetime.now()
            component.status = ComponentStatus.RUNNING
            component.health = HealthStatus.HEALTHY
            
            logger.info("Celery Worker started")
            return True
            
        except Exception as e:
            component.status = ComponentStatus.ERROR
            component.last_error = f"Failed to start Celery Worker: {e}"
            logger.error(f"Error starting Celery Worker: {e}")
            return False
            
    def _start_celery_beat(self, component: ComponentInfo) -> bool:
        """Запуск Celery Beat"""
        try:
            # Ждем немного после запуска Worker
            time.sleep(2)
            
            # Проверяем наличие core директории
            project_root = Path(__file__).parent.parent
            core_path = project_root / 'core'
            if not core_path.exists():
                component.status = ComponentStatus.ERROR
                component.last_error = "Core directory not found"
                return False
            
            # Запускаем в отдельном окне как в bat файле
            if sys.platform == "win32":
                # Exactly match bat file behavior: start /MIN "title" cmd /c "command"
                cmd_str = "celery -A core.celery_app beat --loglevel=info"
                process = subprocess.Popen(
                    ['start', '/MIN', f'"{component.config["window_title"]}"', 'cmd', '/c', f'"{cmd_str}"'],
                    cwd=str(project_root),
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                    shell=True  # Required for 'start' command
                )
            else:
                process = subprocess.Popen(
                    component.config['start_command'],
                    cwd=str(project_root)
                )
            
            component.process = process
            component.pid = process.pid
            component.start_time = datetime.now()
            component.status = ComponentStatus.RUNNING
            component.health = HealthStatus.HEALTHY
            
            logger.info("Celery Beat started")
            return True
            
        except Exception as e:
            component.status = ComponentStatus.ERROR
            component.last_error = f"Failed to start Celery Beat: {e}"
            logger.error(f"Error starting Celery Beat: {e}")
            return False

    def _start_backend(self, component: ComponentInfo) -> bool:
        """Запуск FastAPI Backend"""
        try:
            # Проверяем наличие bldr_api.py
            project_root = Path(__file__).parent.parent
            api_file = project_root / 'core' / 'bldr_api.py'
            if not api_file.exists():
                component.status = ComponentStatus.ERROR
                component.last_error = "bldr_api.py not found"
                return False
            
            # Убиваем процессы на порту компонента
            if component.port:
                self._kill_processes_on_port(component.port)
            time.sleep(3)
            
            env = os.environ.copy()
            env.update(component.config.get('env_vars', {}))
            
            # Запускаем в видимом окне как в bat файле
            if sys.platform == "win32":
                # Exactly match bat file behavior: start "title" cmd /k "command"
                cmd_str = f'start "{component.config["window_title"]}" cmd /k "python -m uvicorn core.bldr_api:app --host 127.0.0.1 --port 8000 --reload"'
                process = subprocess.Popen(
                    cmd_str,
                    cwd=str(project_root),  # This should be the project root directory
                    env=env,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                    shell=True  # Required for 'start' command
                )
            else:
                process = subprocess.Popen(
                    component.config['start_command'],
                    cwd=str(project_root),
                    env=env
                )
            
            component.process = process
            component.pid = process.pid
            component.start_time = datetime.now()
            
            # Ждем запуска (увеличено время ожидания)
            for _ in range(60):  # 60 секунд как в bat файле
                try:
                    response = requests.get(component.config['health_url'], timeout=2)
                    # Any response (even 404) means the server is running
                    if response.status_code:
                        component.status = ComponentStatus.RUNNING
                        component.health = HealthStatus.HEALTHY
                        logger.info("FastAPI Backend started successfully")
                        return True
                except requests.exceptions.RequestException:
                    pass
                    
                time.sleep(1)
                
            component.status = ComponentStatus.ERROR
            component.last_error = "FastAPI Backend failed to start within timeout"
            return False
            
        except Exception as e:
            component.status = ComponentStatus.ERROR
            component.last_error = f"Failed to start backend: {e}"
            logger.error(f"Error starting backend: {e}")
            return False
            
    def _start_frontend(self, component: ComponentInfo) -> bool:
        """Запуск Frontend Dashboard"""
        try:
            # Проверяем наличие package.json
            package_json = component.config['working_dir'] / 'package.json'
            if not package_json.exists():
                component.status = ComponentStatus.ERROR
                component.last_error = "Frontend dashboard not found (package.json missing)"
                return False
            
            # Убиваем процессы на порту компонента
            if component.port:
                self._kill_processes_on_port(component.port)
            time.sleep(5)
            
            # Проверяем, что backend полностью готов перед запуском frontend
            if 'backend' in component.dependencies:
                logger.info("Waiting for backend to be fully ready before starting frontend...")
                for _ in range(30):  # Ждем до 30 секунд
                    try:
                        response = requests.get('http://localhost:8000', timeout=2)
                        if response.status_code == 200:
                            logger.info("Backend is ready, proceeding with frontend start")
                            break
                    except requests.exceptions.RequestException:
                        pass
                    time.sleep(1)
            
            # Проверяем наличие node_modules
            node_modules = component.config['working_dir'] / 'node_modules'
            if not node_modules.exists():
                logger.info("Installing npm dependencies...")
                install_process = subprocess.run(
                    ['npm', 'install'],
                    cwd=component.config['working_dir'],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 минут на установку
                )
                if install_process.returncode != 0:
                    component.status = ComponentStatus.ERROR
                    component.last_error = f"npm install failed: {install_process.stderr}"
                    return False
            
            # Запускаем в видимом окне как в bat файле
            if sys.platform == "win32":
                # Exactly match bat file behavior: start "title" cmd /k "command"
                cmd_str = "npm run dev"
                process = subprocess.Popen(
                    ['start', f'"{component.config["window_title"]}"', 'cmd', '/k', f'"{cmd_str}"'],
                    cwd=str(component.config['working_dir']),
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                    shell=True  # Required for 'start' command
                )
            else:
                process = subprocess.Popen(
                    component.config['start_command'],
                    cwd=str(component.config['working_dir'])
                )
            
            component.process = process
            component.pid = process.pid
            component.start_time = datetime.now()
            
            # Ждем запуска (увеличено время как в bat файле)
            for _ in range(90):  # 90 секунд
                try:
                    response = requests.get(component.config['health_url'], timeout=2)
                    if response.status_code == 200:
                        component.status = ComponentStatus.RUNNING
                        component.health = HealthStatus.HEALTHY
                        logger.info("Frontend Dashboard started successfully")
                        return True
                except requests.exceptions.RequestException:
                    pass
                    
                time.sleep(1)
                
            component.status = ComponentStatus.ERROR
            component.last_error = "Frontend failed to start within timeout"
            return False
            
        except Exception as e:
            component.status = ComponentStatus.ERROR
            component.last_error = f"Failed to start frontend: {e}"
            logger.error(f"Error starting frontend: {e}")
            return False
            
    def _kill_processes_on_port(self, port: int):
        """Убийство процессов на указанном порту"""
        try:
            if sys.platform == "win32":
                # Получаем PID процессов на порту
                result = subprocess.run(
                    ['netstat', '-ano'], 
                    capture_output=True, 
                    text=True
                )
                
                for line in result.stdout.split('\n'):
                    if f':{port}' in line and 'LISTENING' in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            try:
                                # Проверяем, что PID - это число
                                pid_int = int(pid)
                                subprocess.run(['taskkill', '/F', '/PID', str(pid_int)], 
                                             capture_output=True, timeout=5)
                                logger.info(f"Killed process {pid_int} on port {port}")
                            except ValueError:
                                logger.warning(f"Invalid PID format: {pid}")
                            except Exception as e:
                                logger.warning(f"Failed to kill process {pid}: {e}")
            else:
                # Linux/Mac
                subprocess.run(['fuser', '-k', f'{port}/tcp'], 
                             capture_output=True, timeout=5)
                             
        except Exception as e:
            logger.warning(f"Error killing processes on port {port}: {e}")
            

            
    def _stop_component_process(self, component: ComponentInfo) -> bool:
        """Остановка процесса компонента"""
        if not component.process and not component.pid:
            return True
            
        try:
            if component.process:
                # Graceful shutdown
                if sys.platform == "win32":
                    component.process.terminate()
                else:
                    component.process.terminate()
                    
                # Ждем завершения
                try:
                    component.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # Force kill
                    component.process.kill()
                    component.process.wait()
                    
            elif component.pid:
                # Убиваем по PID
                try:
                    process = psutil.Process(component.pid)
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except psutil.TimeoutExpired:
                        process.kill()
                except psutil.NoSuchProcess:
                    pass  # Процесс уже завершен
                    
            return True
            
        except Exception as e:
            logger.error(f"Error stopping process: {e}")
            return False
            
    def _check_rag_training_health(self) -> HealthStatus:
        """Проверка здоровья RAG Training System"""
        try:
            response = requests.get('http://localhost:8000/api/tools/status', timeout=5)
            if response.status_code == 200:
                return HealthStatus.HEALTHY
            else:
                return HealthStatus.WARNING
        except:
            return HealthStatus.CRITICAL
            
    def start_monitoring(self):
        """Запуск мониторинга компонентов"""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Component monitoring started")
        
    def stop_monitoring(self):
        """Остановка мониторинга"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Component monitoring stopped")
        
    def _monitoring_loop(self):
        """Основной цикл мониторинга"""
        while self.monitoring_active:
            try:
                for component_id, component in self.components.items():
                    self._update_component_status(component)
                    self._update_component_metrics(component)
                    
                time.sleep(5)  # Обновление каждые 5 секунд
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)
                
    def _update_component_status(self, component: ComponentInfo):
        """Обновление статуса компонента"""
        if component.status not in [ComponentStatus.RUNNING, ComponentStatus.ERROR]:
            return
            
        old_status = component.status
        
        try:
            if component.id == 'neo4j':
                health_url = component.config.get('health_url')
                if health_url:
                    response = requests.get(health_url, timeout=3)
                    if response.status_code == 200:
                        component.status = ComponentStatus.RUNNING
                        component.health = HealthStatus.HEALTHY
                    else:
                        component.status = ComponentStatus.ERROR
                        component.health = HealthStatus.CRITICAL
                        
            elif component.process:
                if component.process.poll() is None:
                    # Процесс работает, проверяем health endpoint
                    health_url = component.config.get('health_url')
                    if health_url:
                        response = requests.get(health_url, timeout=3)
                        if response.status_code == 200:
                            component.status = ComponentStatus.RUNNING
                            component.health = HealthStatus.HEALTHY
                        else:
                            component.health = HealthStatus.WARNING
                else:
                    # Процесс завершился
                    component.status = ComponentStatus.ERROR
                    component.health = HealthStatus.CRITICAL
                    component.last_error = "Process terminated unexpectedly"
                    
            elif component.id == 'rag_training':
                component.health = self._check_rag_training_health()
                if component.health == HealthStatus.CRITICAL:
                    component.status = ComponentStatus.ERROR
                    
        except requests.exceptions.RequestException:
            component.health = HealthStatus.WARNING
        except Exception as e:
            component.status = ComponentStatus.ERROR
            component.health = HealthStatus.CRITICAL
            component.last_error = str(e)
            
        if old_status != component.status:
            self._notify_status_change(component.id, old_status, component.status)
            
    def _update_component_metrics(self, component: ComponentInfo):
        """Обновление метрик компонента"""
        try:
            if component.process and component.process.poll() is None:
                # Получаем метрики процесса
                process = psutil.Process(component.process.pid)
                component.metrics.cpu_usage = process.cpu_percent()
                component.metrics.memory_usage = process.memory_percent()
                
                if component.start_time:
                    component.metrics.uptime = int((datetime.now() - component.start_time).total_seconds())
                    
            # Проверяем response time для HTTP сервисов
            health_url = component.config.get('health_url')
            if health_url and component.status == ComponentStatus.RUNNING:
                start_time = time.time()
                try:
                    response = requests.get(health_url, timeout=3)
                    component.metrics.response_time = (time.time() - start_time) * 1000  # ms
                except:
                    component.metrics.response_time = None
                    
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        except Exception as e:
            logger.error(f"Error updating metrics for {component.id}: {e}")
            
    def get_system_status(self) -> Dict[str, Any]:
        """Получение общего статуса системы"""
        total_components = len(self.components)
        running_components = sum(1 for c in self.components.values() if c.status == ComponentStatus.RUNNING)
        error_components = sum(1 for c in self.components.values() if c.status == ComponentStatus.ERROR)
        
        if error_components > 0:
            overall_status = "critical"
        elif running_components == total_components:
            overall_status = "healthy"
        elif running_components > 0:
            overall_status = "degraded"
        else:
            overall_status = "offline"
            
        return {
            'overall_status': overall_status,
            'total_components': total_components,
            'running_components': running_components,
            'error_components': error_components,
            'components': {
                comp_id: {
                    'status': comp.status.value,
                    'health': comp.health.value,
                    'last_error': comp.last_error,
                    'uptime': comp.metrics.uptime,
                    'cpu_usage': comp.metrics.cpu_usage,
                    'memory_usage': comp.metrics.memory_usage,
                    'response_time': comp.metrics.response_time
                }
                for comp_id, comp in self.components.items()
            }
        }
        
    def export_status_report(self) -> str:
        """Экспорт отчета о статусе системы"""
        status = self.get_system_status()
        report = {
            'timestamp': datetime.now().isoformat(),
            'system_status': status,
            'detailed_components': {}
        }
        
        for comp_id, component in self.components.items():
            report['detailed_components'][comp_id] = {
                'id': component.id,
                'name': component.name,
                'type': component.type,
                'status': component.status.value,
                'health': component.health.value,
                'port': component.port,
                'dependencies': component.dependencies,
                'pid': component.pid,
                'start_time': component.start_time.isoformat() if component.start_time else None,
                'last_error': component.last_error,
                'metrics': {
                    'cpu_usage': component.metrics.cpu_usage,
                    'memory_usage': component.metrics.memory_usage,
                    'response_time': component.metrics.response_time,
                    'uptime': component.metrics.uptime
                }
            }
            
        return json.dumps(report, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # Тестирование менеджера компонентов
    manager = SystemComponentManager()
    
    def status_callback(component_id: str, old_status: ComponentStatus, new_status: ComponentStatus):
        print(f"Component {component_id}: {old_status.value} -> {new_status.value}")
        
    manager.add_status_callback(status_callback)
    manager.start_monitoring()
    
    try:
        # Тест получения статуса
        print("System Status:")
        status = manager.get_system_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
        
        # Тест запуска компонентов (только проверка, не запускаем реально)
        print("\nTesting component status checks...")
        for comp_id in manager.components:
            component = manager.get_component_status(comp_id)
            if component:
                print(f"{comp_id}: {component.status.value} ({component.health.value})")
    except Exception as e:
        print(f"Error in main: {e}")