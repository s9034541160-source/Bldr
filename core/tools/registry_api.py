# core/tools/registry_api.py
"""
API для работы с реестром инструментов с поддержкой универсального представления.
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from core.tools.base_tool import tool_registry, ToolManifest, ToolInterface, ToolResult

router = APIRouter(prefix="/api/tools", tags=["tools"])

class ToolInfo(BaseModel):
    """Информация об инструменте для API."""
    name: str
    version: str
    title: str
    description: str
    category: str
    ui_placement: str
    enabled: bool
    system: bool
    purpose: str
    input_params: List[str]
    output_fields: List[str]
    execution_steps: int
    performance: str
    reliability: str

class ToolExecutionRequest(BaseModel):
    """Запрос на выполнение инструмента."""
    tool_name: str
    parameters: Dict[str, Any]

class ToolExecutionResponse(BaseModel):
    """Ответ на выполнение инструмента."""
    status: str
    data: Dict[str, Any]
    execution_time: float
    result_type: Optional[str] = None
    result_title: Optional[str] = None
    result_content: Optional[str] = None
    result_table: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None

@router.get("/list", response_model=Dict[str, Any])
async def get_tools_list(
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    enabled_only: bool = Query(True, description="Только включенные инструменты"),
    system_only: bool = Query(None, description="Только системные инструменты")
):
    """Получить список всех инструментов с фильтрацией."""
    try:
        tools = {}
        categories = {}
        
        for name, manifest in tool_registry.tools.items():
            # Применяем фильтры
            if enabled_only and not manifest.enabled:
                continue
            if category and manifest.category != category:
                continue
            if system_only is not None and manifest.system != system_only:
                continue
            
            # Создаем информацию об инструменте
            tool_info = ToolInfo(
                name=manifest.name,
                version=manifest.version,
                title=manifest.title,
                description=manifest.description,
                category=manifest.category,
                ui_placement=manifest.ui_placement,
                enabled=manifest.enabled,
                system=manifest.system,
                purpose=manifest.coordinator_interface.purpose,
                input_params=list(manifest.coordinator_interface.input_requirements.keys()),
                output_fields=list(manifest.coordinator_interface.output_format.get("result_fields", {}).keys()),
                execution_steps=len(manifest.coordinator_interface.execution_flow),
                performance=manifest.coordinator_interface.integration_notes.get("performance", "Неизвестно"),
                reliability=manifest.coordinator_interface.integration_notes.get("reliability", "Неизвестно")
            )
            
            tools[name] = tool_info.dict()
            
            # Подсчитываем категории
            cat = manifest.category
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "tools": tools,
            "categories": categories,
            "total_count": len(tools),
            "filters": {
                "category": category,
                "enabled_only": enabled_only,
                "system_only": system_only
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения списка инструментов: {str(e)}")

@router.get("/{tool_name}/info", response_model=Dict[str, Any])
async def get_tool_info(tool_name: str):
    """Получить подробную информацию об инструменте."""
    try:
        manifest = tool_registry.get_tool_manifest(tool_name)
        if not manifest:
            raise HTTPException(status_code=404, detail=f"Инструмент '{tool_name}' не найден")
        
        interface = manifest.coordinator_interface
        
        return {
            "manifest": {
                "name": manifest.name,
                "version": manifest.version,
                "title": manifest.title,
                "description": manifest.description,
                "category": manifest.category,
                "ui_placement": manifest.ui_placement,
                "enabled": manifest.enabled,
                "system": manifest.system,
                "entrypoint": manifest.entrypoint,
                "permissions": manifest.permissions,
                "tags": manifest.tags
            },
            "coordinator_interface": {
                "purpose": interface.purpose,
                "input_requirements": {
                    name: {
                        "type": param.type,
                        "required": param.required,
                        "description": param.description,
                        "default": param.default
                    }
                    for name, param in interface.input_requirements.items()
                },
                "execution_flow": interface.execution_flow,
                "output_format": interface.output_format,
                "usage_guidelines": interface.usage_guidelines,
                "integration_notes": interface.integration_notes
            },
            "capabilities": tool_registry.get_tool_capabilities(tool_name)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения информации об инструменте: {str(e)}")

@router.get("/{tool_name}/interface", response_model=ToolInterface)
async def get_tool_interface(tool_name: str):
    """Получить универсальное представление инструмента для координатора."""
    try:
        interface = tool_registry.get_tool_interface(tool_name)
        if not interface:
            raise HTTPException(status_code=404, detail=f"Интерфейс инструмента '{tool_name}' не найден")
        
        return interface
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения интерфейса инструмента: {str(e)}")

@router.get("/interfaces/all", response_model=Dict[str, ToolInterface])
async def get_all_interfaces():
    """Получить все интерфейсы инструментов."""
    try:
        interfaces = tool_registry.get_all_interfaces()
        return interfaces
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения интерфейсов: {str(e)}")

@router.get("/search", response_model=Dict[str, Any])
async def search_tools(
    purpose_keywords: List[str] = Query(..., description="Ключевые слова для поиска по назначению"),
    category: Optional[str] = Query(None, description="Фильтр по категории")
):
    """Поиск инструментов по ключевым словам в назначении."""
    try:
        matching_tools = tool_registry.find_tools_by_purpose(purpose_keywords)
        
        # Применяем фильтр по категории если указан
        if category:
            filtered_tools = []
            for tool_name in matching_tools:
                manifest = tool_registry.get_tool_manifest(tool_name)
                if manifest and manifest.category == category:
                    filtered_tools.append(tool_name)
            matching_tools = filtered_tools
        
        # Получаем информацию о найденных инструментах
        tools_info = {}
        for tool_name in matching_tools:
            manifest = tool_registry.get_tool_manifest(tool_name)
            if manifest:
                tools_info[tool_name] = {
                    "name": manifest.name,
                    "title": manifest.title,
                    "purpose": manifest.coordinator_interface.purpose,
                    "category": manifest.category,
                    "enabled": manifest.enabled
                }
        
        return {
            "matching_tools": matching_tools,
            "tools_info": tools_info,
            "search_keywords": purpose_keywords,
            "category_filter": category,
            "total_found": len(matching_tools)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка поиска инструментов: {str(e)}")

@router.post("/{tool_name}/execute", response_model=ToolExecutionResponse)
async def execute_tool(tool_name: str, request: ToolExecutionRequest):
    """Выполнить инструмент с заданными параметрами."""
    try:
        # Проверяем существование инструмента
        manifest = tool_registry.get_tool_manifest(tool_name)
        if not manifest:
            raise HTTPException(status_code=404, detail=f"Инструмент '{tool_name}' не найден")
        
        if not manifest.enabled:
            raise HTTPException(status_code=400, detail=f"Инструмент '{tool_name}' отключен")
        
        # Получаем интерфейс для валидации
        interface = manifest.coordinator_interface
        
        # Валидируем входные параметры
        validation_errors = []
        for param_name, param in interface.input_requirements.items():
            if param.required and param_name not in request.parameters:
                validation_errors.append(f"Обязательный параметр '{param_name}' не предоставлен")
        
        if validation_errors:
            raise HTTPException(status_code=400, detail=f"Ошибки валидации: {', '.join(validation_errors)}")
        
        # Выполняем инструмент
        try:
            # Импортируем и выполняем функцию инструмента
            module_path = manifest.entrypoint
            module_name, function_name = module_path.split(':')
            
            import importlib
            module = importlib.import_module(module_name)
            execute_function = getattr(module, function_name)
            
            result = execute_function(**request.parameters)
            
            return ToolExecutionResponse(
                status=result.get('status', 'success'),
                data=result.get('data', {}),
                execution_time=result.get('execution_time', 0),
                result_type=result.get('result_type'),
                result_title=result.get('result_title'),
                result_content=result.get('result_content'),
                result_table=result.get('result_table'),
                error=result.get('error')
            )
            
        except Exception as execution_error:
            return ToolExecutionResponse(
                status="error",
                data={},
                execution_time=0,
                error=f"Ошибка выполнения инструмента: {str(execution_error)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка выполнения инструмента: {str(e)}")

@router.get("/categories", response_model=Dict[str, int])
async def get_categories():
    """Получить список категорий инструментов с количеством."""
    try:
        categories = {}
        for name, manifest in tool_registry.tools.items():
            if manifest.enabled:
                cat = manifest.category
                categories[cat] = categories.get(cat, 0) + 1
        
        return categories
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения категорий: {str(e)}")

@router.get("/summary", response_model=Dict[str, Any])
async def get_tools_summary():
    """Получить сводку по всем инструментам."""
    try:
        total_tools = len(tool_registry.tools)
        enabled_tools = sum(1 for manifest in tool_registry.tools.values() if manifest.enabled)
        system_tools = sum(1 for manifest in tool_registry.tools.values() if manifest.system)
        
        categories = {}
        for manifest in tool_registry.tools.values():
            if manifest.enabled:
                cat = manifest.category
                categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "total_tools": total_tools,
            "enabled_tools": enabled_tools,
            "system_tools": system_tools,
            "categories": categories,
            "categories_count": len(categories)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения сводки: {str(e)}")
