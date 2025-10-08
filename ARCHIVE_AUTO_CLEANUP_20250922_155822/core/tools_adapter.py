#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TOOLS ADAPTER - Адаптер для интеграции Master Tools System с существующим app.py
================================================================================

Этот файл обеспечивает плавную интеграцию новой Master Tools System 
с существующим кодом приложения, сохраняя обратную совместимость.

ФУНКЦИИ:
- Адаптация API calls из app.py для Master Tools System
- Конвертация результатов в ожидаемые форматы
- Совместимость с UI компонентами  
- Постепенная миграция инструментов
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Optional, Union, List
from dataclasses import asdict

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from master_tools_system import (
        MasterToolsSystem, 
        ToolResult, 
        get_master_tools_system,
        execute_tool as master_execute_tool,
        list_available_tools as master_list_tools
    )
    HAS_MASTER_TOOLS = True
except ImportError as e:
    logging.warning(f"Could not import Master Tools System: {e}")
    HAS_MASTER_TOOLS = False
    
    # Create fallback ToolResult class when master_tools_system is not available
    class ToolResult:
        def __init__(self, status='success', data=None, error=None, execution_time=0.0, metadata=None):
            self.status = status
            self.data = data or {}
            self.error = error
            self.execution_time = execution_time
            self.metadata = metadata or {}
        
        def is_success(self):
            return self.status == 'success'
    
    # Create fallback classes
    class MasterToolsSystem:
        pass
    
    def get_master_tools_system(rag_system, model_manager):
        return None
    
    def master_execute_tool(tool_name, **kwargs):
        return ToolResult(status='error', error='Master Tools System not available')
    
    def master_list_tools():
        return []

logger = logging.getLogger(__name__)

# ============================
# ADAPTER CLASS
# ============================

class ToolsAdapter:
    """
    Адаптер для интеграции Master Tools System с существующим кодом
    """
    
    def __init__(self, rag_system=None, model_manager=None):
        self.rag_system = rag_system
        self.model_manager = model_manager
        self.master_tools = None
        
        # Пытаемся инициализировать Master Tools System
        if HAS_MASTER_TOOLS:
            try:
                self.master_tools = get_master_tools_system(rag_system, model_manager)
                logger.info("Master Tools System initialized successfully")
                self.use_master_tools = True
            except Exception as e:
                logger.error(f"Failed to initialize Master Tools System: {e}")
                self.use_master_tools = False
        else:
            self.use_master_tools = False
            logger.warning("Using legacy tools system (Master Tools System not available)")
    
    def is_master_tools_available(self) -> bool:
        """Проверяем доступность Master Tools System"""
        return self.use_master_tools and self.master_tools is not None
    
    # ============================
    # LEGACY COMPATIBILITY METHODS
    # ============================
    
    def generate_letter(self, description: str, **kwargs) -> Dict[str, Any]:
        """Генерация письма (адаптер для Master Tools)"""
        if self.is_master_tools_available():
            try:
                result = self.master_tools.execute_tool("generate_letter", 
                                                      description=description, **kwargs)
                if result.is_success():
                    return {
                        "status": "success",
                        "letter_text": result.data.get("letter_text", ""),
                        "template_id": result.data.get("template_id", ""),
                        "generated_at": result.data.get("generated_at", ""),
                        "execution_time": result.execution_time
                    }
                else:
                    return {
                        "status": "error", 
                        "error": result.error,
                        "details": result.metadata
                    }
            except Exception as e:
                logger.error(f"Error in generate_letter: {e}")
                return {"status": "error", "error": str(e)}
        else:
            # Fallback к legacy системе
            return self._legacy_generate_letter(description, **kwargs)
    
    def improve_letter(self, draft: str, description: str = "", **kwargs) -> Dict[str, Any]:
        """Улучшение письма (адаптер)"""
        if self.is_master_tools_available():
            try:
                result = self.master_tools.execute_tool("improve_letter",
                                                      draft=draft,
                                                      description=description, **kwargs)
                if result.is_success():
                    return {
                        "status": "success",
                        "improved_text": result.data.get("improved_text", ""),
                        "original_draft": result.data.get("original_draft", ""),
                        "improved_at": result.data.get("improved_at", ""),
                        "execution_time": result.execution_time
                    }
                else:
                    return {"status": "error", "error": result.error}
            except Exception as e:
                return {"status": "error", "error": str(e)}
        else:
            return self._legacy_improve_letter(draft, description, **kwargs)
    
    def auto_budget(self, estimate_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Автоматическое составление смет (адаптер)"""
        if self.is_master_tools_available():
            try:
                result = self.master_tools.execute_tool("auto_budget",
                                                      estimate_data=estimate_data, **kwargs)
                if result.is_success():
                    return {
                        "status": "success",
                        "budget_data": result.data,
                        "execution_time": result.execution_time,
                        "metadata": result.metadata
                    }
                else:
                    return {"status": "error", "error": result.error}
            except Exception as e:
                return {"status": "error", "error": str(e)}
        else:
            return self._legacy_auto_budget(estimate_data, **kwargs)
    
    def generate_ppr(self, project_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Генерация ППР (адаптер)"""
        if self.is_master_tools_available():
            try:
                result = self.master_tools.execute_tool("generate_ppr",
                                                      project_data=project_data, **kwargs)
                if result.is_success():
                    return {
                        "status": "success",
                        "ppr_data": result.data,
                        "execution_time": result.execution_time
                    }
                else:
                    return {"status": "error", "error": result.error}
            except Exception as e:
                return {"status": "error", "error": str(e)}
        else:
            return self._legacy_generate_ppr(project_data, **kwargs)
    
    def search_rag_database(self, query: str, **kwargs) -> Dict[str, Any]:
        """Поиск в RAG базе (адаптер)"""
        if self.is_master_tools_available():
            try:
                result = self.master_tools.execute_tool("search_rag_database",
                                                      query=query, **kwargs)
                if result.is_success():
                    return {
                        "status": "success",
                        "query": result.data.get("query", query),
                        "results": result.data.get("results", []),
                        "total_found": result.data.get("total_found", 0),
                        "execution_time": result.execution_time
                    }
                else:
                    return {"status": "error", "error": result.error}
            except Exception as e:
                return {"status": "error", "error": str(e)}
        else:
            return self._legacy_search_rag(query, **kwargs)
    
    def analyze_image(self, image_path: str, **kwargs) -> Dict[str, Any]:
        """Анализ изображения (адаптер)"""
        if self.is_master_tools_available():
            try:
                result = self.master_tools.execute_tool("analyze_image",
                                                      image_path=image_path, **kwargs)
                if result.is_success():
                    return {
                        "status": "success",
                        "extracted_text": result.data.get("extracted_text", ""),
                        "image_path": result.data.get("image_path", image_path),
                        "text_length": result.data.get("text_length", 0),
                        "execution_time": result.execution_time
                    }
                else:
                    return {"status": "error", "error": result.error}
            except Exception as e:
                return {"status": "error", "error": str(e)}
        else:
            return self._legacy_analyze_image(image_path, **kwargs)
    
    def calculate_financial_metrics(self, metric_type: str, **kwargs) -> Dict[str, Any]:
        """Расчёт финансовых метрик (адаптер)"""
        if self.is_master_tools_available():
            try:
                result = self.master_tools.execute_tool("calculate_financial_metrics",
                                                      metric_type=metric_type, **kwargs)
                if result.is_success():
                    return {
                        "status": "success",
                        "metric_result": result.data,
                        "execution_time": result.execution_time
                    }
                else:
                    return {"status": "error", "error": result.error}
            except Exception as e:
                return {"status": "error", "error": str(e)}
        else:
            return self._legacy_financial_metrics(metric_type, **kwargs)
    
    def create_visualization(self, viz_type: str, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Создание визуализации (адаптер)"""
        if self.is_master_tools_available():
            try:
                tool_name = f"create_{viz_type}_chart"  # pie, bar, gantt
                result = self.master_tools.execute_tool(tool_name, data=data, **kwargs)
                
                if result.is_success():
                    return {
                        "status": "success",
                        "chart_data": result.data,
                        "chart_type": viz_type,
                        "execution_time": result.execution_time
                    }
                else:
                    return {"status": "error", "error": result.error}
            except Exception as e:
                return {"status": "error", "error": str(e)}
        else:
            return self._legacy_create_visualization(viz_type, data, **kwargs)
    
    # ============================
    # GENERIC TOOL EXECUTION
    # ============================
    
    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Универсальное выполнение инструмента"""
        if self.is_master_tools_available():
            try:
                result = self.master_tools.execute_tool(tool_name, **kwargs)
                return self._convert_tool_result(result)
            except Exception as e:
                return {"status": "error", "error": str(e)}
        else:
            return self._legacy_execute_tool(tool_name, **kwargs)
    
    def list_available_tools(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Список доступных инструментов"""
        if self.is_master_tools_available():
            try:
                return self.master_tools.list_all_tools(category)
            except Exception as e:
                return {"status": "error", "error": str(e)}
        else:
            return self._legacy_list_tools(category)
    
    def get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """Информация об инструменте"""
        if self.is_master_tools_available():
            try:
                return self.master_tools.get_tool_info(tool_name)
            except Exception as e:
                return {"status": "error", "error": str(e)}
        else:
            return self._legacy_tool_info(tool_name)
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Статистика выполнения"""
        if self.is_master_tools_available():
            try:
                return self.master_tools.get_execution_stats()
            except Exception as e:
                return {"status": "error", "error": str(e)}
        else:
            return {"status": "legacy", "message": "Statistics not available in legacy mode"}
    
    # ============================
    # UTILITY METHODS
    # ============================
    
    def _convert_tool_result(self, result: ToolResult) -> Dict[str, Any]:
        """Конвертация ToolResult в стандартный словарь"""
        return {
            "status": result.status,
            "data": result.data,
            "error": result.error,
            "warnings": result.warnings,
            "metadata": result.metadata,
            "execution_time": result.execution_time,
            "tool_name": result.tool_name
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Проверка состояния системы инструментов"""
        return {
            "master_tools_available": self.is_master_tools_available(),
            "rag_system_connected": self.rag_system is not None,
            "model_manager_connected": self.model_manager is not None,
            "total_tools": len(self.master_tools.registry.tools) if self.is_master_tools_available() else 0,
            "system_status": "ready" if self.is_master_tools_available() else "legacy_mode"
        }
    
    # ============================
    # LEGACY FALLBACK METHODS
    # ============================
    
    def _legacy_generate_letter(self, description: str, **kwargs) -> Dict[str, Any]:
        """Legacy fallback для генерации письма"""
        try:
            # Попытка импорта legacy модуля
            from letter_generator import LetterGenerator
            gen = LetterGenerator()
            
            template_text = kwargs.get("template_text", 
                                     "Уважаемый [Получатель]!\\n\\n{description}\\n\\nС уважением,")
            
            result = gen.generate_letter_with_lm(
                description=description,
                template_text=template_text,
                **kwargs
            )
            
            return {
                "status": "success",
                "letter_text": result,
                "source": "legacy_system"
            }
        except ImportError:
            return {
                "status": "error", 
                "error": "Legacy letter generator not available"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _legacy_improve_letter(self, draft: str, description: str, **kwargs) -> Dict[str, Any]:
        """Legacy fallback для улучшения письма"""
        return {
            "status": "error",
            "error": "Legacy improve letter not implemented"
        }
    
    def _legacy_auto_budget(self, estimate_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Legacy fallback для составления сметы"""
        try:
            from budget_auto import auto_budget
            result = auto_budget(estimate_data, **kwargs)
            return {
                "status": "success", 
                "budget_data": result,
                "source": "legacy_system"
            }
        except ImportError:
            return {"status": "error", "error": "Legacy budget auto not available"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _legacy_generate_ppr(self, project_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Legacy fallback для генерации ППР"""
        try:
            from ppr_generator import generate_ppr
            result = generate_ppr(project_data, **kwargs)
            return {
                "status": "success",
                "ppr_data": result,
                "source": "legacy_system"  
            }
        except ImportError:
            return {"status": "error", "error": "Legacy PPR generator not available"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _legacy_search_rag(self, query: str, **kwargs) -> Dict[str, Any]:
        """Legacy fallback для RAG поиска"""
        if self.rag_system and hasattr(self.rag_system, 'query'):
            try:
                results = self.rag_system.query(query, k=kwargs.get("k", 5))
                return {
                    "status": "success",
                    "query": query,
                    "results": results.get("results", []),
                    "total_found": len(results.get("results", [])),
                    "source": "legacy_rag"
                }
            except Exception as e:
                return {"status": "error", "error": str(e)}
        else:
            return {
                "status": "error",
                "error": "RAG system not available"
            }
    
    def _legacy_analyze_image(self, image_path: str, **kwargs) -> Dict[str, Any]:
        """Legacy fallback для анализа изображений"""
        return {
            "status": "error",
            "error": "Legacy image analysis not implemented"
        }
    
    def _legacy_financial_metrics(self, metric_type: str, **kwargs) -> Dict[str, Any]:
        """Legacy fallback для финансовых метрик"""
        return {
            "status": "error", 
            "error": "Legacy financial metrics not implemented"
        }
    
    def _legacy_create_visualization(self, viz_type: str, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Legacy fallback для создания визуализации"""
        return {
            "status": "error",
            "error": "Legacy visualization not implemented"
        }
    
    def _legacy_execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Legacy fallback для выполнения инструментов"""
        return {
            "status": "error", 
            "error": f"Legacy execution for tool '{tool_name}' not available"
        }
    
    def _legacy_list_tools(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Legacy fallback для списка инструментов"""
        return {
            "tools": [],
            "total_count": 0,
            "categories": [],
            "message": "Using legacy tools system"
        }
    
    def _legacy_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """Legacy fallback для информации об инструменте"""
        return {
            "error": f"Tool '{tool_name}' not available in legacy mode"
        }

# ============================
# GLOBAL ADAPTER INSTANCE
# ============================

# Глобальный экземпляр адаптера
_global_adapter: Optional[ToolsAdapter] = None

def get_tools_adapter(rag_system=None, model_manager=None) -> ToolsAdapter:
    """Получение глобального экземпляра адаптера"""
    global _global_adapter
    if _global_adapter is None:
        _global_adapter = ToolsAdapter(rag_system, model_manager)
    return _global_adapter

# ============================
# CONVENIENCE FUNCTIONS
# ============================

def execute_tool_safe(tool_name: str, **kwargs) -> Dict[str, Any]:
    """Безопасное выполнение инструмента через адаптер"""
    adapter = get_tools_adapter()
    return adapter.execute_tool(tool_name, **kwargs)

def list_tools_safe(category: Optional[str] = None) -> Dict[str, Any]:
    """Безопасное получение списка инструментов"""
    adapter = get_tools_adapter()
    return adapter.list_available_tools(category)

def is_tool_available(tool_name: str) -> bool:
    """Проверка доступности инструмента"""
    adapter = get_tools_adapter()
    tool_info = adapter.get_tool_info(tool_name)
    return "error" not in tool_info

# ============================
# TESTING
# ============================

if __name__ == "__main__":
    print("🔧 TOOLS ADAPTER - TEST")
    print("=" * 40)
    
    # Создаём адаптер
    adapter = ToolsAdapter()
    
    # Проверяем health check
    health = adapter.health_check()
    print(f"Health Check: {health}")
    
    # Тестируем несколько инструментов
    if health["master_tools_available"]:
        print("\\n✅ Master Tools System доступна - тестируем...")
        
        # Тест поиска в RAG
        result = adapter.search_rag_database("строительные нормы")
        print(f"RAG Search: {result.get('status', 'unknown')}")
        
        # Тест визуализации
        result = adapter.create_visualization("pie", {"A": 30, "B": 70})
        print(f"Visualization: {result.get('status', 'unknown')}")
        
        # Список инструментов
        tools = adapter.list_available_tools()
        print(f"Available tools: {tools.get('total_count', 0)}")
        
    else:
        print("⚠️  Используется legacy режим")
    
    print("\\n🎉 Tools Adapter готов к использованию!")