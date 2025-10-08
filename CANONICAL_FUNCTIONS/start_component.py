# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: start_component
# Основной источник: C:\Bldr\system_launcher\component_manager.py
# Дубликаты (для справки):
#   - C:\Bldr\bldr_system_launcher.py
#================================================================================
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