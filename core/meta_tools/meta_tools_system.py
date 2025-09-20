"""
Meta-Tools System для SuperBuilder - высокоуровневые инструменты,
которые оркеструют выполнение множества базовых инструментов для решения сложных задач.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from .dag_orchestrator import DAGOrchestrator, Priority, TaskStatus

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetaToolCategory(Enum):
    """Категории мета-инструментов"""
    ANALYSIS = "analysis"
    PLANNING = "planning" 
    REPORTING = "reporting"
    AUTOMATION = "automation"
    OPTIMIZATION = "optimization"


@dataclass
class MetaTool:
    """Описание мета-инструмента"""
    name: str
    description: str
    category: MetaToolCategory
    required_params: List[str]
    optional_params: List[str] = field(default_factory=list)
    estimated_time: int = 0  # в минутах
    complexity: str = "medium"  # low, medium, high
    tags: List[str] = field(default_factory=list)


class MetaToolsSystem:
    """
    Система мета-инструментов для управления сложными многошаговыми процессами
    """
    
    def __init__(self, tools_system, dag_orchestrator: Optional[DAGOrchestrator] = None):
        """
        Инициализация системы мета-инструментов
        
        Args:
            tools_system: Базовая система инструментов
            dag_orchestrator: Оркестратор DAG (создается автоматически если не передан)
        """
        self.tools_system = tools_system
        self.orchestrator = dag_orchestrator or DAGOrchestrator(tools_system)
        
        # Реестр мета-инструментов
        self.meta_tools: Dict[str, MetaTool] = {}
        self.meta_tool_handlers: Dict[str, Callable] = {}
        
        # Регистрируем встроенные мета-инструменты
        self._register_builtin_meta_tools()
        
        logger.info("Meta-Tools System инициализирована")
    
    def register_meta_tool(self, 
                          name: str,
                          handler: Callable,
                          description: str,
                          category: MetaToolCategory,
                          required_params: List[str],
                          optional_params: List[str] = None,
                          estimated_time: int = 0,
                          complexity: str = "medium",
                          tags: List[str] = None) -> None:
        """
        Регистрация нового мета-инструмента
        
        Args:
            name: Имя мета-инструмента
            handler: Функция-обработчик
            description: Описание
            category: Категория
            required_params: Обязательные параметры
            optional_params: Опциональные параметры
            estimated_time: Оценочное время выполнения в минутах
            complexity: Сложность (low/medium/high)
            tags: Теги для поиска
        """
        meta_tool = MetaTool(
            name=name,
            description=description,
            category=category,
            required_params=required_params,
            optional_params=optional_params or [],
            estimated_time=estimated_time,
            complexity=complexity,
            tags=tags or []
        )
        
        self.meta_tools[name] = meta_tool
        self.meta_tool_handlers[name] = handler
        
        logger.info(f"Зарегистрирован мета-инструмент: {name}")
    
    def _register_builtin_meta_tools(self) -> None:
        """Регистрация встроенных мета-инструментов"""
        
        # Комплексный анализ проекта
        self.register_meta_tool(
            name="comprehensive_analysis_project",
            handler=self._comprehensive_analysis_project,
            description="Комплексный анализ строительного проекта: поиск норм, анализ документации, расчет сметы, генерация отчета",
            category=MetaToolCategory.ANALYSIS,
            required_params=["project_name", "project_type"],
            optional_params=["project_description", "budget_limit", "timeline_months", "specific_requirements"],
            estimated_time=15,
            complexity="high",
            tags=["анализ", "проект", "строительство", "отчет"]
        )
        
        # Автоматическое планирование проекта
        self.register_meta_tool(
            name="automated_project_planning",
            handler=self._automated_project_planning,
            description="Автоматическое планирование строительного проекта: анализ работ, создание графика, расчет ресурсов",
            category=MetaToolCategory.PLANNING,
            required_params=["project_data", "works_list"],
            optional_params=["constraints", "resources", "priorities"],
            estimated_time=20,
            complexity="high",
            tags=["планирование", "график", "ресурсы", "проект"]
        )
        
        # Комплексная проверка соответствия нормам
        self.register_meta_tool(
            name="comprehensive_compliance_check",
            handler=self._comprehensive_compliance_check,
            description="Комплексная проверка проекта на соответствие строительным нормам и правилам",
            category=MetaToolCategory.ANALYSIS,
            required_params=["project_documents"],
            optional_params=["specific_norms", "region", "building_type"],
            estimated_time=10,
            complexity="medium",
            tags=["нормы", "соответствие", "проверка", "СП", "ГОСТ"]
        )
        
        # Автоматическое создание ППР
        self.register_meta_tool(
            name="automated_ppr_generation",
            handler=self._automated_ppr_generation,
            description="Автоматическое создание проекта производства работ на основе проектной документации",
            category=MetaToolCategory.AUTOMATION,
            required_params=["project_docs", "work_type"],
            optional_params=["safety_requirements", "equipment_list", "timeline"],
            estimated_time=25,
            complexity="high",
            tags=["ППР", "производство работ", "автоматизация"]
        )
        
        # Оптимизация стоимости проекта
        self.register_meta_tool(
            name="project_cost_optimization",
            handler=self._project_cost_optimization,
            description="Оптимизация стоимости проекта: анализ альтернатив, поиск экономии, рекомендации",
            category=MetaToolCategory.OPTIMIZATION,
            required_params=["project_estimate", "optimization_goals"],
            optional_params=["constraints", "alternatives", "acceptable_changes"],
            estimated_time=12,
            complexity="medium",
            tags=["оптимизация", "стоимость", "экономия", "смета"]
        )
    
    async def execute_meta_tool(self, name: str, **params) -> Dict[str, Any]:
        """
        Выполнение мета-инструмента
        
        Args:
            name: Имя мета-инструмента
            **params: Параметры для выполнения
            
        Returns:
            Результат выполнения мета-инструмента
        """
        if name not in self.meta_tools:
            return {"error": f"Мета-инструмент '{name}' не найден"}
        
        meta_tool = self.meta_tools[name]
        handler = self.meta_tool_handlers[name]
        
        # Проверяем обязательные параметры
        missing_params = [p for p in meta_tool.required_params if p not in params]
        if missing_params:
            return {"error": f"Отсутствуют обязательные параметры: {missing_params}"}
        
        logger.info(f"Запуск мета-инструмента: {name}")
        start_time = datetime.now()
        
        try:
            # Выполняем мета-инструмент
            result = await handler(**params)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Мета-инструмент '{name}' выполнен за {execution_time:.2f} секунд")
            
            return {
                "meta_tool": name,
                "status": "success",
                "execution_time": execution_time,
                "result": result
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Ошибка выполнения мета-инструмента '{name}': {e}")
            
            return {
                "meta_tool": name,
                "status": "error",
                "execution_time": execution_time,
                "error": str(e)
            }
    
    # ====== РЕАЛИЗАЦИИ МЕТА-ИНСТРУМЕНТОВ ======
    
    async def _comprehensive_analysis_project(self, **params) -> Dict[str, Any]:
        """
        Комплексный анализ строительного проекта
        
        Выполняет полный анализ проекта включая:
        1. Поиск и анализ применимых норм
        2. Анализ проектной документации
        3. Расчет предварительной сметы
        4. Анализ рисков и ограничений
        5. Генерация комплексного отчета
        """
        project_name = params.get("project_name")
        project_type = params.get("project_type")
        project_description = params.get("project_description", "")
        budget_limit = params.get("budget_limit")
        timeline_months = params.get("timeline_months")
        specific_requirements = params.get("specific_requirements", [])
        
        logger.info(f"Начало комплексного анализа проекта: {project_name}")
        
        # Создаем workflow для анализа проекта
        workflow = self.orchestrator.create_workflow(
            name=f"Анализ проекта: {project_name}",
            description=f"Комплексный анализ строительного проекта типа '{project_type}'"
        )
        
        # ШАГ 1: Поиск применимых строительных норм
        search_norms_task = self.orchestrator.add_task_to_workflow(
            workflow.id,
            "search_rag_database",
            {
                "query": f"строительные нормы {project_type} {' '.join(specific_requirements)}",
                "doc_types": ["norms", "sp", "gost"],
                "n_results": 10
            },
            priority=Priority.HIGH
        )
        
        # ШАГ 2: Параллельный поиск проектной документации
        search_projects_task = self.orchestrator.add_task_to_workflow(
            workflow.id,
            "search_rag_database",
            {
                "query": f"проектная документация {project_type}",
                "doc_types": ["rd", "ppr"],
                "n_results": 5
            },
            priority=Priority.HIGH
        )
        
        # ШАГ 3: Анализ нормативных требований (зависит от поиска норм)
        analyze_norms_task = self.orchestrator.add_task_to_workflow(
            workflow.id,
            "check_normative",
            {
                "project_type": project_type,
                "requirements": specific_requirements
            },
            dependencies=[search_norms_task],
            priority=Priority.NORMAL
        )
        
        # ШАГ 4: Извлечение списка работ
        extract_works_task = self.orchestrator.add_task_to_workflow(
            workflow.id,
            "extract_works_nlp",
            {
                "text": f"Проект {project_name}: {project_description}",
                "doc_type": project_type
            },
            dependencies=[search_projects_task],
            priority=Priority.NORMAL
        )
        
        # ШАГ 5: Расчет предварительной сметы
        calculate_estimate_task = self.orchestrator.add_task_to_workflow(
            workflow.id,
            "calculate_estimate",
            {
                "project_name": project_name,
                "project_type": project_type,
                "description": project_description
            },
            dependencies=[extract_works_task],
            priority=Priority.NORMAL
        )
        
        # ШАГ 6: Анализ финансовых метрик
        financial_analysis_task = self.orchestrator.add_task_to_workflow(
            workflow.id,
            "calculate_financial_metrics",
            {
                "type": "comprehensive",
                "budget_limit": budget_limit,
                "timeline_months": timeline_months
            },
            dependencies=[calculate_estimate_task],
            priority=Priority.NORMAL
        )
        
        # ШАГ 7: Создание графика работ
        create_schedule_task = self.orchestrator.add_task_to_workflow(
            workflow.id,
            "create_gantt_chart",
            {
                "project_name": project_name,
                "timeline_months": timeline_months or 12
            },
            dependencies=[extract_works_task],
            priority=Priority.NORMAL
        )
        
        # ШАГ 8: Анализ рисков (зависит от всех предыдущих анализов)
        risk_analysis_task = self.orchestrator.add_task_to_workflow(
            workflow.id,
            "analyze_tender",
            {
                "project_data": {
                    "name": project_name,
                    "type": project_type,
                    "description": project_description
                },
                "analysis_type": "risk_assessment"
            },
            dependencies=[analyze_norms_task, financial_analysis_task],
            priority=Priority.NORMAL
        )
        
        # ШАГ 9: Генерация комплексного отчета (финальный шаг)
        generate_report_task = self.orchestrator.add_task_to_workflow(
            workflow.id,
            "create_document",
            {
                "template": "comprehensive_analysis_report",
                "data": {
                    "project_name": project_name,
                    "project_type": project_type,
                    "analysis_date": datetime.now().isoformat()
                }
            },
            dependencies=[risk_analysis_task, create_schedule_task],
            priority=Priority.CRITICAL
        )
        
        # Выполняем workflow
        workflow_result = await self.orchestrator.execute_workflow(workflow.id)
        
        if workflow_result.get("status") == "failed":
            return {"error": f"Ошибка выполнения анализа: {workflow_result.get('error')}"}
        
        # Собираем результаты анализа
        results = workflow_result.get("results", {})
        
        return {
            "project_name": project_name,
            "project_type": project_type,
            "workflow_id": workflow.id,
            "analysis_summary": {
                "norms_found": len(results.get(search_norms_task, {}).get("data", [])) if search_norms_task in results else 0,
                "projects_analyzed": len(results.get(search_projects_task, {}).get("data", [])) if search_projects_task in results else 0,
                "works_extracted": len(results.get(extract_works_task, {}).get("data", [])) if extract_works_task in results else 0,
                "estimate_calculated": calculate_estimate_task in results,
                "schedule_created": create_schedule_task in results,
                "risks_analyzed": risk_analysis_task in results,
                "report_generated": generate_report_task in results
            },
            "detailed_results": results,
            "execution_stats": {
                "total_tasks": workflow_result.get("tasks_total"),
                "completed_tasks": workflow_result.get("tasks_completed"),
                "execution_time": workflow_result.get("execution_time")
            }
        }
    
    async def _automated_project_planning(self, **params) -> Dict[str, Any]:
        """
        Автоматическое планирование строительного проекта
        """
        project_data = params.get("project_data", {})
        works_list = params.get("works_list", [])
        constraints = params.get("constraints", {})
        resources = params.get("resources", {})
        priorities = params.get("priorities", {})
        
        logger.info("Начало автоматического планирования проекта")
        
        # Создаем workflow для планирования
        workflow = self.orchestrator.create_workflow(
            name="Автоматическое планирование проекта",
            description="Создание полного плана проекта с учетом ресурсов и ограничений"
        )
        
        # Добавляем задачи планирования
        sequence_task = self.orchestrator.add_task_to_workflow(
            workflow.id,
            "get_work_sequence",
            {"works": works_list, "constraints": constraints}
        )
        
        critical_path_task = self.orchestrator.add_task_to_workflow(
            workflow.id,
            "calculate_critical_path",
            {"project_data": project_data, "works": works_list},
            dependencies=[sequence_task]
        )
        
        schedule_task = self.orchestrator.add_task_to_workflow(
            workflow.id,
            "create_construction_schedule",
            {"project_data": project_data, "resources": resources},
            dependencies=[critical_path_task]
        )
        
        gantt_task = self.orchestrator.add_task_to_workflow(
            workflow.id,
            "create_gantt_chart",
            {"project_data": project_data},
            dependencies=[schedule_task]
        )
        
        # Выполняем workflow
        workflow_result = await self.orchestrator.execute_workflow(workflow.id)
        
        return {
            "planning_complete": workflow_result.get("status") != "failed",
            "workflow_id": workflow.id,
            "results": workflow_result.get("results", {}),
            "execution_time": workflow_result.get("execution_time")
        }
    
    async def _comprehensive_compliance_check(self, **params) -> Dict[str, Any]:
        """
        Комплексная проверка соответствия нормам
        """
        project_documents = params.get("project_documents", [])
        specific_norms = params.get("specific_norms", [])
        region = params.get("region", "москва")
        building_type = params.get("building_type", "")
        
        logger.info("Начало комплексной проверки соответствия нормам")
        
        # Создаем workflow для проверки
        workflow = self.orchestrator.create_workflow(
            name="Проверка соответствия нормам",
            description="Комплексная проверка проекта на соответствие строительным нормам"
        )
        
        # Поиск применимых норм
        norms_search_task = self.orchestrator.add_task_to_workflow(
            workflow.id,
            "search_rag_database",
            {
                "query": f"строительные нормы {building_type} {region}",
                "doc_types": ["norms", "sp", "gost"],
                "n_results": 15
            }
        )
        
        # Проверка каждого документа
        compliance_tasks = []
        for i, doc in enumerate(project_documents):
            task_id = self.orchestrator.add_task_to_workflow(
                workflow.id,
                "check_normative",
                {
                    "document": doc,
                    "building_type": building_type,
                    "region": region
                },
                dependencies=[norms_search_task]
            )
            compliance_tasks.append(task_id)
        
        # Сводный анализ соответствия
        if compliance_tasks:
            summary_task = self.orchestrator.add_task_to_workflow(
                workflow.id,
                "analyze_tender",
                {
                    "analysis_type": "compliance_summary",
                    "documents": project_documents
                },
                dependencies=compliance_tasks
            )
        
        # Выполняем workflow
        workflow_result = await self.orchestrator.execute_workflow(workflow.id)
        
        return {
            "compliance_check_complete": workflow_result.get("status") != "failed",
            "workflow_id": workflow.id,
            "documents_checked": len(project_documents),
            "results": workflow_result.get("results", {}),
            "execution_time": workflow_result.get("execution_time")
        }
    
    async def _automated_ppr_generation(self, **params) -> Dict[str, Any]:
        """
        Автоматическое создание ППР
        """
        project_docs = params.get("project_docs", [])
        work_type = params.get("work_type", "")
        safety_requirements = params.get("safety_requirements", [])
        equipment_list = params.get("equipment_list", [])
        timeline = params.get("timeline", {})
        
        logger.info(f"Начало автоматического создания ППР для работ: {work_type}")
        
        # Создаем workflow для создания ППР
        workflow = self.orchestrator.create_workflow(
            name=f"Создание ППР: {work_type}",
            description="Автоматическое создание проекта производства работ"
        )
        
        # Поиск примеров ППР
        search_ppr_task = self.orchestrator.add_task_to_workflow(
            workflow.id,
            "search_rag_database",
            {
                "query": f"ППР проект производства работ {work_type}",
                "doc_types": ["ppr"],
                "n_results": 5
            }
        )
        
        # Извлечение последовательности работ
        extract_sequence_task = self.orchestrator.add_task_to_workflow(
            workflow.id,
            "get_work_sequence",
            {"work_type": work_type, "project_docs": project_docs},
            dependencies=[search_ppr_task]
        )
        
        # Генерация ППР
        generate_ppr_task = self.orchestrator.add_task_to_workflow(
            workflow.id,
            "generate_ppr",
            {
                "work_type": work_type,
                "safety_requirements": safety_requirements,
                "equipment_list": equipment_list,
                "timeline": timeline
            },
            dependencies=[extract_sequence_task]
        )
        
        # Создание графика работ
        schedule_task = self.orchestrator.add_task_to_workflow(
            workflow.id,
            "create_construction_schedule",
            {"work_type": work_type, "timeline": timeline},
            dependencies=[generate_ppr_task]
        )
        
        # Выполняем workflow
        workflow_result = await self.orchestrator.execute_workflow(workflow.id)
        
        return {
            "ppr_generated": workflow_result.get("status") != "failed",
            "work_type": work_type,
            "workflow_id": workflow.id,
            "results": workflow_result.get("results", {}),
            "execution_time": workflow_result.get("execution_time")
        }
    
    async def _project_cost_optimization(self, **params) -> Dict[str, Any]:
        """
        Оптимизация стоимости проекта
        """
        project_estimate = params.get("project_estimate", {})
        optimization_goals = params.get("optimization_goals", [])
        constraints = params.get("constraints", {})
        alternatives = params.get("alternatives", [])
        acceptable_changes = params.get("acceptable_changes", [])
        
        logger.info("Начало оптимизации стоимости проекта")
        
        # Создаем workflow для оптимизации
        workflow = self.orchestrator.create_workflow(
            name="Оптимизация стоимости проекта",
            description="Поиск возможностей экономии и оптимизации расходов"
        )
        
        # Анализ текущей сметы
        analyze_estimate_task = self.orchestrator.add_task_to_workflow(
            workflow.id,
            "calculate_financial_metrics",
            {
                "estimate_data": project_estimate,
                "analysis_type": "cost_breakdown"
            }
        )
        
        # Поиск альтернативных решений
        alternatives_task = self.orchestrator.add_task_to_workflow(
            workflow.id,
            "search_rag_database",
            {
                "query": "альтернативные материалы технологии экономия",
                "doc_types": ["smeta", "materials"],
                "n_results": 10
            }
        )
        
        # Monte Carlo анализ рисков
        risk_analysis_task = self.orchestrator.add_task_to_workflow(
            workflow.id,
            "monte_carlo_sim",
            {
                "project_data": project_estimate,
                "optimization_goals": optimization_goals
            },
            dependencies=[analyze_estimate_task, alternatives_task]
        )
        
        # Генерация рекомендаций
        recommendations_task = self.orchestrator.add_task_to_workflow(
            workflow.id,
            "create_document",
            {
                "template": "cost_optimization_report",
                "data": {
                    "optimization_goals": optimization_goals,
                    "constraints": constraints
                }
            },
            dependencies=[risk_analysis_task]
        )
        
        # Выполняем workflow
        workflow_result = await self.orchestrator.execute_workflow(workflow.id)
        
        return {
            "optimization_complete": workflow_result.get("status") != "failed",
            "workflow_id": workflow.id,
            "results": workflow_result.get("results", {}),
            "execution_time": workflow_result.get("execution_time")
        }
    
    # ====== UTILITY METHODS ======
    
    def list_meta_tools(self) -> Dict[str, Any]:
        """Получить список всех доступных мета-инструментов"""
        return {
            "meta_tools": [
                {
                    "name": name,
                    "description": tool.description,
                    "category": tool.category.value,
                    "required_params": tool.required_params,
                    "optional_params": tool.optional_params,
                    "estimated_time": tool.estimated_time,
                    "complexity": tool.complexity,
                    "tags": tool.tags
                }
                for name, tool in self.meta_tools.items()
            ],
            "total": len(self.meta_tools)
        }
    
    def get_meta_tool_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Получить подробную информацию о мета-инструменте"""
        if name not in self.meta_tools:
            return None
        
        tool = self.meta_tools[name]
        return {
            "name": name,
            "description": tool.description,
            "category": tool.category.value,
            "required_params": tool.required_params,
            "optional_params": tool.optional_params,
            "estimated_time": tool.estimated_time,
            "complexity": tool.complexity,
            "tags": tool.tags
        }
    
    def search_meta_tools(self, query: str, category: Optional[MetaToolCategory] = None) -> List[Dict[str, Any]]:
        """Поиск мета-инструментов по запросу"""
        query_lower = query.lower()
        results = []
        
        for name, tool in self.meta_tools.items():
            # Фильтр по категории
            if category and tool.category != category:
                continue
            
            # Поиск по имени, описанию и тегам
            searchable_text = f"{name} {tool.description} {' '.join(tool.tags)}".lower()
            if query_lower in searchable_text:
                results.append({
                    "name": name,
                    "description": tool.description,
                    "category": tool.category.value,
                    "relevance": searchable_text.count(query_lower),  # Простой счетчик релевантности
                    "estimated_time": tool.estimated_time,
                    "complexity": tool.complexity
                })
        
        # Сортируем по релевантности
        results.sort(key=lambda x: x["relevance"], reverse=True)
        return results
    
    def get_orchestrator_statistics(self) -> Dict[str, Any]:
        """Получить статистику работы оркестратора"""
        return self.orchestrator.get_statistics()


# Пример использования
async def example_meta_tools_usage():
    """Пример использования Meta-Tools System"""
    
    # Mock tools system для примера
    class MockToolsSystem:
        def execute_tool(self, tool_name: str, **params):
            return f"Mock result from {tool_name} with params: {params}"
    
    # Создаем систему мета-инструментов
    tools_system = MockToolsSystem()
    meta_system = MetaToolsSystem(tools_system)
    
    # Получаем список доступных мета-инструментов
    meta_tools_list = meta_system.list_meta_tools()
    print("Доступные мета-инструменты:")
    for tool in meta_tools_list["meta_tools"]:
        print(f"- {tool['name']}: {tool['description']}")
    
    # Выполняем комплексный анализ проекта
    result = await meta_system.execute_meta_tool(
        "comprehensive_analysis_project",
        project_name="Жилой комплекс 'Северный'",
        project_type="жилое строительство",
        project_description="Многоэтажный жилой комплекс из 3 домов",
        budget_limit=500000000,
        timeline_months=24,
        specific_requirements=["энергоэффективность", "парковка", "детская площадка"]
    )
    
    print("Результат комплексного анализа:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    # Запуск примера
    asyncio.run(example_meta_tools_usage())