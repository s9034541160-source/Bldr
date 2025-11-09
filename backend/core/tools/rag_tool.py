"""
Инструмент RAG для агентов
"""

from backend.core.tools.base_tool import Tool
from backend.services.rag_service import rag_service
from typing import Dict, Any


class RAGTool(Tool):
    """Инструмент для поиска информации через RAG"""
    
    def __init__(self):
        super().__init__(
            tool_id="rag_search",
            name="RAG Search",
            description="Поиск информации в индексированных документах через RAG"
        )
    
    def execute(self, query: str, limit: int = 5, **kwargs) -> Dict[str, Any]:
        """Выполнение поиска через RAG"""
        results = rag_service.search(
            query=query,
            limit=limit,
            score_threshold=kwargs.get("score_threshold", 0.7)
        )
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "count": len(results)
        }
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "query": {
                "type": "string",
                "description": "Поисковый запрос"
            },
            "limit": {
                "type": "integer",
                "description": "Максимальное количество результатов",
                "default": 5
            },
            "score_threshold": {
                "type": "float",
                "description": "Минимальный порог релевантности",
                "default": 0.7
            }
        }

