"""
Инструмент калькулятор для агентов
"""

from backend.core.tools.base_tool import Tool
from typing import Dict, Any
import re


class CalculatorTool(Tool):
    """Инструмент для выполнения математических расчетов"""
    
    def __init__(self):
        super().__init__(
            tool_id="calculator",
            name="Calculator",
            description="Выполнение математических расчетов и вычислений"
        )
    
    def execute(self, expression: str, **kwargs) -> Dict[str, Any]:
        """Выполнение математического выражения"""
        try:
            # Безопасная оценка выражения
            # Разрешаем только математические операции
            allowed_chars = set("0123456789+-*/()., ")
            if not all(c in allowed_chars for c in expression):
                return {
                    "success": False,
                    "error": "Invalid characters in expression"
                }
            
            # Замена запятых на точки для десятичных чисел
            expression = expression.replace(",", ".")
            
            # Вычисление
            result = eval(expression)
            
            return {
                "success": True,
                "expression": expression,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "expression": {
                "type": "string",
                "description": "Математическое выражение для вычисления"
            }
        }

