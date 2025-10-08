#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPECIALIZED AGENTS FOR Bldr Empire
==================================

Специализированные агенты с четким разделением ответственности
на основе паттернов из agents-towards-production.
"""

from typing import Dict, Any, List, Optional
from core.agents.base_agent import BaseAgent, Task, TaskResult
from core.exceptions import AgentExecutionError
from core.structured_logging import get_logger

class ChiefEngineerAgent(BaseAgent):
    """
    🏗️ АГЕНТ ГЛАВНОГО ИНЖЕНЕРА
    
    Специализация: Нормативные документы, технические расчеты, проектирование
    """
    
    def __init__(self, tools_system=None):
        super().__init__("chief_engineer", "Нормативные документы и технические расчеты")
        self.tools_system = tools_system
        self.logger = get_logger("chief_engineer")
    
    async def process(self, task: Task) -> TaskResult:
        """Обработка задач главного инженера"""
        try:
            # Определяем тип задачи и выбираем инструмент
            if "норма" in task.description.lower() or "сп" in task.description.lower():
                # Поиск нормативных документов
                result = await self._search_norms(task)
            elif "расчет" in task.description.lower() or "проект" in task.description.lower():
                # Технические расчеты
                result = await self._technical_calculations(task)
            elif "анализ" in task.description.lower():
                # Анализ проектов
                result = await self._project_analysis(task)
            else:
                # Общий поиск в базе знаний
                result = await self._general_search(task)
            
            return TaskResult(
                task_id=task.id,
                success=True,
                result_data=result,
                metadata={"agent": "chief_engineer", "task_type": "technical"}
            )
            
        except Exception as e:
            raise AgentExecutionError(
                self.name,
                task.description,
                f"Ошибка обработки технической задачи: {str(e)}"
            )
    
    async def _search_norms(self, task: Task) -> Dict[str, Any]:
        """Поиск нормативных документов"""
        if not self.tools_system:
            return {"error": "Система инструментов недоступна"}
        
        query = task.input_data.get("query", task.description)
        result = await self.tools_system.execute_tool_async(
            "search_norms",
            query=query,
            timeout_seconds=30
        )
        return result.data if hasattr(result, 'data') else str(result)
    
    async def _technical_calculations(self, task: Task) -> Dict[str, Any]:
        """Технические расчеты"""
        if not self.tools_system:
            return {"error": "Система инструментов недоступна"}
        
        # Здесь можно добавить специфичные расчеты
        result = await self.tools_system.execute_tool_async(
            "search_rag_database",
            query=task.description,
            timeout_seconds=30
        )
        return result.data if hasattr(result, 'data') else str(result)
    
    async def _project_analysis(self, task: Task) -> Dict[str, Any]:
        """Анализ проектов"""
        if not self.tools_system:
            return {"error": "Система инструментов недоступна"}
        
        result = await self.tools_system.execute_tool_async(
            "search_rag_database",
            query=task.description,
            timeout_seconds=30
        )
        return result.data if hasattr(result, 'data') else str(result)
    
    async def _general_search(self, task: Task) -> Dict[str, Any]:
        """Общий поиск"""
        if not self.tools_system:
            return {"error": "Система инструментов недоступна"}
        
        result = await self.tools_system.execute_tool_async(
            "search_rag_database",
            query=task.description,
            timeout_seconds=30
        )
        return result.data if hasattr(result, 'data') else str(result)
    
    def can_handle(self, task: Task) -> bool:
        """Проверка способности обработки"""
        description_lower = task.description.lower()
        return any(keyword in description_lower for keyword in [
            "норма", "сп", "снип", "гост", "расчет", "проект", "анализ",
            "технический", "строительный", "инженерный"
        ])
    
    def get_capabilities(self) -> List[str]:
        """Способности агента"""
        return [
            "Поиск нормативных документов",
            "Технические расчеты",
            "Анализ проектов",
            "Работа с СП, СНиП, ГОСТ",
            "Строительные расчеты"
        ]


class AnalystAgent(BaseAgent):
    """
    📊 АГЕНТ АНАЛИТИКА
    
    Специализация: Сметные расчеты, финансовый анализ, стоимость
    """
    
    def __init__(self, tools_system=None):
        super().__init__("analyst", "Сметные расчеты и финансовый анализ")
        self.tools_system = tools_system
        self.logger = get_logger("analyst")
    
    async def process(self, task: Task) -> TaskResult:
        """Обработка задач аналитика"""
        try:
            # Определяем тип задачи
            if "смета" in task.description.lower() or "стоимость" in task.description.lower():
                result = await self._cost_estimation(task)
            elif "бюджет" in task.description.lower():
                result = await self._budget_analysis(task)
            elif "финанс" in task.description.lower():
                result = await self._financial_analysis(task)
            else:
                result = await self._general_analysis(task)
            
            return TaskResult(
                task_id=task.id,
                success=True,
                result_data=result,
                metadata={"agent": "analyst", "task_type": "financial"}
            )
            
        except Exception as e:
            raise AgentExecutionError(
                self.name,
                task.description,
                f"Ошибка обработки финансовой задачи: {str(e)}"
            )
    
    async def _cost_estimation(self, task: Task) -> Dict[str, Any]:
        """Сметные расчеты"""
        if not self.tools_system:
            return {"error": "Система инструментов недоступна"}
        
        result = await self.tools_system.execute_tool_async(
            "estimate_cost",
            query=task.description,
            timeout_seconds=45
        )
        return result.data if hasattr(result, 'data') else str(result)
    
    async def _budget_analysis(self, task: Task) -> Dict[str, Any]:
        """Анализ бюджета"""
        if not self.tools_system:
            return {"error": "Система инструментов недоступна"}
        
        result = await self.tools_system.execute_tool_async(
            "search_rag_database",
            query=task.description,
            timeout_seconds=30
        )
        return result.data if hasattr(result, 'data') else str(result)
    
    async def _financial_analysis(self, task: Task) -> Dict[str, Any]:
        """Финансовый анализ"""
        if not self.tools_system:
            return {"error": "Система инструментов недоступна"}
        
        result = await self.tools_system.execute_tool_async(
            "search_rag_database",
            query=task.description,
            timeout_seconds=30
        )
        return result.data if hasattr(result, 'data') else str(result)
    
    async def _general_analysis(self, task: Task) -> Dict[str, Any]:
        """Общий анализ"""
        if not self.tools_system:
            return {"error": "Система инструментов недоступна"}
        
        result = await self.tools_system.execute_tool_async(
            "search_rag_database",
            query=task.description,
            timeout_seconds=30
        )
        return result.data if hasattr(result, 'data') else str(result)
    
    def can_handle(self, task: Task) -> bool:
        """Проверка способности обработки"""
        description_lower = task.description.lower()
        return any(keyword in description_lower for keyword in [
            "смета", "стоимость", "цена", "бюджет", "финанс", "расчет",
            "экономический", "финансовый", "стоимостной"
        ])
    
    def get_capabilities(self) -> List[str]:
        """Способности агента"""
        return [
            "Сметные расчеты",
            "Финансовый анализ",
            "Расчет стоимости",
            "Бюджетное планирование",
            "Экономические расчеты"
        ]


class CoordinatorAgent(BaseAgent):
    """
    🎯 АГЕНТ КООРДИНАТОРА
    
    Специализация: Планирование, координация, общие запросы
    """
    
    def __init__(self, tools_system=None):
        super().__init__("coordinator", "Планирование и координация")
        self.tools_system = tools_system
        self.logger = get_logger("coordinator")
    
    async def process(self, task: Task) -> TaskResult:
        """Обработка задач координатора"""
        try:
            # Определяем тип задачи
            if "привет" in task.description.lower() or "здравствуй" in task.description.lower():
                result = await self._greeting_response(task)
            elif "расскажи" in task.description.lower() and "себе" in task.description.lower():
                result = await self._self_introduction(task)
            elif "помощь" in task.description.lower() or "помоги" in task.description.lower():
                result = await self._help_response(task)
            else:
                result = await self._general_response(task)
            
            return TaskResult(
                task_id=task.id,
                success=True,
                result_data=result,
                metadata={"agent": "coordinator", "task_type": "coordination"}
            )
            
        except Exception as e:
            raise AgentExecutionError(
                self.name,
                task.description,
                f"Ошибка координации: {str(e)}"
            )
    
    async def _greeting_response(self, task: Task) -> str:
        """Ответ на приветствие"""
        return "Привет! Я координатор системы Bldr Empire. Чем могу помочь?"
    
    async def _self_introduction(self, task: Task) -> str:
        """Самопрезентация"""
        return """Я - координатор системы Bldr Empire, многоагентной системы для строительной отрасли. 
        Моя задача - планировать и координировать работу специализированных агентов:
        - Главный инженер (нормативные документы, технические расчеты)
        - Аналитик (сметные расчеты, финансовый анализ)
        
        Я помогаю определить, какой специалист лучше всего подходит для вашего запроса."""
    
    async def _help_response(self, task: Task) -> str:
        """Ответ на запрос помощи"""
        return """Я могу помочь с:
        - Поиском нормативных документов (СП, СНиП, ГОСТ)
        - Техническими расчетами и проектированием
        - Сметными расчетами и финансовым анализом
        - Анализом строительных проектов
        
        Просто опишите, что вам нужно, и я направлю запрос нужному специалисту."""
    
    async def _general_response(self, task: Task) -> str:
        """Общий ответ"""
        return "Я получил ваш запрос и проанализирую его для определения подходящего специалиста."
    
    def can_handle(self, task: Task) -> bool:
        """Проверка способности обработки"""
        description_lower = task.description.lower()
        return any(keyword in description_lower for keyword in [
            "привет", "здравствуй", "расскажи", "помощь", "помоги",
            "координация", "планирование", "общий"
        ])
    
    def get_capabilities(self) -> List[str]:
        """Способности агента"""
        return [
            "Планирование задач",
            "Координация агентов",
            "Обработка общих запросов",
            "Маршрутизация задач",
            "Управление рабочим процессом"
        ]
