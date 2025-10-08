# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: auto_budget
# Основной источник: C:\Bldr\core\tools_adapter.py
# Дубликаты (для справки):
#   - C:\Bldr\core\budget_auto.py
#================================================================================
    def auto_budget(self, estimate_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Автоматическое составление смет (адаптер)"""
        if self.is_master_tools_available():
            try:
                result = self.master_tools.execute_tool("auto_budget",
                                                      estimate_data=estimate_data, **kwargs)
                if result.is_success():
                    return {
                        "status": "success",
                        "budget_data": result.data,
                        "execution_time": result.execution_time,
                        "metadata": result.metadata
                    }
                else:
                    return {"status": "error", "error": result.error}
            except Exception as e:
                return {"status": "error", "error": str(e)}
        else:
            return self._legacy_auto_budget(estimate_data, **kwargs)