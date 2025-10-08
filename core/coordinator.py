import json
import base64
import threading
from typing import Dict, Any, List, Optional
from core.model_manager import ModelManager

class Coordinator:
    def __init__(self, model_manager: ModelManager, tools_system: Any, rag_system: Any):
        """
        Coordinator - центральный интеллект системы SuperBuilder.
        
        Args:
            model_manager: Менеджер моделей для работы с ролями
            tools_system: Система инструментов для выполнения задач
            rag_system: RAG система для поиска информации
        """
        self.model_manager = model_manager
        self.tools_system = tools_system
        self.rag_system = rag_system
        
        # История взаимодействий с блокировкой для потокобезопасности
        self.history = []
        self.history_lock = threading.Lock()
        self.max_history_length = 100
        
        # Получить клиента координатора
        self.coordinator_client = self.model_manager.get_model_client("coordinator")
    
    def _add_to_history(self, entry: Dict[str, Any]):
        """Добавить запись в историю с блокировкой и ограничением длины"""
        with self.history_lock:
            self.history.append(entry)
            # Ограничить длину истории
            if len(self.history) > self.max_history_length:
                self.history = self.history[-self.max_history_length:]
    
    def analyze_request_complexity(self, user_input: str) -> str:
        """
        Анализ сложности запроса и определение категории.
        
        Args:
            user_input: Запрос пользователя
            
        Returns:
            Категория запроса
        """
        # Определить категорию запроса на основе ключевых слов
        text_lower = user_input.lower()
        
        if any(keyword in text_lower for keyword in ["норма", "сп ", "гост", "снип", "фз", "пункт", "cl.", "cl ", "cl:"]):
            return "norms"
        elif any(keyword in text_lower for keyword in ["ппр", "производства работ", "технологическая карта"]):
            return "ppr"
        elif any(keyword in text_lower for keyword in ["смета", "расчет", "бюджет", "гэсн", "фер", "стоимость"]):
            return "estimate"
        elif any(keyword in text_lower for keyword in ["рабочая документация", "чертеж", "спецификация", "dwg", "dxf", "ifc"]):
            return "rd"
        elif any(keyword in text_lower for keyword in ["учебник", "учебные материалы", "обучение", "курс"]):
            return "educational"
        elif any(keyword in text_lower for keyword in ["проект", "работы", "график", "планирование"]):
            return "project"
        else:
            return "general"
    
    def analyze_request(self, user_input: str) -> Dict[str, Any]:
        """
        Анализ запроса пользователя и формирование JSON-плана действий.
        
        Args:
            user_input: Запрос пользователя
            
        Returns:
            JSON-план действий
        """
        # If message contains transcription wrapper, extract the actual text
        normalized_input = user_input
        try:
            marker = "Транскрипция:"
            if isinstance(user_input, str) and marker in user_input:
                after = user_input.split(marker, 1)[1].strip()
                # Trim surrounding quotes if any
                if after.startswith("'") or after.startswith('"'):
                    after = after[1:]
                if after.endswith("'") or after.endswith('"'):
                    after = after[:-1]
                if len(after) >= 3:
                    normalized_input = after
        except Exception:
            normalized_input = user_input

        print(f"Анализ запроса: {normalized_input}")
        
        # Добавить запрос в историю
        self._add_to_history({
            "type": "user_request",
            "content": normalized_input,
            "timestamp": __import__('time').time()
        })
        
        # Искусственных упрощённых правил нет: дальнейшее решение — на стороне модели/плана

        # Parse request using SBERT for better accuracy
        try:
            from core.parse_utils import parse_request_with_sbert
            parse_result = parse_request_with_sbert(normalized_input)
            print(f"SBERT Parse Result: {parse_result}")
        except Exception as e:
            print(f"Error in SBERT parsing: {e}")
            parse_result = {"intent": "unknown", "confidence": 0.0, "entities": {}}
        
        # Определить тип запроса и необходимые инструменты
        plan = self._generate_plan(normalized_input, parse_result)
        
        return plan
    
    def _generate_plan(self, user_input: str, parse_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Генерация плана действий на основе запроса пользователя с использованием реального координатора.
        
        Args:
            user_input: Запрос пользователя
            parse_result: Результат парсинга с помощью SBERT
            
        Returns:
            JSON-план действий
        """
        # Использовать модель координатора для анализа запроса и формирования плана
        try:
            # Получить модель координатора
            coordinator_model = self.model_manager.get_model_client("coordinator")
            
            # Подготовить контекст для модели
            tools_description = """
ДОСТУПНЫЕ ИНСТРУМЕНТЫ:
- search_knowledge_base: Поиск в базе знаний
- calculate_estimate: Расчет сметы
- find_normatives: Поиск нормативов
- extract_works_nlp: Извлечение работ из текста
- generate_mermaid_diagram: Генерация диаграмм
- create_gantt_chart: Создание диаграмм Ганта
- create_pie_chart: Создание круговых диаграмм
- create_bar_chart: Создание столбчатых диаграмм
- get_work_sequence: Получение последовательности работ
- extract_construction_data: Извлечение строительных данных
- create_construction_schedule: Создание графика строительства
- calculate_critical_path: Расчет критического пути
- extract_financial_data: Извлечение финансовых данных
- analyze_image: Анализ изображений
- generate_letter: Генерация официальных писем
- auto_budget: Автоматический расчет бюджета
- generate_ppr: Генерация ППР
- create_gpp: Создание ГПП
- parse_gesn_estimate: Парсинг смет по ГЭСН
- analyze_tender: Анализ тендеров
- search_rag_database: Поиск в RAG базе
- check_normative: Проверка нормативов
- create_document: Создание документов
- generate_construction_schedule: Генерация графика строительства
- calculate_financial_metrics: Расчет финансовых метрик
- extract_text_from_pdf: Извлечение текста из PDF
- analyze_bentley_model: Анализ моделей Bentley
- autocad_export: Экспорт в AutoCAD
- monte_carlo_sim: Симуляция Monte Carlo
- semantic_parse: SBERT NLU для определения намерений и сущностей
"""

            roles_list = """
ДОСТУПНЫЕ РОЛИ:
- coordinator: Координатор (стратегическое управление)
- analyst: Аналитик (анализ данных и расчеты)
- chief_engineer: Главный инженер (технические решения)
- project_manager: Менеджер проекта (управление проектами)
- construction_worker: Строитель (практическая реализация)
"""

            # Prepare input data with SBERT parsing results
            input_data = f"Запрос пользователя: {user_input}"
            if parse_result:
                input_data += f"\nSBERT Parse: intent='{parse_result.get('intent', 'unknown')}', confidence={parse_result.get('confidence', 0.0)}, entities={parse_result.get('entities', {})}"
            
            analysis_prompt = f"""
Проанализируй запрос пользователя и сформируй JSON-план действий.

{input_data}

ВАЖНЫЕ ПРАВИЛА:
1. Всегда возвращай строго JSON-объект
2. Используй только доступные инструменты и роли
3. Указывай конкретные аргументы для инструментов
4. Планируй пошаговое выполнение задач
5. Учитывай результаты SBERT парсинга при выборе инструментов и ролей

Пример возвращаемого JSON:
{{
    "status": "planning",
    "query_type": "тип_запроса",
    "requires_tools": true,
    "tools": [
        {{
            "name": "имя_инструмента",
            "arguments": {{
                "параметр1": "значение1",
                "параметр2": "значение2"
            }}
        }}
    ],
    "roles_involved": ["роль1", "роль2"],
    "required_data": ["данные1", "данные2"],
    "next_steps": ["шаг1", "шаг2"]
}}
"""

            # Выполнить запрос к координатору
            messages = [
                {
                    "role": "system",
                    "content": analysis_prompt + tools_description + roles_list
                },
                {
                    "role": "user",
                    "content": user_input
                }
            ]
            
            response = self.model_manager.query("coordinator", messages)
            
            # Попытаться извлечь JSON из ответа
            try:
                # Ищем JSON в ответе
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    plan_json = json_match.group()
                    plan = json.loads(plan_json)
                    return plan
                else:
                    # Если JSON не найден, используем резервный подход
                    raise ValueError("JSON not found in response")
            except (json.JSONDecodeError, ValueError):
                # Резервный подход на основе ключевых слов
                print("Не удалось распарсить JSON из ответа координатора, используем резервный подход")
                pass
                
        except Exception as e:
            print(f"Ошибка генерации плана с помощью модели: {e}")
            # Использовать резервный подход на основе ключевых слов
            pass
        
        # Определить тип запроса на основе ключевых слов (резервный подход)
        if any(keyword in user_input.lower() for keyword in ["стоимость", "смета", "расчет", "финанс", "бюджет"]):
            # Финансовый запрос
            return {
                "status": "planning",
                "query_type": "financial",
                "requires_tools": True,
                "tools": [
                    {"name": "search_rag_database", "arguments": {"query": user_input, "doc_types": ["estimate", "smeta"]}},
                    {"name": "calculate_estimate", "arguments": {"query": user_input}}
                ],
                "roles_involved": ["analyst", "chief_engineer"],
                "required_data": ["расценки", "материалы", "работы"],
                "next_steps": [
                    "Поиск соответствующих расценок в базе знаний",
                    "Расчет стоимости с учетом материалов и работ"
                ]
            }
        elif any(keyword in user_input.lower() for keyword in ["норма", "сп ", "гост", "снип", "фз", "пункт"]):
            # Простой нормативный запрос - только поиск и ответ
            return {
                "status": "planning",
                "query_type": "normative_simple",
                "requires_tools": True,
                "tools": [
                    {"name": "search_rag_database", "arguments": {"query": user_input, "doc_types": ["norms"], "n_results": 3}}
                ],
                "roles_involved": ["coordinator"],
                "required_data": ["нормативные документы"],
                "next_steps": [
                    "Поиск нормативных документов",
                    "Ответ пользователю"
                ],
                "requires_specialists": False  # Модель сама решает
            }
        elif any(keyword in user_input.lower() for keyword in ["проект", "ппр", "технологическая карта", "работы", "график"]):
            # Проектный запрос
            return {
                "status": "planning",
                "query_type": "project",
                "requires_tools": True,
                "tools": [
                    {"name": "search_rag_database", "arguments": {"query": user_input, "doc_types": ["ppr", "rd"]}},
                    {"name": "extract_works_nlp", "arguments": {"text": user_input, "doc_type": "ppr"}},
                    {"name": "create_gantt_chart", "arguments": {"tasks": [], "title": "График работ"}}
                ],
                "roles_involved": ["project_manager", "construction_worker"],
                "required_data": ["проектные документы", "технологические карты"],
                "next_steps": [
                    "Поиск проектной документации",
                    "Анализ последовательности работ",
                    "Создание графика выполнения работ"
                ]
            }
        elif any(keyword in user_input.lower() for keyword in ["диаграмма", "график", "chart", "diagram"]):
            # Запрос на создание диаграммы
            return {
                "status": "planning",
                "query_type": "visualization",
                "requires_tools": True,
                "tools": [
                    {"name": "generate_mermaid_diagram", "arguments": {"type": "flow", "data": {}}},
                    {"name": "create_pie_chart", "arguments": {"data": [], "title": "Диаграмма"}}
                ],
                "roles_involved": ["analyst", "project_manager"],
                "required_data": ["данные для визуализации"],
                "next_steps": [
                    "Генерация диаграммы",
                    "Подготовка данных для визуализации"
                ]
            }
        elif any(keyword in user_input.lower() for keyword in ["письмо", "официальное", "деловое"]):
            # Запрос на создание официального письма
            return {
                "status": "planning",
                "query_type": "official_letter",
                "requires_tools": True,
                "tools": [
                    {"name": "generate_letter", "arguments": {"template": "compliance_sp31", "data": {}}}
                ],
                "roles_involved": ["chief_engineer"],
                "required_data": ["шаблон письма", "данные получателя"],
                "next_steps": [
                    "Определение типа письма",
                    "Сбор данных для письма",
                    "Генерация официального письма"
                ]
            }
        elif any(keyword in user_input.lower() for keyword in ["бюджет", "автоматический", "смета", "гэсн"]):
            # Запрос на автоматический бюджет
            return {
                "status": "planning",
                "query_type": "auto_budget",
                "requires_tools": True,
                "tools": [
                    {"name": "parse_gesn_estimate", "arguments": {"estimate_file": "", "region": "ekaterinburg"}},
                    {"name": "auto_budget", "arguments": {"estimate_data": {}, "gesn_rates": {}}}
                ],
                "roles_involved": ["analyst"],
                "required_data": ["сметные данные", "ГЭСН расценки"],
                "next_steps": [
                    "Парсинг сметного файла",
                    "Получение ГЭСН расценок",
                    "Расчет автоматического бюджета"
                ]
            }
        elif any(keyword in user_input.lower() for keyword in ["ппр", "производства работ"]):
            # Запрос на создание ППР
            return {
                "status": "planning",
                "query_type": "ppr_generation",
                "requires_tools": True,
                "tools": [
                    {"name": "get_work_sequence", "arguments": {"query": "stage11_work_sequence"}},
                    {"name": "generate_ppr", "arguments": {"project_data": {}, "works_seq": []}}
                ],
                "roles_involved": ["chief_engineer"],
                "required_data": ["данные проекта", "последовательность работ"],
                "next_steps": [
                    "Получение последовательности работ из stage11",
                    "Генерация проекта производства работ"
                ]
            }
        elif any(keyword in user_input.lower() for keyword in ["гпп", "график", "производства"]):
            # Запрос на создание ГПП
            return {
                "status": "planning",
                "query_type": "gpp_creation",
                "requires_tools": True,
                "tools": [
                    {"name": "get_work_sequence", "arguments": {"query": "stage11_work_sequence"}},
                    {"name": "create_gpp", "arguments": {"works_seq": [], "timeline": {}}}
                ],
                "roles_involved": ["project_manager"],
                "required_data": ["последовательность работ", "временная шкала"],
                "next_steps": [
                    "Получение последовательности работ из stage11",
                    "Создание графика производства работ"
                ]
            }
        elif any(keyword in user_input.lower() for keyword in ["анализ", "тендер", "проекта"]):
            # Запрос на комплексный анализ проекта/тендера
            return {
                "status": "planning",
                "query_type": "tender_analysis",
                "requires_tools": True,
                "tools": [
                    {"name": "search_rag_database", "arguments": {"query": user_input, "doc_types": ["norms", "ppr", "smeta"]}},
                    {"name": "analyze_tender", "arguments": {"tender_data": {}, "requirements": []}}
                ],
                "roles_involved": ["analyst", "chief_engineer", "project_manager"],
                "required_data": ["данные тендера", "требования проекта"],
                "next_steps": [
                    "Сбор информации о тендере",
                    "Комплексный анализ проекта",
                    "Формирование рекомендаций"
                ]
            }
        elif any(keyword in user_input.lower() for keyword in ["roi", "npv", "irr", "доходность", "рентабельность"]):
            # Запрос на финансовые метрики
            return {
                "status": "planning",
                "query_type": "financial_metrics",
                "requires_tools": True,
                "tools": [
                    {"name": "calculate_financial_metrics", "arguments": {"type": "ROI", "profit": 300000000, "cost": 200000000}}
                ],
                "roles_involved": ["analyst"],
                "required_data": ["финансовые показатели"],
                "next_steps": [
                    "Расчет финансовых метрик",
                    "Анализ рентабельности"
                ]
            }
        elif any(keyword in user_input.lower() for keyword in ["bim", "ifc", "анализ модели", "анализ bim"]):
            # Запрос на анализ BIM модели
            return {
                "status": "planning",
                "query_type": "bim_analysis",
                "requires_tools": True,
                "tools": [
                    {"name": "analyze_bentley_model", "arguments": {"ifc_path": "sample.ifc", "analysis_type": "clash"}}
                ],
                "roles_involved": ["chief_engineer", "analyst"],
                "required_data": ["IFC файл модели", "тип анализа"],
                "next_steps": [
                    "Загрузка IFC модели",
                    "Анализ модели на коллизии",
                    "Формирование отчета о нарушениях"
                ]
            }
        elif any(keyword in user_input.lower() for keyword in ["autocad", "dwg", "экспорт в autocad", "экспорт dwg"]):
            # Запрос на экспорт в AutoCAD
            return {
                "status": "planning",
                "query_type": "autocad_export",
                "requires_tools": True,
                "tools": [
                    {"name": "autocad_export", "arguments": {"dwg_data": {}, "works_seq": []}}
                ],
                "roles_involved": ["chief_engineer"],
                "required_data": ["последовательность работ", "параметры экспорта"],
                "next_steps": [
                    "Получение последовательности работ",
                    "Создание DWG файла",
                    "Экспорт чертежа"
                ]
            }
        elif any(keyword in user_input.lower() for keyword in ["monte carlo", "монте-карло", "риск", "анализ рисков", "симуляция"]):
            # Запрос на Monte Carlo симуляцию
            return {
                "status": "planning",
                "query_type": "monte_carlo_simulation",
                "requires_tools": True,
                "tools": [
                    {"name": "monte_carlo_sim", "arguments": {"project_data": {"base_cost": 200000000, "profit": 300000000, "vars": {"cost": 0.2, "time": 0.15, "roi": 0.1}}}}
                ],
                "roles_involved": ["analyst"],
                "required_data": ["базовая стоимость", "прибыль", "параметры вариации"],
                "next_steps": [
                    "Подготовка данных для симуляции",
                    "Запуск Monte Carlo анализа",
                    "Анализ результатов рисков"
                ]
            }
        else:
            # Общий запрос
            return {
                "status": "planning",
                "query_type": "general",
                "requires_tools": True,
                "tools": [
                    {"name": "search_rag_database", "arguments": {"query": user_input, "doc_types": ["norms", "ppr", "smeta", "rd"]}}
                ],
                "roles_involved": ["coordinator"],
                "required_data": ["общая информация"],
                "next_steps": [
                    "Поиск общей информации в базе знаний"
                ]
            }
    
    def execute_tools(self, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Выполнение инструментов из плана.
        
        Args:
            plan: JSON-план действий
            
        Returns:
            Результаты выполнения инструментов
        """
        tool_results = []
        
        if "tools" in plan and plan["tools"]:
            print(f"Выполнение {len(plan['tools'])} инструментов...")
            # Выполняем каждый инструмент из плана
            for i, tool_info in enumerate(plan["tools"]):
                if isinstance(tool_info, dict) and "name" in tool_info:
                    tool_name = tool_info["name"]
                    # Используем "arguments" вместо "params" согласно структуре плана
                    tool_params = tool_info.get("arguments", {})
                    print(f"  → Выполнение {tool_name} с аргументами: {tool_params}")
                    
                    try:
                        result = self.tools_system.execute_tool(tool_name, **tool_params)
                        print(f"  ← Результат: {result}")
                        
                        # Обработка результата
                        if hasattr(result, 'data'):
                            result_data = result.data
                        elif hasattr(result, 'is_success') and result.is_success():
                            result_data = getattr(result, 'data', str(result))
                        else:
                            result_data = str(result)
                        
                        tool_results.append({
                            "tool_name": tool_name,
                            "result": result_data,
                            "status": "success" if hasattr(result, 'is_success') and result.is_success() else "error"
                        })
                    except Exception as e:
                        print(f"  ← Ошибка: {e}")
                        tool_results.append({
                            "tool_name": tool_name,
                            "result": str(e),
                            "status": "error"
                        })
        else:
            print("Инструменты не требуются или не найдены в плане")
        
        return tool_results
    
    def _coordinate_with_specialists(self, plan: Dict[str, Any], tool_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Координация с специалистами на основе плана и результатов инструментов.
        
        Args:
            plan: JSON-план действий
            tool_results: Результаты выполнения инструментов
            
        Returns:
            Ответы специалистов
        """
        specialist_responses = []
        
        if "roles_involved" in plan and plan["roles_involved"]:
            for role in plan["roles_involved"]:
                if role != "coordinator":  # Координатор не отвечает сам себе
                    try:
                        # Получить клиента модели для роли
                        model_client = self.model_manager.get_model_client(role)
                        if model_client:
                            # Подготовить промт для специалиста
                            specialist_prompt = self._create_specialist_prompt(role, plan, tool_results)
                            
                            # Выполнить запрос к специалисту
                            messages = [
                                {
                                    "role": "system",
                                    "content": self.model_manager.get_capabilities_prompt(role)
                                },
                                {
                                    "role": "user",
                                    "content": specialist_prompt
                                }
                            ]
                            
                            response_content = self.model_manager.query(role, messages)
                            response = {
                                "role": role,
                                "response": response_content,
                                "tool_results": tool_results
                            }
                            specialist_responses.append(response)
                    except Exception as e:
                        print(f"Ошибка получения ответа от специалиста {role}: {e}")
        
        return specialist_responses
    
    def _create_specialist_prompt(self, role: str, plan: Dict[str, Any], tool_results: List[Dict[str, Any]]) -> str:
        """
        Создание промта для специалиста на основе плана и результатов инструментов.
        
        Args:
            role: Роль специалиста
            plan: План действий
            tool_results: Результаты выполнения инструментов
            
        Returns:
            Промт для специалиста
        """
        prompt = f"Вы - {role}. Вам нужно выполнить следующую задачу:\n\n"
        prompt += f"Запрос пользователя: {plan.get('query_type', 'общий запрос')}\n\n"
        
        if tool_results:
            prompt += "Результаты выполнения инструментов:\n"
            for result in tool_results:
                if result.get("status") == "success":
                    prompt += f"- {result.get('tool_name', 'Инструмент')}: {result.get('result', 'Результат')}\n"
                else:
                    prompt += f"- {result.get('tool_name', 'Инструмент')}: ОШИБКА - {result.get('result', 'Неизвестная ошибка')}\n"
            prompt += "\n"
        
        prompt += "Пожалуйста, предоставьте профессиональный анализ и рекомендации по данной задаче."
        return prompt
    
    def synthesize_response(self, user_input: str, tool_results: List[Dict[str, Any]], 
                          specialist_responses: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        СИНТЕЗ ФИНАЛЬНОГО ОТВЕТА НА ОСНОВЕ РЕЗУЛЬТАТОВ ИНСТРУМЕНТОВ.
        """
        print(f"Синтез ответа на запрос: {user_input}")

        # 1) Прямой ответ по результатам RAG, если есть
        try:
            for result in (tool_results or []):
                if result.get("tool_name") == "search_rag_database" and result.get("status") == "success":
                    data = result.get("result") or {}
                    if isinstance(data, dict):
                        rag_results = data.get("results", []) or (data.get("data", {}) if isinstance(data.get("data"), dict) else {}).get("results", [])
                        if rag_results:
                            first = rag_results[0]
                            content = (first.get("content") if isinstance(first, dict) else None) or first.get("chunk") or "Не найдено содержимого"
                            meta = (first.get("metadata") if isinstance(first, dict) else {}) or {}
                            source = meta.get("source") or meta.get("doc") or meta.get("title") or "Неизвестный источник"
                            return f"Найдено: {content} [Источник: {source}]"
        except Exception as e:
            print(f"Ошибка быстрого RAG-ответа: {e}")

        # 2) Приветствие/самопредставление
        try:
            low = (user_input or '').lower()
            if any(kw in low for kw in ["привет", "кто ты", "что ты", "как дела", "представься"]) or ("как" in low and ("зовут" in low or "называть" in low or "тебя" in low)):
                return (
                    "Привет! Я — Bldr2, ваш AI‑координатор в системе Bldr Empire. "
                    "Ищу нормы (СП, ГОСТ, СНиП), генерирую сметы и отчёты, создаю чек‑листы и графики. "
                    "Сформулируйте задачу — я соберу данные инструментами и верну результат (чаще всего в виде файла)."
                )
        except Exception:
            pass

        # 3) По умолчанию: если ничего полезного не найдено
        return "Не удалось найти информацию по вашему запросу. Попробуйте уточнить."
    
    def clean_response(self, response: str) -> str:
        """
        Очистка ответа от технических деталей и мыслительных процессов.
        
        Args:
            response: Исходный ответ
            
        Returns:
            Очищенный ответ
        """
        # Удалить технические детали и мыслительные процессы
        lines = response.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Пропустить строки с техническими деталями
            if not any(keyword in line.lower() for keyword in ["мышление", "размышление", "process", "thinking"]):
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def process_request(self, user_input: str) -> str:
        """
        Полная обработка запроса пользователя: анализ → выполнение инструментов → синтез ответа.
        
        Args:
            user_input: Запрос пользователя
            
        Returns:
            Финальный ответ
        """
        print(f"Обработка запроса: {user_input}")
        
        # 1. Анализ запроса и формирование плана
        plan = self.analyze_request(user_input)
        print(f"Сформирован план: {json.dumps(plan, ensure_ascii=False, indent=2)}")
        
        # Единый путь обработки - доверяем модели самой решать

        # 2. Выполнение инструментов
        tool_results = self.execute_tools(plan)
        print(f"Выполнены инструменты: {len(tool_results)} результатов")
        
        # 3. Координация с специалистами (если требуется)
        specialist_responses = []
        if plan.get("requires_specialists", True):  # По умолчанию привлекаем специалистов
            specialist_responses = self._coordinate_with_specialists(plan, tool_results)
            print(f"Получены ответы специалистов: {len(specialist_responses)} ответов")
        else:
            print("Пропускаем специалистов по решению модели")
        
        # 4. Синтез финального ответа
        final_response = self.synthesize_response(user_input, tool_results, specialist_responses)
        
        # 5. Очистка ответа
        cleaned_response = self.clean_response(final_response)
        
        # 6. Принудительная очистка памяти (кроме координатора)
        try:
            self.model_manager.force_cleanup()
        except Exception as e:
            print(f"Ошибка очистки памяти: {e}")
        
        return cleaned_response

    def process_photo(self, image_input: str) -> str:
        """
        Обработка фотографии с использованием Qwen2.5-vl-7b для реального анализа.
        
        Args:
            base64_image: Изображение в формате base64
            
        Returns:
            Результат анализа
        """
        try:
            import os
            import base64
            import tempfile

            # Determine if input is a base64 string or file path
            is_existing_path = isinstance(image_input, str) and os.path.exists(image_input)
            temp_path = image_input
            base64_str = None

            if not is_existing_path:
                # Assume base64 string without data URL header
                base64_str = image_input
                # Create temp file for tool processing
                fd, tmpfile = tempfile.mkstemp(suffix=".jpg")
                os.close(fd)
                with open(tmpfile, "wb") as f:
                    try:
                        f.write(base64.b64decode(base64_str))
                    except Exception:
                        # If header present like data:image/jpeg;base64,
                        b64 = base64_str.split(",", 1)[-1]
                        f.write(base64.b64decode(b64))
                temp_path = tmpfile
            else:
                # If we only have a path, try to read and create base64 for VL model
                try:
                    with open(image_input, "rb") as f:
                        base64_str = base64.b64encode(f.read()).decode("utf-8")
                except Exception:
                    base64_str = None

            # Decide VL capability
            try:
                from core.config import MODELS_CONFIG
                coord_model = MODELS_CONFIG.get("coordinator", {}).get("model", "")
                is_vl = isinstance(coord_model, str) and ("-vl-" in coord_model.lower() or "vl" in coord_model.lower())
            except Exception:
                is_vl = False

            # 1) Run tool analysis on file path
            tool_kwargs = {
                "image_path": temp_path,
                "analysis_type": "objects" if is_vl else "basic",
                "ocr_lang": "rus",
                "detect_objects": True,
                "extract_dimensions": True if is_vl else False,
            }
            tool_result = None
            if getattr(self, "tools_system", None):
                tool_result = self.tools_system.execute_tool("analyze_image", **tool_kwargs)

            # 2) Run VL model analysis with base64 data URL if available
            vl_summary = None
            if is_vl and base64_str:
                try:
                    # LM Studio OpenAI-compatible often expects plain strings; pass text + image URL as string
                    prompt_text = (
                        "Проанализируй фото и кратко опиши, что на нём, возможные проблемы/объекты.\n"
                        "Изображение: data:image/jpeg;base64," + base64_str
                    )
                    vl_resp = self.model_manager.query("coordinator", [
                        {"role": "user", "content": prompt_text}
                    ])
                    # Clamp overly short/bad replies
                    vl_summary = str(vl_resp).strip()
                except Exception as vl_e:
                    vl_summary = f"VL-анализ недоступен: {vl_e}"

            # Build combined response
            parts = []
            if vl_summary:
                parts.append(f"[КООРДИНАТОР-VL] {vl_summary}")

            if tool_result is not None:
                if hasattr(tool_result, "is_success") and tool_result.is_success():
                    data = getattr(tool_result, "data", {}) or {}
                    if isinstance(data, dict):
                        brief = data.get("summary") or data.get("result") or str(data)[:500]
                    else:
                        brief = str(data)
                    parts.append(f"[ИНСТРУМЕНТ analyze_image] {brief}")
                else:
                    err = getattr(tool_result, "error", None)
                    parts.append(f"[ИНСТРУМЕНТ analyze_image] Ошибка: {err or 'Неизвестная ошибка'}")

            # Cleanup temp file if we created it
            try:
                if not is_existing_path and temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass

            if parts:
                return "\n\n".join(parts)
            return "Анализ изображения выполнен, но результатов нет"

        except Exception as e:
            return f"Ошибка обработки фотографии: {str(e)}"
    
    def process_document_search(self, query: str) -> str:
        """
        Поиск документов в RAG системе.
        
        Args:
            query: Поисковый запрос
            
        Returns:
            Результаты поиска
        """
        try:
            # Использовать инструмент поиска в RAG
            result = self.tools_system.execute_tool(
                "search_rag_database",
                query=query,
                doc_types=["norms", "ppr", "smeta", "rd", "educational"]
            )
            
            if hasattr(result, "is_success") and result.is_success():
                data = getattr(result, "data", {}) or {}
                results = data.get("results", []) if isinstance(data, dict) else []
                if results:
                    response = "Найденные документы:\n"
                    for i, doc in enumerate(results[:5], 1):  # Ограничить 5 результатами
                        chunk = doc.get("chunk", "")[:200] + "..." if len(doc.get("chunk", "")) > 200 else doc.get("chunk", "")
                        response += f"{i}. {chunk}\n"
                    return response
                else:
                    return "Документы не найдены"
            else:
                err = getattr(result, "error", None)
                return f"Ошибка поиска: {err or 'Неизвестная ошибка'}"
        except Exception as e:
            return f"Ошибка поиска документов: {str(e)}"
    
    def create_and_send_file(self, file_type: str, content: Dict[str, Any]) -> str:
        """
        Создание и отправка файла с реальной генерацией docx/openpyxl и отправкой в Telegram.
        
        Args:
            file_type: Тип файла (docx, xlsx)
            content: Содержимое файла
            
        Returns:
            Результат создания и отправки
        """
        try:
            if file_type == "docx":
                # Создать документ
                result = self.tools_system.execute_tool("create_document", **content)
                if hasattr(result, "is_success") and result.is_success():
                    data = getattr(result, "data", {}) or {}
                    file_path = data.get("file_path", "") if isinstance(data, dict) else str(data)
                    return f"Документ создан: {file_path}"
                else:
                    err = getattr(result, "error", None)
                    return f"Ошибка создания документа: {err or 'Неизвестная ошибка'}"
            else:
                return f"Неподдерживаемый тип файла: {file_type}"
        except Exception as e:
            return f"Ошибка создания файла: {str(e)}"
    
    def _handle_voice_request(self, audio_data: bytes) -> str:
        """
        Обработка голосового запроса с использованием тулзы транскрибации (Whisper)
        и последующего анализа координатором.

        Args:
            audio_data: байты аудиофайла (ogg/opus и др.)
        Returns:
            Человеко-читаемый ответ с транскриптом и анализом
        """
        import tempfile, os
        temp_audio_path = None
        try:
            # Save to temp file
            fd, temp_audio_path = tempfile.mkstemp(suffix='.ogg')
            os.close(fd)
            with open(temp_audio_path, 'wb') as f:
                f.write(audio_data)

            # Use tools system to transcribe
            if not getattr(self, 'tools_system', None):
                return "🎤 Получил голосовое сообщение, но система инструментов недоступна для транскрибации."

            result = self.tools_system.execute_tool("transcribe_audio", audio_path=temp_audio_path, language="ru")
            status = result.get("status")
            if status != "success":
                err = result.get("error")
                return f"🎤 Не удалось распознать речь: {err or 'ошибка транскрибации'}"

            transcription = (result.get("text") or "").strip()
            if not transcription:
                return "🎤 Получил голосовое сообщение, но не удалось распознать текст. Попробуйте записать снова."

            # Analyze transcription with coordinator
            enhanced_prompt = (
                "Пользователь прислал голосовое сообщение. Транскрипция: '"
                + transcription + "'. Проанализируй запрос и дай ответ."
            )
            analysis = self.process_request(enhanced_prompt)
            return f"🎤 Голосовое сообщение обработано\n\nТранскрипция: \"{transcription}\"\n\n{analysis}"
        except Exception as e:
            return f"🎤 Ошибка обработки голосового сообщения: {e}"
        finally:
            try:
                if temp_audio_path and os.path.exists(temp_audio_path):
                    os.remove(temp_audio_path)
            except Exception:
                pass
    
    def _format_plan_response(self, plan: Dict[str, Any]) -> str:
        """
        Форматирование плана в строгий JSON без текста.
        
        Args:
            plan: JSON план
            
        Returns:
            Отформатированный план как строка
        """
        # Вернуть строгий JSON без дополнительного текста
        return json.dumps(plan, ensure_ascii=False, indent=2)