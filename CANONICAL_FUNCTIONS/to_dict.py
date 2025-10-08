# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: to_dict
# Основной источник: C:\Bldr\core\tools_system.py
# Дубликаты (для справки):
#   - C:\Bldr\integrated_structure_chunking_system.py
#   - C:\Bldr\core\meta_tools\dag_orchestrator.py
#   - C:\Bldr\core\meta_tools\dag_orchestrator.py
#================================================================================
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization"""
        from dataclasses import asdict
        return asdict(self)