"""
Реестр инструментов для агентов
"""

from typing import Dict, Optional, Any, List
from backend.core.tools.base_tool import Tool
from backend.core.tools.rag_tool import RAGTool
from backend.core.tools.calculator_tool import CalculatorTool
from backend.core.tools.document_tool import DocumentTool
import logging

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Реестр всех доступных инструментов"""
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Регистрация инструментов по умолчанию"""
        default_tools = [
            RAGTool(),
            CalculatorTool(),
            DocumentTool()
        ]
        
        for tool in default_tools:
            self.register_tool(tool)
    
    def register_tool(self, tool: Tool):
        """Регистрация инструмента"""
        self.tools[tool.tool_id] = tool
        logger.info(f"Tool {tool.tool_id} registered")
    
    def unregister_tool(self, tool_id: str) -> bool:
        """Удаление инструмента из реестра"""
        if tool_id in self.tools:
            del self.tools[tool_id]
            logger.info("Tool %s unregistered", tool_id)
            return True
        return False
    
    def get_tool(self, tool_id: str) -> Optional[Tool]:
        """Получение инструмента по ID"""
        return self.tools.get(tool_id)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """Список всех инструментов"""
        return [tool.get_schema() for tool in self.tools.values()]
    
    def execute_tool(self, tool_id: str, **kwargs) -> Dict:
        """Выполнение инструмента"""
        tool = self.get_tool(tool_id)
        if not tool:
            return {
                "success": False,
                "error": f"Tool {tool_id} not found"
            }
        
        if not tool.validate_params(**kwargs):
            return {
                "success": False,
                "error": "Invalid parameters"
            }
        
        try:
            return tool.execute(**kwargs)
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Глобальный реестр инструментов
tool_registry = ToolRegistry()

