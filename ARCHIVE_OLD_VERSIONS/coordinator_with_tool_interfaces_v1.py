# core/coordinator_with_tool_interfaces.py
"""
Координатор с поддержкой универсального представления инструментов.
Использует coordinator_interface для динамического планирования.
"""

import json
from typing import Dict, List, Any, Optional
from core.tools.base_tool import tool_registry, ToolInterface

class CoordinatorWithToolInterfaces:
    """Координатор с поддержкой универсального представления инструментов."""
    
    def __init__(self):
        self.tools_system = None
        self.available_tools = []
        self.tool_interfaces = {}
    
    def set_tools_system(self, tools_system):
        """Установить систему инструментов."""
        self.tools_system = tools_system
        self._load_tool_interfaces()
    
    def _load_tool_interfaces(self):
        """Загрузить интерфейсы всех доступных инструментов."""
        if not self.tools_system:
            return
        
        # Получаем список доступных инструментов
        if hasattr(self.tools_system, 'get_available_tools'):
            self.available_tools = self.tools_system.get_available_tools()
        else:
            # Fallback: используем статический список
            self.available_tools = [
                'search_rag_database',
                'generate_letter', 
                'auto_budget'
            ]
        
        # Загружаем интерфейсы инструментов
        for tool_name in self.available_tools:
            interface = self._get_tool_interface(tool_name)
            if interface:
                self.tool_interfaces[tool_name] = interface
    
    def _get_tool_interface(self, tool_name: str) -> Optional[ToolInterface]:
        """Получить универсальное представление инструмента."""
        if self.tools_system and hasattr(self.tools_system, 'get_tool_manifest'):
            manifest = self.tools_system.get_tool_manifest(tool_name)
            if manifest and hasattr(manifest, 'coordinator_interface'):
                return manifest.coordinator_interface
        
        # Fallback: получаем из реестра
        return tool_registry.get_tool_interface(tool_name)
    
    def get_tool_capabilities(self, tool_name: str) -> Dict[str, Any]:
        """Получить возможности инструмента."""
        interface = self.tool_interfaces.get(tool_name)
        if not interface:
            return {}
        
        return {
            "purpose": interface.purpose,
            "input_params": list(interface.input_requirements.keys()),
            "output_format": interface.output_format,
            "execution_steps": len(interface.execution_flow),
            "guidelines": interface.usage_guidelines
        }
    
    def find_tools_by_purpose(self, purpose_keywords: List[str]) -> List[str]:
        """Найти инструменты по ключевым словам в назначении."""
        matching_tools = []
        for tool_name, interface in self.tool_interfaces.items():
            purpose_lower = interface.purpose.lower()
            if any(keyword.lower() in purpose_lower for keyword in purpose_keywords):
                matching_tools.append(tool_name)
        return matching_tools
    
    def plan_with_tool_interfaces(self, user_query: str) -> Dict[str, Any]:
        """Планирование с использованием интерфейсов инструментов."""
        
        # Анализируем запрос пользователя
        query_keywords = self._extract_keywords(user_query)
        
        # Находим подходящие инструменты
        suitable_tools = self._find_suitable_tools(query_keywords)
        
        # Формируем план на основе интерфейсов
        plan = self._generate_plan_with_interfaces(user_query, suitable_tools)
        
        return plan
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Извлечь ключевые слова из запроса."""
        # Простая логика извлечения ключевых слов
        keywords = []
        
        # Ключевые слова для поиска
        if any(word in query.lower() for word in ['найти', 'поиск', 'искать', 'найти', 'поиск']):
            keywords.append('поиск')
        
        # Ключевые слова для генерации документов
        if any(word in query.lower() for word in ['письмо', 'документ', 'создать', 'написать', 'сгенерировать']):
            keywords.append('генерация')
        
        # Ключевые слова для бюджета
        if any(word in query.lower() for word in ['бюджет', 'стоимость', 'расчет', 'цена', 'деньги']):
            keywords.append('бюджет')
        
        return keywords
    
    def _find_suitable_tools(self, keywords: List[str]) -> List[str]:
        """Найти подходящие инструменты по ключевым словам."""
        suitable_tools = []
        
        for tool_name, interface in self.tool_interfaces.items():
            # Проверяем соответствие по назначению
            purpose_lower = interface.purpose.lower()
            if any(keyword.lower() in purpose_lower for keyword in keywords):
                suitable_tools.append(tool_name)
        
        return suitable_tools
    
    def _generate_plan_with_interfaces(self, user_query: str, suitable_tools: List[str]) -> Dict[str, Any]:
        """Генерировать план с использованием интерфейсов инструментов."""
        
        if not suitable_tools:
            return {
                "status": "error",
                "error": "Не найдены подходящие инструменты для выполнения запроса",
                "suggestions": "Попробуйте переформулировать запрос или использовать другие ключевые слова"
            }
        
        # Выбираем лучший инструмент
        best_tool = self._select_best_tool(user_query, suitable_tools)
        
        if not best_tool:
            return {
                "status": "error", 
                "error": "Не удалось выбрать подходящий инструмент"
            }
        
        # Получаем интерфейс выбранного инструмента
        interface = self.tool_interfaces.get(best_tool)
        if not interface:
            return {
                "status": "error",
                "error": f"Интерфейс инструмента {best_tool} недоступен"
            }
        
        # Генерируем план на основе интерфейса
        plan = {
            "status": "success",
            "selected_tool": best_tool,
            "tool_purpose": interface.purpose,
            "execution_flow": interface.execution_flow,
            "input_requirements": {
                param_name: {
                    "type": param.type,
                    "required": param.required,
                    "description": param.description
                }
                for param_name, param in interface.input_requirements.items()
            },
            "expected_output": interface.output_format,
            "usage_guidelines": interface.usage_guidelines,
            "integration_notes": interface.integration_notes
        }
        
        return plan
    
    def _select_best_tool(self, user_query: str, suitable_tools: List[str]) -> Optional[str]:
        """Выбрать лучший инструмент из подходящих."""
        if not suitable_tools:
            return None
        
        # Простая логика выбора: берем первый подходящий
        # В будущем можно добавить более сложную логику ранжирования
        return suitable_tools[0]
    
    def execute_plan_with_interface(self, plan: Dict[str, Any], user_input: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнить план с использованием интерфейса инструмента."""
        
        if plan.get("status") != "success":
            return plan
        
        selected_tool = plan.get("selected_tool")
        if not selected_tool:
            return {
                "status": "error",
                "error": "Не указан инструмент для выполнения"
            }
        
        # Получаем интерфейс инструмента
        interface = self.tool_interfaces.get(selected_tool)
        if not interface:
            return {
                "status": "error",
                "error": f"Интерфейс инструмента {selected_tool} недоступен"
            }
        
        # Валидируем входные данные на основе интерфейса
        validation_result = self._validate_input_with_interface(user_input, interface)
        if not validation_result["valid"]:
            return {
                "status": "error",
                "error": f"Ошибка валидации входных данных: {', '.join(validation_result['errors'])}"
            }
        
        # Выполняем инструмент
        try:
            if self.tools_system and hasattr(self.tools_system, 'execute_tool'):
                result = self.tools_system.execute_tool(selected_tool, **user_input)
                return result
            else:
                return {
                    "status": "error",
                    "error": "Система инструментов недоступна"
                }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Ошибка выполнения инструмента: {str(e)}"
            }
    
    def _validate_input_with_interface(self, user_input: Dict[str, Any], interface: ToolInterface) -> Dict[str, Any]:
        """Валидировать входные данные на основе интерфейса инструмента."""
        errors = []
        
        # Проверяем обязательные параметры
        for param_name, param in interface.input_requirements.items():
            if param.required and param_name not in user_input:
                errors.append(f"Обязательный параметр '{param_name}' не предоставлен")
        
        # Проверяем типы данных
        for param_name, param in interface.input_requirements.items():
            if param_name in user_input:
                value = user_input[param_name]
                if not self._validate_parameter_type(value, param):
                    errors.append(f"Параметр '{param_name}' имеет неверный тип")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _validate_parameter_type(self, value: Any, param) -> bool:
        """Валидировать тип параметра."""
        # Простая валидация типов
        if param.type == "string" and not isinstance(value, str):
            return False
        elif param.type == "number" and not isinstance(value, (int, float)):
            return False
        elif param.type == "boolean" and not isinstance(value, bool):
            return False
        elif param.type == "array" and not isinstance(value, list):
            return False
        elif param.type == "object" and not isinstance(value, dict):
            return False
        
        return True
    
    def get_all_tool_interfaces(self) -> Dict[str, ToolInterface]:
        """Получить все интерфейсы инструментов."""
        return self.tool_interfaces.copy()
    
    def get_tool_interface_summary(self) -> Dict[str, Any]:
        """Получить краткую сводку по всем инструментам."""
        summary = {}
        for tool_name, interface in self.tool_interfaces.items():
            summary[tool_name] = {
                "purpose": interface.purpose,
                "input_params": list(interface.input_requirements.keys()),
                "execution_steps": len(interface.execution_flow)
            }
        return summary
