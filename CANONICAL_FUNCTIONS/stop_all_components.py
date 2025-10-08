# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: stop_all_components
# Основной источник: C:\Bldr\system_launcher\component_manager.py
# Дубликаты (для справки):
#   - C:\Bldr\bldr_system_launcher.py
#================================================================================
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