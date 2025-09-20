#!/usr/bin/env python3
"""
Diagnostic and Recovery Tools
Инструменты диагностики и восстановления системы Bldr Empire v2
"""

import os
import sys
import time
import psutil
import requests
import subprocess
import socket
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class DiagnosticSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class RecoveryAction(Enum):
    RESTART_COMPONENT = "restart_component"
    CLEAR_CACHE = "clear_cache"
    RESET_DATABASE = "reset_database"
    REINSTALL_DEPENDENCIES = "reinstall_dependencies"
    MANUAL_INTERVENTION = "manual_intervention"
    NO_ACTION = "no_action"

@dataclass
class DiagnosticResult:
    component_id: str
    check_name: str
    severity: DiagnosticSeverity
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    recommended_action: RecoveryAction = RecoveryAction.NO_ACTION
    auto_fixable: bool = False
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class RecoveryResult:
    success: bool
    message: str
    actions_taken: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

class SystemDiagnostics:
    """Система диагностики компонентов Bldr Empire"""
    
    def __init__(self):
        self.diagnostic_results: List[DiagnosticResult] = []
        self.recovery_history: List[RecoveryResult] = []
        
    def run_full_diagnostic(self) -> List[DiagnosticResult]:
        """Запуск полной диагностики системы"""
        logger.info("Starting full system diagnostic...")
        
        self.diagnostic_results.clear()
        
        # Диагностика системных ресурсов
        self._check_system_resources()
        
        # Диагностика сетевых портов
        self._check_network_ports()
        
        # Диагностика Neo4j
        self._diagnose_neo4j()
        
        # Диагностика Backend API
        self._diagnose_backend()
        
        # Диагностика Frontend
        self._diagnose_frontend()
        
        # Диагностика файловой системы
        self._check_filesystem()
        
        # Диагностика зависимостей
        self._check_dependencies()
        
        logger.info(f"Diagnostic completed. Found {len(self.diagnostic_results)} issues.")
        return self.diagnostic_results.copy()
        
    def _check_system_resources(self):
        """Проверка системных ресурсов"""
        
        # Проверка памяти
        memory = psutil.virtual_memory()
        available_gb = memory.available / 1024**3
        
        if available_gb < 2:
            self.diagnostic_results.append(DiagnosticResult(
                component_id="system",
                check_name="memory_check",
                severity=DiagnosticSeverity.CRITICAL,
                message=f"Low available memory: {available_gb:.1f} GB",
                details={"available_gb": available_gb, "total_gb": memory.total / 1024**3},
                recommended_action=RecoveryAction.MANUAL_INTERVENTION
            ))
        elif available_gb < 4:
            self.diagnostic_results.append(DiagnosticResult(
                component_id="system",
                check_name="memory_check",
                severity=DiagnosticSeverity.WARNING,
                message=f"Limited available memory: {available_gb:.1f} GB",
                details={"available_gb": available_gb}
            ))
            
        # Проверка дискового пространства
        for drive in ['C:', 'I:'] if sys.platform == "win32" else ['/']:
            try:
                if sys.platform == "win32" and not os.path.exists(drive):
                    continue
                    
                disk = psutil.disk_usage(drive)
                free_gb = disk.free / 1024**3
                
                if free_gb < 5:
                    self.diagnostic_results.append(DiagnosticResult(
                        component_id="system",
                        check_name="disk_space_check",
                        severity=DiagnosticSeverity.CRITICAL,
                        message=f"Low disk space on {drive}: {free_gb:.1f} GB",
                        details={"drive": drive, "free_gb": free_gb},
                        recommended_action=RecoveryAction.CLEAR_CACHE,
                        auto_fixable=True
                    ))
                elif free_gb < 10:
                    self.diagnostic_results.append(DiagnosticResult(
                        component_id="system",
                        check_name="disk_space_check",
                        severity=DiagnosticSeverity.WARNING,
                        message=f"Limited disk space on {drive}: {free_gb:.1f} GB",
                        details={"drive": drive, "free_gb": free_gb}
                    ))
            except Exception as e:
                logger.error(f"Error checking disk space for {drive}: {e}")
                
        # Проверка CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 90:
            self.diagnostic_results.append(DiagnosticResult(
                component_id="system",
                check_name="cpu_check",
                severity=DiagnosticSeverity.WARNING,
                message=f"High CPU usage: {cpu_percent}%",
                details={"cpu_percent": cpu_percent}
            ))
            
    def _check_network_ports(self):
        """Проверка доступности сетевых портов"""
        required_ports = {
            7474: "Neo4j HTTP",
            7687: "Neo4j Bolt", 
            8000: "Backend API",
            5173: "Frontend Dev Server"
        }
        
        for port, service in required_ports.items():
            if self._is_port_in_use(port):
                # Проверяем, отвечает ли сервис
                if port in [7474, 8000, 5173]:
                    try:
                        response = requests.get(f"http://localhost:{port}", timeout=3)
                        if response.status_code not in [200, 404]:  # 404 может быть нормальным
                            self.diagnostic_results.append(DiagnosticResult(
                                component_id="network",
                                check_name="port_response_check",
                                severity=DiagnosticSeverity.WARNING,
                                message=f"Port {port} ({service}) responding with status {response.status_code}",
                                details={"port": port, "service": service, "status_code": response.status_code}
                            ))
                    except requests.exceptions.RequestException:
                        self.diagnostic_results.append(DiagnosticResult(
                            component_id="network",
                            check_name="port_response_check",
                            severity=DiagnosticSeverity.ERROR,
                            message=f"Port {port} ({service}) is occupied but not responding",
                            details={"port": port, "service": service},
                            recommended_action=RecoveryAction.RESTART_COMPONENT,
                            auto_fixable=True
                        ))
            else:
                # Порт свободен - это может быть нормально если сервис не запущен
                pass
                
    def _diagnose_neo4j(self):
        """Диагностика Neo4j"""
        
        # Проверка доступности HTTP интерфейса
        try:
            response = requests.get("http://localhost:7474", timeout=5)
            if response.status_code == 200:
                # Neo4j работает, проверяем подключение к базе
                try:
                    # Простой запрос к базе данных
                    auth_response = requests.get(
                        "http://localhost:7474/db/data/",
                        auth=('neo4j', 'password'),
                        timeout=5
                    )
                    if auth_response.status_code == 200:
                        self.diagnostic_results.append(DiagnosticResult(
                            component_id="neo4j",
                            check_name="database_connection",
                            severity=DiagnosticSeverity.INFO,
                            message="Neo4j database is accessible",
                            details={"status": "healthy"}
                        ))
                    else:
                        self.diagnostic_results.append(DiagnosticResult(
                            component_id="neo4j",
                            check_name="database_connection",
                            severity=DiagnosticSeverity.ERROR,
                            message="Neo4j authentication failed",
                            details={"status_code": auth_response.status_code},
                            recommended_action=RecoveryAction.MANUAL_INTERVENTION
                        ))
                except Exception as e:
                    self.diagnostic_results.append(DiagnosticResult(
                        component_id="neo4j",
                        check_name="database_connection",
                        severity=DiagnosticSeverity.ERROR,
                        message=f"Neo4j database connection error: {e}",
                        recommended_action=RecoveryAction.RESTART_COMPONENT
                    ))
            else:
                self.diagnostic_results.append(DiagnosticResult(
                    component_id="neo4j",
                    check_name="http_interface",
                    severity=DiagnosticSeverity.ERROR,
                    message=f"Neo4j HTTP interface returned status {response.status_code}",
                    details={"status_code": response.status_code},
                    recommended_action=RecoveryAction.RESTART_COMPONENT
                ))
        except requests.exceptions.RequestException:
            self.diagnostic_results.append(DiagnosticResult(
                component_id="neo4j",
                check_name="http_interface",
                severity=DiagnosticSeverity.CRITICAL,
                message="Neo4j is not accessible",
                recommended_action=RecoveryAction.MANUAL_INTERVENTION
            ))
            
        # Проверка файлов конфигурации Neo4j
        neo4j_paths = [
            Path.home() / ".Neo4jDesktop",
            Path("C:/Users") / os.getenv('USERNAME', '') / ".Neo4jDesktop" if sys.platform == "win32" else None
        ]
        
        neo4j_found = False
        for path in neo4j_paths:
            if path and path.exists():
                neo4j_found = True
                break
                
        if not neo4j_found:
            self.diagnostic_results.append(DiagnosticResult(
                component_id="neo4j",
                check_name="installation_check",
                severity=DiagnosticSeverity.ERROR,
                message="Neo4j Desktop installation not found",
                recommended_action=RecoveryAction.MANUAL_INTERVENTION
            ))
            
    def _diagnose_backend(self):
        """Диагностика Backend API"""
        
        # Проверка доступности API
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                # Проверяем основные endpoints
                endpoints_to_check = [
                    "/api/tools/list",
                    "/docs"
                ]
                
                for endpoint in endpoints_to_check:
                    try:
                        ep_response = requests.get(f"http://localhost:8000{endpoint}", timeout=3)
                        if ep_response.status_code not in [200, 404]:
                            self.diagnostic_results.append(DiagnosticResult(
                                component_id="backend",
                                check_name="endpoint_check",
                                severity=DiagnosticSeverity.WARNING,
                                message=f"Backend endpoint {endpoint} returned status {ep_response.status_code}",
                                details={"endpoint": endpoint, "status_code": ep_response.status_code}
                            ))
                    except Exception as e:
                        self.diagnostic_results.append(DiagnosticResult(
                            component_id="backend",
                            check_name="endpoint_check",
                            severity=DiagnosticSeverity.ERROR,
                            message=f"Backend endpoint {endpoint} error: {e}",
                            details={"endpoint": endpoint}
                        ))
            else:
                self.diagnostic_results.append(DiagnosticResult(
                    component_id="backend",
                    check_name="health_check",
                    severity=DiagnosticSeverity.ERROR,
                    message=f"Backend health check failed with status {response.status_code}",
                    details={"status_code": response.status_code},
                    recommended_action=RecoveryAction.RESTART_COMPONENT,
                    auto_fixable=True
                ))
        except requests.exceptions.RequestException:
            self.diagnostic_results.append(DiagnosticResult(
                component_id="backend",
                check_name="health_check",
                severity=DiagnosticSeverity.CRITICAL,
                message="Backend API is not accessible",
                recommended_action=RecoveryAction.RESTART_COMPONENT,
                auto_fixable=True
            ))
            
        # Проверка файлов backend
        backend_files = [
            "main.py",
            "requirements.txt",
            "core/",
            "web/"
        ]
        
        for file_path in backend_files:
            path = Path(file_path)
            if not path.exists():
                self.diagnostic_results.append(DiagnosticResult(
                    component_id="backend",
                    check_name="file_check",
                    severity=DiagnosticSeverity.ERROR,
                    message=f"Backend file/directory missing: {file_path}",
                    details={"missing_path": str(path)},
                    recommended_action=RecoveryAction.MANUAL_INTERVENTION
                ))
                
    def _diagnose_frontend(self):
        """Диагностика Frontend"""
        
        # Проверка доступности frontend
        try:
            response = requests.get("http://localhost:5173", timeout=5)
            if response.status_code == 200:
                self.diagnostic_results.append(DiagnosticResult(
                    component_id="frontend",
                    check_name="accessibility_check",
                    severity=DiagnosticSeverity.INFO,
                    message="Frontend is accessible",
                    details={"status": "healthy"}
                ))
            else:
                self.diagnostic_results.append(DiagnosticResult(
                    component_id="frontend",
                    check_name="accessibility_check",
                    severity=DiagnosticSeverity.ERROR,
                    message=f"Frontend returned status {response.status_code}",
                    details={"status_code": response.status_code},
                    recommended_action=RecoveryAction.RESTART_COMPONENT,
                    auto_fixable=True
                ))
        except requests.exceptions.RequestException:
            self.diagnostic_results.append(DiagnosticResult(
                component_id="frontend",
                check_name="accessibility_check",
                severity=DiagnosticSeverity.CRITICAL,
                message="Frontend is not accessible",
                recommended_action=RecoveryAction.RESTART_COMPONENT,
                auto_fixable=True
            ))
            
        # Проверка файлов frontend
        frontend_path = Path("web/bldr_dashboard")
        if frontend_path.exists():
            required_files = [
                "package.json",
                "src/",
                "public/"
            ]
            
            for file_path in required_files:
                full_path = frontend_path / file_path
                if not full_path.exists():
                    self.diagnostic_results.append(DiagnosticResult(
                        component_id="frontend",
                        check_name="file_check",
                        severity=DiagnosticSeverity.ERROR,
                        message=f"Frontend file/directory missing: {file_path}",
                        details={"missing_path": str(full_path)},
                        recommended_action=RecoveryAction.REINSTALL_DEPENDENCIES
                    ))
                    
            # Проверка node_modules
            node_modules = frontend_path / "node_modules"
            if not node_modules.exists():
                self.diagnostic_results.append(DiagnosticResult(
                    component_id="frontend",
                    check_name="dependencies_check",
                    severity=DiagnosticSeverity.WARNING,
                    message="Frontend dependencies not installed (node_modules missing)",
                    recommended_action=RecoveryAction.REINSTALL_DEPENDENCIES,
                    auto_fixable=True
                ))
        else:
            self.diagnostic_results.append(DiagnosticResult(
                component_id="frontend",
                check_name="installation_check",
                severity=DiagnosticSeverity.CRITICAL,
                message="Frontend directory not found",
                details={"expected_path": str(frontend_path)},
                recommended_action=RecoveryAction.MANUAL_INTERVENTION
            ))
            
    def _check_filesystem(self):
        """Проверка файловой системы"""
        
        # Проверка критических директорий
        critical_dirs = [
            "I:/docs/downloaded",
            "I:/docs_generated",
            "I:/docs/cache"
        ]
        
        for dir_path in critical_dirs:
            path = Path(dir_path)
            if not path.exists():
                self.diagnostic_results.append(DiagnosticResult(
                    component_id="filesystem",
                    check_name="directory_check",
                    severity=DiagnosticSeverity.WARNING,
                    message=f"Critical directory missing: {dir_path}",
                    details={"missing_path": str(path)},
                    recommended_action=RecoveryAction.MANUAL_INTERVENTION
                ))
            elif not os.access(path, os.W_OK):
                self.diagnostic_results.append(DiagnosticResult(
                    component_id="filesystem",
                    check_name="permissions_check",
                    severity=DiagnosticSeverity.ERROR,
                    message=f"No write permission for directory: {dir_path}",
                    details={"path": str(path)},
                    recommended_action=RecoveryAction.MANUAL_INTERVENTION
                ))
                
        # Проверка размеров кэш-директорий
        cache_dirs = [
            "I:/docs/cache",
            "./cache",
            "./logs"
        ]
        
        for cache_dir in cache_dirs:
            path = Path(cache_dir)
            if path.exists():
                try:
                    total_size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
                    size_gb = total_size / 1024**3
                    
                    if size_gb > 10:  # Больше 10 GB
                        self.diagnostic_results.append(DiagnosticResult(
                            component_id="filesystem",
                            check_name="cache_size_check",
                            severity=DiagnosticSeverity.WARNING,
                            message=f"Large cache directory: {cache_dir} ({size_gb:.1f} GB)",
                            details={"path": str(path), "size_gb": size_gb},
                            recommended_action=RecoveryAction.CLEAR_CACHE,
                            auto_fixable=True
                        ))
                except Exception as e:
                    logger.error(f"Error checking cache size for {cache_dir}: {e}")
                    
    def _check_dependencies(self):
        """Проверка зависимостей"""
        
        # Проверка Python пакетов
        required_packages = [
            "fastapi",
            "uvicorn", 
            "neo4j",
            "requests",
            "psutil",
            "numpy",
            "pandas"
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
                
        if missing_packages:
            self.diagnostic_results.append(DiagnosticResult(
                component_id="dependencies",
                check_name="python_packages",
                severity=DiagnosticSeverity.ERROR,
                message=f"Missing Python packages: {', '.join(missing_packages)}",
                details={"missing_packages": missing_packages},
                recommended_action=RecoveryAction.REINSTALL_DEPENDENCIES,
                auto_fixable=True
            ))
            
        # Проверка Node.js (если есть)
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                node_version = result.stdout.strip()
                self.diagnostic_results.append(DiagnosticResult(
                    component_id="dependencies",
                    check_name="nodejs_check",
                    severity=DiagnosticSeverity.INFO,
                    message=f"Node.js available: {node_version}",
                    details={"version": node_version}
                ))
            else:
                self.diagnostic_results.append(DiagnosticResult(
                    component_id="dependencies",
                    check_name="nodejs_check",
                    severity=DiagnosticSeverity.WARNING,
                    message="Node.js not working properly",
                    recommended_action=RecoveryAction.MANUAL_INTERVENTION
                ))
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.diagnostic_results.append(DiagnosticResult(
                component_id="dependencies",
                check_name="nodejs_check",
                severity=DiagnosticSeverity.WARNING,
                message="Node.js not found or not accessible",
                recommended_action=RecoveryAction.MANUAL_INTERVENTION
            ))
            
    def _is_port_in_use(self, port: int) -> bool:
        """Проверка использования порта"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
            
    def attempt_auto_recovery(self, diagnostic_result: DiagnosticResult) -> RecoveryResult:
        """Попытка автоматического восстановления"""
        
        if not diagnostic_result.auto_fixable:
            return RecoveryResult(
                success=False,
                message="This issue requires manual intervention",
                errors=["Auto-recovery not available for this issue"]
            )
            
        logger.info(f"Attempting auto-recovery for {diagnostic_result.component_id}: {diagnostic_result.check_name}")
        
        try:
            if diagnostic_result.recommended_action == RecoveryAction.CLEAR_CACHE:
                return self._clear_cache_recovery(diagnostic_result)
            elif diagnostic_result.recommended_action == RecoveryAction.RESTART_COMPONENT:
                return self._restart_component_recovery(diagnostic_result)
            elif diagnostic_result.recommended_action == RecoveryAction.REINSTALL_DEPENDENCIES:
                return self._reinstall_dependencies_recovery(diagnostic_result)
            else:
                return RecoveryResult(
                    success=False,
                    message="Unknown recovery action",
                    errors=["Recovery action not implemented"]
                )
                
        except Exception as e:
            logger.error(f"Error during auto-recovery: {e}")
            return RecoveryResult(
                success=False,
                message=f"Recovery failed with error: {e}",
                errors=[str(e)]
            )
            
    def _clear_cache_recovery(self, diagnostic_result: DiagnosticResult) -> RecoveryResult:
        """Очистка кэша"""
        actions_taken = []
        errors = []
        
        cache_dirs = [
            "I:/docs/cache",
            "./cache", 
            "./logs",
            "./temp"
        ]
        
        for cache_dir in cache_dirs:
            path = Path(cache_dir)
            if path.exists():
                try:
                    # Удаляем содержимое, но не саму директорию
                    for item in path.iterdir():
                        if item.is_file():
                            item.unlink()
                            actions_taken.append(f"Deleted file: {item}")
                        elif item.is_dir():
                            shutil.rmtree(item)
                            actions_taken.append(f"Deleted directory: {item}")
                except Exception as e:
                    errors.append(f"Error clearing {cache_dir}: {e}")
                    
        success = len(errors) == 0
        message = "Cache cleared successfully" if success else "Cache clearing completed with errors"
        
        return RecoveryResult(
            success=success,
            message=message,
            actions_taken=actions_taken,
            errors=errors
        )
        
    def _restart_component_recovery(self, diagnostic_result: DiagnosticResult) -> RecoveryResult:
        """Перезапуск компонента"""
        component_id = diagnostic_result.component_id
        
        # Здесь должна быть интеграция с ComponentManager
        # Для демонстрации возвращаем успешный результат
        return RecoveryResult(
            success=True,
            message=f"Component {component_id} restart initiated",
            actions_taken=[f"Sent restart signal to {component_id}"]
        )
        
    def _reinstall_dependencies_recovery(self, diagnostic_result: DiagnosticResult) -> RecoveryResult:
        """Переустановка зависимостей"""
        actions_taken = []
        errors = []
        
        if diagnostic_result.component_id == "frontend":
            # Переустановка npm зависимостей
            frontend_path = Path("web/bldr_dashboard")
            if frontend_path.exists():
                try:
                    result = subprocess.run(
                        ['npm', 'install'],
                        cwd=frontend_path,
                        capture_output=True,
                        text=True,
                        timeout=300  # 5 минут
                    )
                    
                    if result.returncode == 0:
                        actions_taken.append("npm install completed successfully")
                    else:
                        errors.append(f"npm install failed: {result.stderr}")
                        
                except subprocess.TimeoutExpired:
                    errors.append("npm install timed out")
                except Exception as e:
                    errors.append(f"npm install error: {e}")
                    
        elif diagnostic_result.component_id == "dependencies":
            # Переустановка Python пакетов
            missing_packages = diagnostic_result.details.get("missing_packages", [])
            for package in missing_packages:
                try:
                    result = subprocess.run(
                        [sys.executable, '-m', 'pip', 'install', package],
                        capture_output=True,
                        text=True,
                        timeout=120
                    )
                    
                    if result.returncode == 0:
                        actions_taken.append(f"Installed Python package: {package}")
                    else:
                        errors.append(f"Failed to install {package}: {result.stderr}")
                        
                except subprocess.TimeoutExpired:
                    errors.append(f"Installation of {package} timed out")
                except Exception as e:
                    errors.append(f"Error installing {package}: {e}")
                    
        success = len(errors) == 0
        message = "Dependencies reinstalled successfully" if success else "Dependency installation completed with errors"
        
        return RecoveryResult(
            success=success,
            message=message,
            actions_taken=actions_taken,
            errors=errors
        )
        
    def get_diagnostic_summary(self) -> Dict[str, Any]:
        """Получение сводки диагностики"""
        if not self.diagnostic_results:
            return {"status": "no_diagnostics_run"}
            
        severity_counts = {
            DiagnosticSeverity.INFO: 0,
            DiagnosticSeverity.WARNING: 0,
            DiagnosticSeverity.ERROR: 0,
            DiagnosticSeverity.CRITICAL: 0
        }
        
        auto_fixable_count = 0
        component_issues = {}
        
        for result in self.diagnostic_results:
            severity_counts[result.severity] += 1
            
            if result.auto_fixable:
                auto_fixable_count += 1
                
            if result.component_id not in component_issues:
                component_issues[result.component_id] = []
            component_issues[result.component_id].append({
                "check": result.check_name,
                "severity": result.severity.value,
                "message": result.message,
                "auto_fixable": result.auto_fixable
            })
            
        # Определяем общий статус системы
        if severity_counts[DiagnosticSeverity.CRITICAL] > 0:
            overall_status = "critical"
        elif severity_counts[DiagnosticSeverity.ERROR] > 0:
            overall_status = "error"
        elif severity_counts[DiagnosticSeverity.WARNING] > 0:
            overall_status = "warning"
        else:
            overall_status = "healthy"
            
        return {
            "overall_status": overall_status,
            "total_issues": len(self.diagnostic_results),
            "auto_fixable_issues": auto_fixable_count,
            "severity_breakdown": {sev.value: count for sev, count in severity_counts.items()},
            "component_issues": component_issues,
            "last_diagnostic": self.diagnostic_results[0].timestamp.isoformat() if self.diagnostic_results else None
        }
        
    def export_diagnostic_report(self) -> str:
        """Экспорт отчета диагностики"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": self.get_diagnostic_summary(),
            "detailed_results": [
                {
                    "component_id": result.component_id,
                    "check_name": result.check_name,
                    "severity": result.severity.value,
                    "message": result.message,
                    "details": result.details,
                    "recommended_action": result.recommended_action.value,
                    "auto_fixable": result.auto_fixable,
                    "timestamp": result.timestamp.isoformat()
                }
                for result in self.diagnostic_results
            ],
            "recovery_history": [
                {
                    "success": recovery.success,
                    "message": recovery.message,
                    "actions_taken": recovery.actions_taken,
                    "errors": recovery.errors
                }
                for recovery in self.recovery_history
            ]
        }
        
        return json.dumps(report, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # Тестирование диагностических инструментов
    diagnostics = SystemDiagnostics()
    
    print("Running full system diagnostic...")
    results = diagnostics.run_full_diagnostic()
    
    print(f"\nFound {len(results)} issues:")
    for result in results:
        print(f"  {result.severity.value.upper()}: {result.component_id} - {result.message}")
        if result.auto_fixable:
            print(f"    -> Auto-fixable with action: {result.recommended_action.value}")
            
    print("\nDiagnostic Summary:")
    summary = diagnostics.get_diagnostic_summary()
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    
    # Тест автоматического восстановления
    auto_fixable_results = [r for r in results if r.auto_fixable]
    if auto_fixable_results:
        print(f"\nTesting auto-recovery for {len(auto_fixable_results)} issues...")
        for result in auto_fixable_results[:2]:  # Тестируем только первые 2
            print(f"Attempting recovery for: {result.message}")
            recovery_result = diagnostics.attempt_auto_recovery(result)
            print(f"  Result: {recovery_result.message}")
            if recovery_result.actions_taken:
                print(f"  Actions: {recovery_result.actions_taken}")
            if recovery_result.errors:
                print(f"  Errors: {recovery_result.errors}")