"""
API эндпоинты для работы с инструментами
"""

from fastapi import APIRouter, Depends
from backend.core.tools.registry import tool_registry
from backend.middleware.rbac import get_current_user
from backend.models.auth import User

router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("/")
async def list_tools(current_user: User = Depends(get_current_user)):
    """Список всех доступных инструментов"""
    return {"tools": tool_registry.list_tools()}


@router.get("/{tool_id}")
async def get_tool_info(
    tool_id: str,
    current_user: User = Depends(get_current_user)
):
    """Информация об инструменте"""
    tool = tool_registry.get_tool(tool_id)
    if not tool:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Tool not found")
    
    return tool.get_schema()

