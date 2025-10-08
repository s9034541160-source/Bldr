# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: start_all_components
# Основной источник: C:\Bldr\system_launcher\component_manager.py
# Дубликаты (для справки):
#   - C:\Bldr\bldr_system_launcher.py
#================================================================================
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