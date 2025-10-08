# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: generate_ppr
# Основной источник: C:\Bldr\core\tools_adapter.py
# Дубликаты (для справки):
#   - C:\Bldr\core\ppr_generator.py
#================================================================================
    def generate_ppr(self, project_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Генерация ППР (адаптер)"""
        if self.is_master_tools_available():
            try:
                result = self.master_tools.execute_tool("generate_ppr",
                                                      project_data=project_data, **kwargs)
                if result.is_success():
                    return {
                        "status": "success",
                        "ppr_data": result.data,
                        "execution_time": result.execution_time
                    }
                else:
                    return {"status": "error", "error": result.error}
            except Exception as e:
                return {"status": "error", "error": str(e)}
        else:
            return self._legacy_generate_ppr(project_data, **kwargs)