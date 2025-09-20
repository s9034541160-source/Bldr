#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
УНИФИЦИРОВАННАЯ СИСТЕМА ИНСТРУМЕНТОВ С KWARGS
=============================================

Единая система для всех 47+ инструментов с унифицированными:
- Форматами входных/выходных данных  
- Обработкой ошибок
- Валидацией параметров через **kwargs
- Стандартизированными ответами

"""

import json
import traceback
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import logging

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class ToolResult:
    """Стандартизированный результат выполнения инструмента"""
    status: str  # 'success' | 'error' | 'partial'
    data: Any = None
    error: Optional[str] = None
    warnings: List[str] = None
    metadata: Dict[str, Any] = None
    execution_time: Optional[float] = None
    tool_name: Optional[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для JSON serialization"""
        return asdict(self)
    
    def is_success(self) -> bool:
        return self.status == 'success'
    
    def add_warning(self, warning: str):
        self.warnings.append(warning)
    
    def set_metadata(self, key: str, value: Any):
        self.metadata[key] = value

@dataclass 
class ToolSignature:
    """Сигнатура инструмента с описанием параметров"""
    name: str
    description: str
    required_params: List[str] = None
    optional_params: Dict[str, Any] = None
    return_type: str = "ToolResult"
    category: str = "general"
    
    def __post_init__(self):
        if self.required_params is None:
            self.required_params = []
        if self.optional_params is None:
            self.optional_params = {}

class ToolValidationError(Exception):
    """Ошибка валидации параметров инструмента"""
    pass

class ToolExecutionError(Exception):
    """Ошибка выполнения инструмента"""
    pass

class UnifiedToolsSystem:
    """Унифицированная система инструментов с kwargs поддержкой"""
    
    def __init__(self):
        self.tools_registry: Dict[str, ToolSignature] = {}
        self.tools_methods: Dict[str, Callable] = {}
        self.execution_stats: Dict[str, Dict[str, Any]] = {}
        
        # Register all tools
        self._register_all_tools()
    
    def _register_all_tools(self):
        """Регистрация всех 47+ инструментов"""
        
        # PRO FEATURE TOOLS (9)
        self.register_tool(
            "generate_letter",
            description="AI-генерация официальных писем",
            required_params=["description"],
            optional_params={
                "template_id": "compliance_sp31",
                "project_id": None,
                "tone": 0.0,
                "dryness": 0.5,
                "humanity": 0.7,
                "length": "medium",
                "formality": "formal"
            },
            category="pro_features"
        )
        
        self.register_tool(
            "improve_letter",
            description="Улучшение черновиков писем",
            required_params=["draft"],
            optional_params={
                "description": "",
                "template_id": "",
                "project_id": None,
                "tone": 0.0,
                "dryness": 0.5,
                "humanity": 0.7,
                "length": "medium",
                "formality": "formal"
            },
            category="pro_features"
        )
        
        self.register_tool(
            "auto_budget",
            description="Автоматическое составление смет",
            required_params=["estimate_data"],
            optional_params={
                "gesn_rates": {},
                "regional_coefficients": {},
                "overheads_percentage": 15,
                "profit_percentage": 10
            },
            category="pro_features"
        )
        
        self.register_tool(
            "generate_ppr",
            description="Генерация проекта производства работ",
            required_params=["project_data"],
            optional_params={
                "works_seq": [],
                "timeline": None,
                "resources": {},
                "safety_requirements": []
            },
            category="pro_features"
        )
        
        self.register_tool(
            "create_gpp",
            description="Создание календарного плана",
            required_params=["works_seq"],
            optional_params={
                "timeline": None,
                "constraints": {},
                "resources": {},
                "dependencies": []
            },
            category="pro_features"
        )
        
        # SUPER FEATURE TOOLS (3)
        self.register_tool(
            "analyze_bentley_model",
            description="Анализ IFC/BIM моделей",
            required_params=["ifc_path"],
            optional_params={
                "analysis_type": "clash",
                "output_format": "json",
                "detailed": False
            },
            category="super_features"
        )
        
        self.register_tool(
            "monte_carlo_sim",
            description="Monte Carlo анализ рисков",
            required_params=["project_data"],
            optional_params={
                "iterations": 10000,
                "confidence_level": 0.95,
                "variables": {},
                "seed": None
            },
            category="super_features"
        )
        
        # ENHANCED TOOLS (8)
        self.register_tool(
            "search_rag_database",
            description="Поиск в БЗ с SBERT",
            required_params=["query"],
            optional_params={
                "doc_types": ["norms"],
                "k": 5,
                "use_sbert": False,
                "embed_model": "nomic",
                "min_relevance": 0.0,
                "security_level": 1,
                "date_range": None,
                "summarize": False
            },
            category="enhanced"
        )
        
        self.register_tool(
            "analyze_image",
            description="OCR + анализ изображений",
            required_params=["image_path"],
            optional_params={
                "analysis_type": "basic",
                "ocr_lang": "rus",
                "detect_objects": True,
                "extract_dimensions": False
            },
            category="enhanced"
        )
        
        self.register_tool(
            "calculate_financial_metrics",
            description="Финансовые расчёты (ROI/NPV/IRR)",
            required_params=["type"],
            optional_params={
                "profit": 0.0,
                "cost": 0.0,
                "investment": 0.0,
                "revenue": 0.0,
                "cash_flows": [],
                "discount_rate": 0.1
            },
            category="enhanced"
        )
        
        # DATA VISUALIZATION TOOLS (5)
        self.register_tool(
            "create_gantt_chart",
            description="Диаграммы Ганта",
            required_params=["tasks"],
            optional_params={
                "title": "Gantt Chart",
                "start_date": None,
                "timeline": "auto",
                "dependencies": True,
                "resources": False
            },
            category="visualization"
        )
        
        self.register_tool(
            "create_pie_chart",
            description="Круговые диаграммы",
            required_params=["data"],
            optional_params={
                "title": "Pie Chart",
                "colors": None,
                "show_percentages": True,
                "explode": None
            },
            category="visualization"
        )
        
        # Add more tools...
        logger.info(f"Registered {len(self.tools_registry)} tools in unified system")
    
    def register_tool(self, name: str, description: str, 
                     required_params: List[str] = None,
                     optional_params: Dict[str, Any] = None,
                     category: str = "general"):
        """Регистрация нового инструмента"""
        
        signature = ToolSignature(
            name=name,
            description=description,
            required_params=required_params or [],
            optional_params=optional_params or {},
            category=category
        )
        
        self.tools_registry[name] = signature
        logger.debug(f"Registered tool: {name}")
    
    def validate_tool_call(self, tool_name: str, **kwargs) -> None:
        """Валидация вызова инструмента с kwargs"""
        
        if tool_name not in self.tools_registry:
            raise ToolValidationError(f"Unknown tool: {tool_name}")
        
        signature = self.tools_registry[tool_name]
        
        # Проверяем обязательные параметры
        missing_params = []
        for param in signature.required_params:
            if param not in kwargs:
                missing_params.append(param)
        
        if missing_params:
            raise ToolValidationError(
                f"Tool '{tool_name}' missing required parameters: {missing_params}"
            )
        
        # Добавляем дефолтные значения для опциональных параметров
        for param, default_value in signature.optional_params.items():
            if param not in kwargs:
                kwargs[param] = default_value
    
    def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """Выполнение инструмента с унифицированным результатом"""
        
        start_time = datetime.now()
        
        try:
            # Валидация
            self.validate_tool_call(tool_name, **kwargs)
            
            # Выполнение
            if tool_name in self.tools_methods:
                # Если инструмент уже зарегистрирован в новой системе
                result_data = self.tools_methods[tool_name](**kwargs)
            else:
                # Временно используем старую систему для обратной совместимости
                result_data = self._execute_legacy_tool(tool_name, **kwargs)
            
            # Создание унифицированного результата
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = ToolResult(
                status="success",
                data=result_data,
                tool_name=tool_name,
                execution_time=execution_time
            )
            
            # Статистика
            self._update_execution_stats(tool_name, True, execution_time)
            
            return result
            
        except ToolValidationError as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            result = ToolResult(
                status="error",
                error=f"Validation error: {str(e)}",
                tool_name=tool_name,
                execution_time=execution_time
            )
            self._update_execution_stats(tool_name, False, execution_time)
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            result = ToolResult(
                status="error", 
                error=f"Execution error: {str(e)}",
                tool_name=tool_name,
                execution_time=execution_time
            )
            result.set_metadata("traceback", traceback.format_exc())
            self._update_execution_stats(tool_name, False, execution_time)
            return result
    
    def _execute_legacy_tool(self, tool_name: str, **kwargs) -> Any:
        """Временная обратная совместимость со старой системой"""
        
        # Импортируем старую систему
        from core.tools_system import ToolsSystem
        
        # Создаём аргументы в старом формате
        arguments = dict(kwargs)
        
        # Выполняем через старую систему (пока не перенесём все инструменты)
        legacy_system = ToolsSystem(None, None)  # Mock dependencies пока что
        legacy_result = legacy_system.execute_tool(tool_name, arguments)
        
        return legacy_result
    
    def _update_execution_stats(self, tool_name: str, success: bool, execution_time: float):
        """Обновление статистики выполнения"""
        if tool_name not in self.execution_stats:
            self.execution_stats[tool_name] = {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "avg_execution_time": 0.0,
                "total_execution_time": 0.0
            }
        
        stats = self.execution_stats[tool_name]
        stats["total_calls"] += 1
        stats["total_execution_time"] += execution_time
        stats["avg_execution_time"] = stats["total_execution_time"] / stats["total_calls"]
        
        if success:
            stats["successful_calls"] += 1
        else:
            stats["failed_calls"] += 1
    
    def get_tool_info(self, tool_name: str) -> Optional[ToolSignature]:
        """Получение информации об инструменте"""
        return self.tools_registry.get(tool_name)
    
    def list_tools(self, category: Optional[str] = None) -> List[ToolSignature]:
        """Список всех инструментов"""
        if category:
            return [sig for sig in self.tools_registry.values() if sig.category == category]
        return list(self.tools_registry.values())
    
    def get_categories(self) -> List[str]:
        """Список всех категорий инструментов"""
        return list(set(sig.category for sig in self.tools_registry.values()))
    
    def get_execution_stats(self, tool_name: Optional[str] = None) -> Dict[str, Any]:
        """Статистика выполнения инструментов"""
        if tool_name:
            return self.execution_stats.get(tool_name, {})
        return self.execution_stats
    
    def execute_tool_chain(self, chain: List[Dict[str, Any]]) -> List[ToolResult]:
        """Выполнение цепочки инструментов"""
        results = []
        
        for step in chain:
            tool_name = step.get("tool")
            kwargs = step.get("params", {})
            
            if not tool_name:
                result = ToolResult(
                    status="error",
                    error="Missing tool name in chain step",
                    metadata={"step": step}
                )
                results.append(result)
                continue
            
            # Можем использовать результаты предыдущих шагов
            if step.get("use_previous_result") and results:
                previous_result = results[-1]
                if previous_result.is_success():
                    kwargs.update(previous_result.data or {})
            
            result = self.execute_tool(tool_name, **kwargs)
            results.append(result)
            
            # Прерываем цепочку при ошибке, если не указано иное
            if not result.is_success() and not step.get("continue_on_error", False):
                break
        
        return results

# Создание глобального экземпляра
unified_tools = UnifiedToolsSystem()

# Convenience functions для обратной совместимости
def execute_tool(tool_name: str, **kwargs) -> ToolResult:
    """Удобная функция для выполнения инструментов"""
    return unified_tools.execute_tool(tool_name, **kwargs)

def list_available_tools(category: str = None) -> List[str]:
    """Список доступных инструментов"""
    tools = unified_tools.list_tools(category)
    return [tool.name for tool in tools]

def get_tool_signature(tool_name: str) -> Optional[ToolSignature]:
    """Получение сигнатуры инструмента"""
    return unified_tools.get_tool_info(tool_name)