# core/coordinator_improved.py
"""
Улучшенный координатор с автоматической генерацией input_requirements
и улучшенной обработкой ошибок.
"""

import json
from typing import Dict, Any, List, Optional
from core.tools.base_tool import ToolManifest, ToolInterface, ToolParam, ToolResult, ToolParamType

class CoordinatorImproved:
    def __init__(self):
        self.available_tools: Dict[str, ToolManifest] = {}
        self._load_mock_tools()

    def _load_mock_tools(self):
        """Загружаем инструменты (в реальной системе - из реестра)."""
        # Mock loading - в реальной системе будет динамическая загрузка
        pass

    def _build_input_requirements(self, manifest: ToolManifest) -> Dict[str, Dict[str, Any]]:
        """Автоматически генерируем input_requirements из manifest.params."""
        requirements = {}
        
        for param in manifest.params:
            requirements[param.name] = {
                "type": param.type.value,
                "required": param.required,
                "description": param.description,
                "default": param.default
            }
            
            # Добавляем enum если есть
            if param.enum:
                requirements[param.name]["enum"] = param.enum
                
            # Добавляем UI hints если есть
            if param.ui:
                requirements[param.name]["ui"] = param.ui
        
        return requirements

    def get_tool_interface(self, tool_name: str) -> Optional[ToolInterface]:
        """Получаем интерфейс инструмента с автогенерированными input_requirements."""
        manifest = self.available_tools.get(tool_name)
        if not manifest:
            return None
        
        # Автоматически генерируем input_requirements
        auto_requirements = self._build_input_requirements(manifest)
        
        # Создаем ToolParam объекты из автогенерированных требований
        input_requirements = {}
        for param_name, param_info in auto_requirements.items():
            input_requirements[param_name] = ToolParam(
                name=param_name,
                type=ToolParamType(param_info["type"]),
                required=param_info["required"],
                description=param_info["description"],
                default=param_info.get("default"),
                enum=param_info.get("enum"),
                ui=param_info.get("ui")
            )
        
        # Создаем улучшенный интерфейс
        return ToolInterface(
            purpose=manifest.coordinator_interface.purpose,
            input_requirements=input_requirements,  # Автогенерированные!
            execution_flow=manifest.coordinator_interface.execution_flow,
            output_format=manifest.coordinator_interface.output_format,
            usage_guidelines=manifest.coordinator_interface.usage_guidelines,
            integration_notes=manifest.coordinator_interface.integration_notes
        )

    def _categorize_error(self, error: str, tool_name: str) -> str:
        """Категоризируем ошибки для лучших рекомендаций."""
        error_lower = error.lower()
        
        if any(keyword in error_lower for keyword in ['validation', 'required', 'missing', 'invalid']):
            return 'validation'
        elif any(keyword in error_lower for keyword in ['connection', 'database', 'network', 'timeout']):
            return 'dependency'
        elif any(keyword in error_lower for keyword in ['processing', 'calculation', 'computation']):
            return 'processing'
        elif any(keyword in error_lower for keyword in ['permission', 'access', 'denied']):
            return 'permission'
        else:
            return 'unknown'

    def _get_error_suggestions(self, error: str, tool_name: str, error_category: str) -> List[str]:
        """Получаем конкретные рекомендации по исправлению ошибок."""
        suggestions = {
            'validation': [
                f"Проверьте правильность параметров для инструмента {tool_name}",
                "Убедитесь, что все обязательные поля заполнены",
                "Проверьте типы данных параметров"
            ],
            'dependency': [
                "Проверьте подключение к базам данных",
                "Убедитесь, что все сервисы запущены",
                "Проверьте сетевые настройки"
            ],
            'processing': [
                "Попробуйте упростить запрос",
                "Проверьте корректность входных данных",
                "Попробуйте другой режим обработки"
            ],
            'permission': [
                "Проверьте права доступа к файлам",
                "Убедитесь, что у пользователя есть необходимые разрешения",
                "Проверьте настройки безопасности"
            ],
            'unknown': [
                "Попробуйте перезапустить инструмент",
                "Проверьте логи системы",
                "Обратитесь к администратору"
            ]
        }
        
        return suggestions.get(error_category, suggestions['unknown'])

    def plan_with_tool_interfaces(self, user_query: str) -> Dict[str, Any]:
        """Планирование с улучшенной обработкой ошибок."""
        print(f"\n--- Улучшенный координатор планирует: '{user_query}' ---")
        
        # Получаем интерфейсы всех доступных инструментов
        tool_interfaces_data = {}
        for name, manifest in self.available_tools.items():
            interface = self.get_tool_interface(name)
            if interface:
                tool_interfaces_data[name] = {
                    'purpose': interface.purpose,
                    'input_requirements': self._build_input_requirements(manifest),
                    'execution_flow': interface.execution_flow,
                    'output_format': interface.output_format
                }
        
        # Простое планирование на основе ключевых слов
        if any(keyword in user_query.lower() for keyword in ["поиск", "найти", "документы"]):
            return {
                "tool": "search_rag_database",
                "params": {
                    "query": user_query,
                    "doc_types": ["norms"]
                },
                "status": "success"
            }
        elif any(keyword in user_query.lower() for keyword in ["письмо", "создать", "написать"]):
            return {
                "tool": "generate_letter",
                "params": {
                    "description": user_query,
                    "letter_type": "business"
                },
                "status": "success"
            }
        elif any(keyword in user_query.lower() for keyword in ["бюджет", "расчет", "стоимость"]):
            return {
                "tool": "auto_budget",
                "params": {
                    "project_name": "Проект",
                    "base_cost": 1000000
                },
                "status": "success"
            }
        
        return {
            "tool": "none",
            "params": {},
            "status": "error",
            "message": "Не удалось найти подходящий инструмент для запроса"
        }

    def execute_plan_with_interface(self, plan: Dict[str, Any], actual_params: Dict[str, Any]) -> ToolResult:
        """Выполнение плана с улучшенной обработкой ошибок."""
        tool_name = plan.get("tool")
        if not tool_name or tool_name == "none":
            return ToolResult(
                status="error", 
                error=plan.get("message", "No tool specified in plan.")
            )

        manifest = self.available_tools.get(tool_name)
        if not manifest:
            return ToolResult(
                status="error", 
                error=f"Tool '{tool_name}' not found."
            )

        interface = self.get_tool_interface(tool_name)
        if not interface:
            return ToolResult(
                status="error", 
                error=f"Interface for tool '{tool_name}' not available."
            )

        # Валидация параметров с детальными сообщениями об ошибках
        validation_errors = []
        for param_name, param_def in interface.input_requirements.items():
            if param_def.required and param_name not in actual_params:
                validation_errors.append(f"Обязательный параметр '{param_name}' не предоставлен")
            elif param_name in actual_params:
                # Дополнительная валидация типов
                if param_def.type == ToolParamType.STRING and not isinstance(actual_params[param_name], str):
                    validation_errors.append(f"Параметр '{param_name}' должен быть строкой")
                elif param_def.type == ToolParamType.NUMBER and not isinstance(actual_params[param_name], (int, float)):
                    validation_errors.append(f"Параметр '{param_name}' должен быть числом")

        if validation_errors:
            error_msg = f"Ошибки валидации для инструмента '{tool_name}': " + "; ".join(validation_errors)
            return ToolResult(
                status="error", 
                error=error_msg,
                error_category="validation"
            )

        print(f"\n--- Координатор выполняет инструмент: '{tool_name}' ---")
        print(f"Параметры: {actual_params}")

        # В реальной системе здесь был бы вызов инструмента
        # Для демонстрации возвращаем успешный результат
        return ToolResult(
            status="success",
            data={
                "message": f"Инструмент '{tool_name}' выполнен успешно",
                "parameters": actual_params
            },
            execution_time=0.1
        )

    def handle_tool_error(self, error: str, tool_name: str, error_category: str) -> Dict[str, Any]:
        """Обработка ошибок инструментов с конкретными рекомендациями."""
        suggestions = self._get_error_suggestions(error, tool_name, error_category)
        
        return {
            "error": error,
            "tool": tool_name,
            "category": error_category,
            "suggestions": suggestions,
            "next_steps": [
                "Проверьте рекомендации выше",
                "Попробуйте исправить ошибку",
                "При необходимости обратитесь к документации"
            ]
        }

# Пример использования
if __name__ == "__main__":
    coordinator = CoordinatorImproved()
    
    # Демонстрация автогенерации input_requirements
    print("🔧 Демонстрация улучшенного координатора:")
    
    # Планирование
    user_query = "найти документы о бетоне"
    plan = coordinator.plan_with_tool_interfaces(user_query)
    print(f"План: {json.dumps(plan, indent=2, ensure_ascii=False)}")
    
    # Выполнение
    if plan.get("status") == "success":
        result = coordinator.execute_plan_with_interface(plan, plan["params"])
        print(f"Результат: {result.status}")
        if result.status == "error":
            error_info = coordinator.handle_tool_error(
                result.error, 
                plan["tool"], 
                getattr(result, 'error_category', 'unknown')
            )
            print(f"Обработка ошибки: {json.dumps(error_info, indent=2, ensure_ascii=False)}")
