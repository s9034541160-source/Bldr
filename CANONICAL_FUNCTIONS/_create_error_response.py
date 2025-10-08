# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _create_error_response
# Основной источник: C:\Bldr\core\super_smart_coordinator.py
# Дубликаты (для справки):
#   - C:\Bldr\working_frontend_rag_integration.py
#================================================================================
    def _create_error_response(self, query: str, error: str) -> Dict[str, Any]:
        """Создание ответа об ошибке"""
        return {
            'response': f"❌ Произошла ошибка при обработке запроса: {query}",
            'error': error,
            'success': False,
            'suggested_next_steps': [
                "Попробуйте переформулировать запрос",
                "Уточните детали задачи",
                "Обратитесь к системному администратору"
            ],
            'timestamp': datetime.now().isoformat()
        }