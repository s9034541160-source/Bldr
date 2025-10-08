# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: stop_component
# Основной источник: C:\Bldr\system_launcher\component_manager.py
# Дубликаты (для справки):
#   - C:\Bldr\bldr_system_launcher.py
#================================================================================
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