# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _generate_filename
# Основной источник: C:\Bldr\core\super_smart_coordinator.py
# Дубликаты (для справки):
#   - C:\Bldr\core\norms_updater.py
#================================================================================
    def _generate_filename(self, context: RequestContext, step: Dict) -> str:
        """Генерация имени файла"""
        domain = context.construction_domain
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        
        base_name = f"{domain}_{timestamp}"
        return f"{base_name}.docx"