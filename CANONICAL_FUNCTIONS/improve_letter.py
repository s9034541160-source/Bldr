# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: improve_letter
# Основной источник: C:\Bldr\core\tools_adapter.py
# Дубликаты (для справки):
#   - C:\Bldr\core\letter_service.py
#================================================================================
    def improve_letter(self, draft: str, description: str = "", **kwargs) -> Dict[str, Any]:
        """Улучшение письма (адаптер)"""
        if self.is_master_tools_available():
            try:
                result = self.master_tools.execute_tool("improve_letter",
                                                      draft=draft,
                                                      description=description, **kwargs)
                if result.is_success():
                    return {
                        "status": "success",
                        "improved_text": result.data.get("improved_text", ""),
                        "original_draft": result.data.get("original_draft", ""),
                        "improved_at": result.data.get("improved_at", ""),
                        "execution_time": result.execution_time
                    }
                else:
                    return {"status": "error", "error": result.error}
            except Exception as e:
                return {"status": "error", "error": str(e)}
        else:
            return self._legacy_improve_letter(draft, description, **kwargs)