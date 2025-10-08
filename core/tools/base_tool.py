# core/tools/base_tool.py
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Union
from enum import Enum

class ToolParamType(str, Enum):
    """Типы параметров инструментов."""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    ENUM = "enum"
    FILE = "file"

class ToolParam(BaseModel):
    """Параметр инструмента."""
    name: str
    type: ToolParamType
    required: bool = False
    default: Any = None
    description: str
    enum: Optional[List[Dict[str, str]]] = None
    ui: Optional[Dict[str, Any]] = None

class ToolInterface(BaseModel):
    """Универсальное представление инструмента для координатора."""
    purpose: str = Field(..., description="Назначение инструмента (кратко)")
    input_requirements: Dict[str, ToolParam] = Field(..., description="Требуемые параметры")
    execution_flow: List[str] = Field(..., description="Пошаговый процесс выполнения")
    output_format: Dict[str, Any] = Field(..., description="Структура результата")
    usage_guidelines: Dict[str, List[str]] = Field(..., description="Правила использования")
    integration_notes: Optional[Dict[str, Any]] = None

class ToolManifest(BaseModel):
    """Манифест инструмента."""
    name: str
    version: str
    title: str
    description: str
    category: str
    ui_placement: str
    enabled: bool = True
    system: bool = False
    entrypoint: str
    params: List[ToolParam]
    outputs: List[str]
    permissions: List[str] = []
    tags: List[str] = []
    result_display: Optional[Dict[str, Any]] = None
    documentation: Optional[Dict[str, Any]] = None
    # УНИВЕРСАЛЬНОЕ ПРЕДСТАВЛЕНИЕ ДЛЯ КООРДИНАТОРА:
    coordinator_interface: ToolInterface

class ToolResult(BaseModel):
    """Результат выполнения инструмента."""
    status: str  # success | error | stub_not_implemented | validation_error | resource_error | timeout_error
    data: Dict[str, Any] = {}
    files: List[str] = []
    metadata: Dict[str, Any] = {}
    error: Optional[str] = None
    execution_time: Optional[float] = None
    result_type: Optional[str] = None
    result_title: Optional[str] = None
    result_content: Optional[str] = None
    result_table: Optional[List[Dict[str, Any]]] = None
    # 🚀 НОВЫЕ ПОЛЯ ДЛЯ PRODUCTION-READY:
    incident_id: Optional[str] = None  # Уникальный ID инцидента для трассировки
    traceback: Optional[str] = None  # Полный stack trace при ошибках
    stub_info: Optional[Dict[str, Any]] = None  # Информация о заглушках

class ToolRegistry:
    """Реестр инструментов с поддержкой универсального представления."""
    
    def __init__(self):
        self.tools: Dict[str, ToolManifest] = {}
        self.loaded_modules: Dict[str, Any] = {}
        self.tool_methods: Dict[str, Any] = {}  # Store callable functions
        self.load_tools_from_directory("tools")  # Load tools from the 'tools' directory
    
    def load_tools_from_directory(self, directory: str):
        """Load tools from directory structure."""
        import os
        import importlib.util
        
        if not os.path.exists(directory):
            return
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    file_path = os.path.join(root, file)
                    module_name = file[:-3]  # Remove .py
                    
                    try:
                        # Load module
                        spec = importlib.util.spec_from_file_location(module_name, file_path)
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                            
                            # Check if module has manifest and execute function
                            if hasattr(module, 'manifest') and hasattr(module, 'execute'):
                                manifest = module.manifest
                                self.tools[manifest.name] = manifest
                                self.tool_methods[manifest.name] = module.execute
                                self.loaded_modules[manifest.name] = module
                                
                    except Exception as e:
                        print(f"Error loading tool {file_path}: {e}")
    
    def register_tool(self, manifest: ToolManifest) -> None:
        """Регистрация инструмента в реестре."""
        self.tools[manifest.name] = manifest
    
    def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """Execute a tool by name."""
        if tool_name not in self.tool_methods:
            return ToolResult(
                status="error",
                error=f"Tool {tool_name} not found",
                data={}
            )
        
        try:
            result = self.tool_methods[tool_name](**kwargs)
            return result
        except Exception as e:
            return ToolResult(
                status="error",
                error=str(e),
                data={}
            )
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all tools."""
        return [
            {
                "name": manifest.name,
                "version": manifest.version,
                "title": manifest.title,
                "description": manifest.description,
                "category": manifest.category,
                "ui_placement": manifest.ui_placement,
                "enabled": manifest.enabled,
                "system": manifest.system,
                "entrypoint": manifest.entrypoint,
                "params": [param.dict() for param in manifest.params],
                "outputs": manifest.outputs,
                "permissions": manifest.permissions,
                "coordinator_interface": manifest.coordinator_interface.dict()
            }
            for manifest in self.tools.values()
        ]
    
    def get_tool_manifest(self, tool_name: str) -> Optional[ToolManifest]:
        """Получить манифест инструмента."""
        return self.tools.get(tool_name)
    
    def get_tool_interface(self, tool_name: str) -> Optional[ToolInterface]:
        """Получить универсальное представление инструмента для координатора."""
        manifest = self.get_tool_manifest(tool_name)
        return manifest.coordinator_interface if manifest else None
    
    def get_all_interfaces(self) -> Dict[str, ToolInterface]:
        """Получить все интерфейсы инструментов."""
        return {
            name: manifest.coordinator_interface 
            for name, manifest in self.tools.items()
            if manifest.enabled
        }
    
    def find_tools_by_purpose(self, purpose_keywords: List[str]) -> List[str]:
        """Найти инструменты по ключевым словам в назначении."""
        matching_tools = []
        for name, manifest in self.tools.items():
            if not manifest.enabled:
                continue
            purpose_lower = manifest.coordinator_interface.purpose.lower()
            if any(keyword.lower() in purpose_lower for keyword in purpose_keywords):
                matching_tools.append(name)
        return matching_tools
    
    def get_tool_capabilities(self, tool_name: str) -> Dict[str, Any]:
        """Получить возможности инструмента."""
        interface = self.get_tool_interface(tool_name)
        if not interface:
            return {}
        
        return {
            "purpose": interface.purpose,
            "input_params": list(interface.input_requirements.keys()),
            "output_format": interface.output_format,
            "execution_steps": len(interface.execution_flow),
            "guidelines": interface.usage_guidelines
        }
    
    def create_stub_result(self, tool_name: str, message: str = "Инструмент не реализован") -> ToolResult:
        """🚀 СОЗДАНИЕ STUB РЕЗУЛЬТАТА ДЛЯ НЕРЕАЛИЗОВАННОГО ИНСТРУМЕНТА"""
        import uuid
        import traceback
        
        return ToolResult(
            status="stub_not_implemented",
            data={},
            error=message,
            metadata={
                "tool_name": tool_name,
                "stub": True,
                "implementation_required": True
            },
            incident_id=str(uuid.uuid4()),
            stub_info={
                "message": message,
                "tool_name": tool_name,
                "requires_implementation": True,
                "suggested_actions": [
                    "Реализовать основную логику инструмента",
                    "Добавить обработку ошибок",
                    "Протестировать с реальными данными"
                ]
            }
        )
    
    def create_error_result(self, tool_name: str, error: Exception, execution_time: float = None) -> ToolResult:
        """🚀 СОЗДАНИЕ РЕЗУЛЬТАТА ОБ ОШИБКЕ С ТРАССИРОВКОЙ"""
        import uuid
        import traceback
        
        error_type = type(error).__name__
        error_message = str(error)
        full_traceback = traceback.format_exc()
        
        # Определяем тип ошибки
        if "validation" in error_message.lower():
            status = "validation_error"
        elif "resource" in error_message.lower() or "not found" in error_message.lower():
            status = "resource_error"
        elif "timeout" in error_message.lower():
            status = "timeout_error"
        else:
            status = "error"
        
        return ToolResult(
            status=status,
            data={},
            error=f"{error_type}: {error_message}",
            execution_time=execution_time,
            metadata={
                "tool_name": tool_name,
                "error_type": error_type,
                "error_message": error_message
            },
            incident_id=str(uuid.uuid4()),
            traceback=full_traceback
        )

# Глобальный реестр инструментов
tool_registry = ToolRegistry()
