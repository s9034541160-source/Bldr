"""
API эндпоинты для работы с инструментами агентов.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.core.tools.registry import tool_registry
from backend.middleware.rbac import get_current_user
from backend.models.auth import User

router = APIRouter(prefix="/tools", tags=["tools"])


class ToolSchema(BaseModel):
    tool_id: str = Field(..., alias="tool_id")
    name: str
    description: str
    parameters: Dict[str, Any]

    @classmethod
    def from_raw(cls, raw: Dict[str, Any]) -> "ToolSchema":
        return cls(
            tool_id=raw["tool_id"],
            name=raw.get("name", raw["tool_id"]),
            description=raw.get("description", ""),
            parameters=raw.get("parameters", {}),
        )


class ToolListResponse(BaseModel):
    tools: list[ToolSchema]


class ToolExecuteRequest(BaseModel):
    tool_id: str = Field(..., description="Идентификатор инструмента")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Параметры выполнения")


class ToolRegisterRequest(BaseModel):
    import_path: str = Field(
        ...,
        description="Полный путь до класса инструмента, например 'backend.core.tools.rag_tool.RAGTool'",
    )


@router.get("/", response_model=ToolListResponse)
async def list_tools(current_user: User = Depends(get_current_user)) -> ToolListResponse:
    """Список всех доступных инструментов."""
    schemas = [ToolSchema.from_raw(schema) for schema in tool_registry.list_tools()]
    return ToolListResponse(tools=schemas)


@router.get("/{tool_id}", response_model=ToolSchema)
async def get_tool_info(tool_id: str, current_user: User = Depends(get_current_user)) -> ToolSchema:
    """Информация об инструменте."""
    tool = tool_registry.get_tool(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return ToolSchema.from_raw(tool.get_schema())


@router.post("/execute")
async def execute_tool(
    request: ToolExecuteRequest,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Выполнение инструмента."""
    return tool_registry.execute_tool(request.tool_id, **request.parameters)


@router.post("/register")
async def register_tool(request: ToolRegisterRequest, current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """Регистрация нового инструмента (требует прав администратора)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only admins can register tools")

    module_path, _, class_name = request.import_path.rpartition(".")
    if not module_path or not class_name:
        raise HTTPException(status_code=400, detail="Invalid import path")

    try:
        module = import_module(module_path)
        tool_class = getattr(module, class_name)
        tool_instance = tool_class()
        tool_registry.register_tool(tool_instance)
        return {"status": "registered", "tool_id": tool_instance.tool_id}
    except (ModuleNotFoundError, AttributeError) as exc:
        raise HTTPException(status_code=400, detail=f"Cannot import tool: {exc}")


@router.delete("/{tool_id}")
async def unregister_tool(tool_id: str, current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """Удаление инструмента из реестра (требует прав администратора)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only admins can unregister tools")

    removed = tool_registry.unregister_tool(tool_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Tool not found")
    return {"status": "unregistered", "tool_id": tool_id}

