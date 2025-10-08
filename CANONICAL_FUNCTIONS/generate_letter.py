# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: generate_letter
# Основной источник: C:\Bldr\core\tools_adapter.py
# Дубликаты (для справки):
#   - C:\Bldr\core\letter_service.py
#================================================================================
    def generate_letter(self, description: str, **kwargs) -> Dict[str, Any]:
        """Генерация письма (адаптер для Master Tools)"""
        if self.is_master_tools_available():
            try:
                result = self.master_tools.execute_tool("generate_letter", 
                                                      description=description, **kwargs)
                if result.is_success():
                    return {
                        "status": "success",
                        "letter_text": result.data.get("letter_text", ""),
                        "template_id": result.data.get("template_id", ""),
                        "generated_at": result.data.get("generated_at", ""),
                        "execution_time": result.execution_time
                    }
                else:
                    return {
                        "status": "error", 
                        "error": result.error,
                        "details": result.metadata
                    }
            except Exception as e:
                logger.error(f"Error in generate_letter: {e}")
                return {"status": "error", "error": str(e)}
        else:
            # Fallback к legacy системе
            return self._legacy_generate_letter(description, **kwargs)