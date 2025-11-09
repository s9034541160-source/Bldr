"""
Инструмент для работы с документами
"""

from backend.core.tools.base_tool import Tool
from backend.services.minio_service import minio_service
from typing import Dict, Any, Optional


class DocumentTool(Tool):
    """Инструмент для работы с документами в MinIO"""
    
    def __init__(self):
        super().__init__(
            tool_id="document_manager",
            name="Document Manager",
            description="Управление документами: загрузка, скачивание, поиск"
        )
    
    def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Выполнение действия с документом"""
        try:
            if action == "list":
                bucket = kwargs.get("bucket", "documents")
                prefix = kwargs.get("prefix", "")
                files = minio_service.list_files(bucket, prefix)
                return {
                    "success": True,
                    "action": action,
                    "files": files
                }
            
            elif action == "get_url":
                bucket = kwargs.get("bucket", "documents")
                object_name = kwargs.get("object_name")
                if not object_name:
                    return {
                        "success": False,
                        "error": "object_name is required"
                    }
                
                url = minio_service.get_file_url(
                    bucket=bucket,
                    object_name=object_name,
                    expires_seconds=kwargs.get("expires_seconds", 3600)
                )
                return {
                    "success": True,
                    "action": action,
                    "url": url
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "action": {
                "type": "string",
                "description": "Действие: 'list' или 'get_url'",
                "enum": ["list", "get_url"]
            },
            "bucket": {
                "type": "string",
                "description": "Имя bucket",
                "default": "documents"
            },
            "object_name": {
                "type": "string",
                "description": "Имя объекта (для get_url)"
            },
            "prefix": {
                "type": "string",
                "description": "Префикс для поиска (для list)"
            }
        }

