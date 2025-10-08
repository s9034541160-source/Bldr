"""
СУПЕР-УМНЫЙ КООРДИНАТОР v2.0
============================
Интеллектуальный координатор, который:
1. ПОНИМАЕТ короткие запросы пользователя
2. ПЛАНИРУЕТ цепочки действий автоматически
3. ВЫПОЛНЯЕТ задачи проактивно
4. ПРЕДЛАГАЕТ следующие шаги
5. ЗАПОМИНАЕТ контекст разговора
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field

from .smart_request_processor import SmartRequestProcessor, RequestContext, create_smart_processor

logger = logging.getLogger(__name__)

@dataclass
class ActionPlan:
    """План действий для выполнения запроса"""
    steps: List[Dict[str, Any]]
    priority: str
    estimated_time: str
    dependencies: List[str]
    expected_outputs: List[str]

@dataclass
class ConversationMemory:
    """Память разговора с пользователем"""
    user_id: str = "default"
    conversation_history: List[Dict] = field(default_factory=list)
    context_summary: str = ""
    last_domain: str = "general"
    ongoing_tasks: List[Dict] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)

class SuperSmartCoordinator:
    """
    СУПЕР-УМНЫЙ КООРДИНАТОР
    Главная фишка - понимает ЛЮБОЙ короткий запрос и делает из него ПОЛНОЦЕННУЮ задачу
    """
    
    def __init__(self, model_manager=None, tools_system=None, rag_system=None):
        self.model_manager = model_manager
        self.tools_system = tools_system
        self.rag_system = rag_system
        
        # Создаем умный процессор запросов
        self.request_processor = create_smart_processor(rag_system=rag_system)
        
        # Память разговоров
        self.conversations: Dict[str, ConversationMemory] = {}
        
        # Шаблоны для создания планов действий
        self.action_templates = {
            'create_document': {
                'checklist': [
                    {"action": "analyze_requirements", "tool": "search_rag_database", "description": "Найти требования к документу"},
                    {"action": "gather_data", "tool": None, "description": "Собрать исходные данные"},
                    {"action": "create_structure", "tool": None, "description": "Создать структуру документа"},
                    {"action": "fill_content", "tool": "gen_docx", "description": "Заполнить содержимое"},
                    {"action": "review_compliance", "tool": "search_rag_database", "description": "Проверить соответствие нормам"}
                ],
                'estimates': [
                    {"action": "identify_work_items", "tool": "search_rag_database", "description": "Определить виды работ"},
                    {"action": "calculate_quantities", "tool": "calc_estimate", "description": "Рассчитать объемы"},
                    {"action": "apply_rates", "tool": "calc_estimate", "description": "Применить расценки ГЭСН/ФЕР"},
                    {"action": "generate_report", "tool": "gen_excel", "description": "Создать смету в Excel"}
                ],
                'safety_plan': [
                    {"action": "identify_hazards", "tool": "search_rag_database", "description": "Выявить опасные факторы"},
                    {"action": "define_measures", "tool": "search_rag_database", "description": "Определить защитные меры"},
                    {"action": "create_instructions", "tool": "gen_docx", "description": "Создать инструкции"}
                ]
            },
            'analyze_document': [
                {"action": "extract_content", "tool": None, "description": "Извлечь содержимое документа"},
                {"action": "identify_requirements", "tool": "search_rag_database", "description": "Найти применимые требования"},
                {"action": "compare_compliance", "tool": None, "description": "Сравнить с нормами"},
                {"action": "generate_report", "tool": "gen_docx", "description": "Создать отчет о проверке"}
            ],
            'calculate': [
                {"action": "identify_parameters", "tool": None, "description": "Определить исходные параметры"},
                {"action": "find_formulas", "tool": "search_rag_database", "description": "Найти расчетные формулы"},
                {"action": "perform_calculation", "tool": "calc_estimate", "description": "Выполнить расчет"},
                {"action": "verify_results", "tool": None, "description": "Проверить результаты"}
            ]
        }
        
    def process_request(self, query: str, user_id: str = "default", context: Dict = None) -> Dict[str, Any]:
        """
        ГЛАВНАЯ ФУНКЦИЯ: Обработка запроса пользователя с полным пониманием и выполнением
        """
        try:
            logger.info(f"🧠 SuperSmartCoordinator обрабатывает: {query}")
            
            # 1. Получаем или создаем память разговора
            if user_id not in self.conversations:
                self.conversations[user_id] = ConversationMemory(user_id=user_id)
            
            memory = self.conversations[user_id]
            
            # 2. Умная обработка запроса
            request_context = self.request_processor.process_request(query, context)
            
            # 3. Обновляем память разговора
            self._update_conversation_memory(memory, query, request_context)
            
            # 4. Создаем умный план действий
            action_plan = self._create_intelligent_action_plan(request_context, memory)
            
            # 5. Выполняем план действий
            execution_results = self._execute_action_plan(action_plan, request_context)
            
            # 6. Генерируем проактивные предложения
            proactive_suggestions = self._generate_contextual_suggestions(
                request_context, memory, execution_results
            )
            
            # 7. Формируем итоговый ответ
            final_response = self._synthesize_response(
                request_context, execution_results, proactive_suggestions
            )
            
            # 8. Сохраняем результат в память
            self._save_to_memory(memory, final_response)
            
            return final_response
            
        except Exception as e:
            logger.error(f"Ошибка в SuperSmartCoordinator: {e}")
            return self._create_error_response(query, str(e))
    
    def _update_conversation_memory(self, memory: ConversationMemory, query: str, context: RequestContext):
        """Обновление памяти разговора"""
        memory.conversation_history.append({
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'intent': context.intent,
            'domain': context.construction_domain,
            'confidence': context.confidence
        })
        
        # Обновляем контекстную информацию
        memory.last_domain = context.construction_domain
        
        # Создаем краткое резюме контекста (последние 5 сообщений)
        recent_queries = [item['query'] for item in memory.conversation_history[-5:]]
        memory.context_summary = f"Недавние темы: {'; '.join(recent_queries)}"
    
    def _create_intelligent_action_plan(self, context: RequestContext, memory: ConversationMemory) -> ActionPlan:
        """Создание умного плана действий"""
        try:
            # Определяем тип документа/задачи для более точного планирования
            doc_types = context.entities.get('document_types', [])
            intent = context.intent
            domain = context.construction_domain
            
            # Выбираем подходящий шаблон
            if intent == 'create_document':
                if 'checklist' in doc_types or 'чек-лист' in context.original_query.lower():
                    template_steps = self.action_templates['create_document']['checklist']
                elif 'estimates' in doc_types or any(word in context.original_query.lower() 
                                                   for word in ['смета', 'расчет', 'стоимость']):
                    template_steps = self.action_templates['create_document']['estimates']
                elif domain == 'safety' or any(word in context.original_query.lower() 
                                              for word in ['безопасность', 'охрана труда']):
                    template_steps = self.action_templates['create_document']['safety_plan']
                else:
                    template_steps = self.action_templates['create_document']['checklist']
            
            elif intent in self.action_templates:
                template_steps = self.action_templates[intent]
            else:
                # Создаем базовый план для неизвестных намерений
                template_steps = [
                    {"action": "understand_request", "tool": "search_rag_database", "description": "Понять суть запроса"},
                    {"action": "find_solution", "tool": "search_rag_database", "description": "Найти решение"},
                    {"action": "provide_answer", "tool": None, "description": "Дать ответ пользователю"}
                ]
            
            # Адаптируем план под конкретный запрос
            adapted_steps = self._adapt_steps_to_context(template_steps, context)
            
            return ActionPlan(
                steps=adapted_steps,
                priority=context.priority,
                estimated_time=self._estimate_execution_time(adapted_steps),
                dependencies=self._identify_dependencies(adapted_steps),
                expected_outputs=self._identify_expected_outputs(context)
            )
            
        except Exception as e:
            logger.error(f"Ошибка создания плана: {e}")
            # Fallback план
            return ActionPlan(
                steps=[{"action": "basic_response", "tool": None, "description": "Базовый ответ"}],
                priority="medium",
                estimated_time="1-2 минуты",
                dependencies=[],
                expected_outputs=["Ответ пользователю"]
            )
    
    def _adapt_steps_to_context(self, template_steps: List[Dict], context: RequestContext) -> List[Dict]:
        """Адаптация шагов плана под конкретный контекст"""
        adapted_steps = []
        
        for step in template_steps:
            adapted_step = step.copy()
            
            # Адаптируем поисковые запросы под домен
            if step.get('tool') == 'search_rag_database':
                adapted_step['search_params'] = {
                    'query': f"{context.original_query} {context.construction_domain}",
                    'doc_types': ['norms', 'technical'],
                    'domain': context.construction_domain
                }
            
            # Адаптируем создание документов
            elif step.get('tool') == 'gen_docx':
                doc_type = context.entities.get('document_types', ['general'])[0]
                adapted_step['doc_params'] = {
                    'template_type': doc_type,
                    'domain': context.construction_domain
                }
            
            adapted_steps.append(adapted_step)
        
        return adapted_steps
    
    def _execute_action_plan(self, plan: ActionPlan, context: RequestContext) -> Dict[str, Any]:
        """Выполнение плана действий"""
        results = {
            'completed_steps': [],
            'outputs': [],
            'errors': [],
            'generated_files': []
        }
        
        try:
            for i, step in enumerate(plan.steps):
                logger.info(f"📋 Выполняем шаг {i+1}/{len(plan.steps)}: {step['description']}")
                
                step_result = self._execute_single_step(step, context, results)
                
                results['completed_steps'].append({
                    'step_number': i + 1,
                    'description': step['description'],
                    'result': step_result,
                    'timestamp': datetime.now().isoformat()
                })
                
                if step_result.get('output'):
                    results['outputs'].append(step_result['output'])
                
                if step_result.get('file'):
                    results['generated_files'].append(step_result['file'])
                
                if step_result.get('error'):
                    results['errors'].append(step_result['error'])
            
            return results
            
        except Exception as e:
            logger.error(f"Ошибка выполнения плана: {e}")
            results['errors'].append(f"Ошибка выполнения: {str(e)}")
            return results
    
    def _execute_single_step(self, step: Dict, context: RequestContext, previous_results: Dict) -> Dict[str, Any]:
        """Выполнение одного шага плана"""
        try:
            tool_name = step.get('tool')
            
            if tool_name == 'search_rag_database':
                return self._execute_rag_search(step, context)
            elif tool_name == 'gen_docx':
                return self._execute_document_generation(step, context, previous_results)
            elif tool_name == 'calc_estimate':
                return self._execute_calculation(step, context)
            else:
                # Логические шаги без инструментов
                return self._execute_logical_step(step, context, previous_results)
                
        except Exception as e:
            logger.error(f"Ошибка выполнения шага {step['description']}: {e}")
            return {'error': str(e), 'success': False}
    
    def _execute_rag_search(self, step: Dict, context: RequestContext) -> Dict[str, Any]:
        """Выполнение поиска в RAG"""
        try:
            if not self.rag_system:
                return {'error': 'RAG система недоступна', 'success': False}
            
            search_params = step.get('search_params', {})
            query = search_params.get('query', context.enriched_query)
            
            results = self.rag_system.search_documents(
                query=query,
                n_results=5,
                doc_types=search_params.get('doc_types', ['norms']),
                min_relevance=0.3
            )
            
            if results:
                # Извлекаем наиболее релевантную информацию
                top_results = results[:3]
                summary = self._summarize_search_results(top_results, context)
                
                return {
                    'success': True,
                    'output': summary,
                    'raw_results': top_results,
                    'results_count': len(results)
                }
            else:
                return {
                    'success': False,
                    'output': 'Релевантной информации не найдено',
                    'results_count': 0
                }
                
        except Exception as e:
            return {'error': f'Ошибка поиска: {str(e)}', 'success': False}
    
    def _execute_document_generation(self, step: Dict, context: RequestContext, previous_results: Dict) -> Dict[str, Any]:
        """Выполнение создания документа"""
        try:
            # Собираем контент из предыдущих шагов
            content_parts = []
            
            # Добавляем заголовок
            doc_title = self._generate_document_title(context)
            content_parts.append(f"# {doc_title}\n\n")
            
            # Добавляем найденную информацию
            for output in previous_results.get('outputs', []):
                if isinstance(output, str) and len(output) > 10:
                    content_parts.append(f"{output}\n\n")
            
            # Добавляем проактивные рекомендации
            content_parts.append("## Рекомендации:\n")
            for suggestion in context.suggested_actions[:3]:
                content_parts.append(f"- {suggestion}\n")
            
            content = "".join(content_parts)
            
            # Генерируем имя файла
            filename = self._generate_filename(context, step)
            
            # Если есть tools_system, используем его
            if self.tools_system:
                try:
                    tool_result = self.tools_system.execute_tool("gen_docx", {
                        "content": content,
                        "filename": filename,
                        "format": "docx"
                    })
                    
                    if tool_result.get('success'):
                        return {
                            'success': True,
                            'output': f"Документ создан: {filename}",
                            'file': filename,
                            'content_preview': content[:300] + "..."
                        }
                except Exception as e:
                    logger.warning(f"Ошибка создания через tools_system: {e}")
            
            # Fallback - возвращаем контент
            return {
                'success': True,
                'output': f"Подготовлен контент для документа: {filename}",
                'content': content,
                'filename': filename
            }
            
        except Exception as e:
            return {'error': f'Ошибка создания документа: {str(e)}', 'success': False}
    
    def _execute_calculation(self, step: Dict, context: RequestContext) -> Dict[str, Any]:
        """Выполнение расчетов"""
        try:
            # Пытаемся извлечь параметры расчета из запроса
            calc_params = self._extract_calculation_params(context)
            
            if self.tools_system and calc_params:
                try:
                    tool_result = self.tools_system.execute_tool("calc_estimate", calc_params)
                    
                    if tool_result.get('success'):
                        return {
                            'success': True,
                            'output': f"Расчет выполнен: {tool_result.get('result', 'Результат получен')}",
                            'calculation_result': tool_result
                        }
                except Exception as e:
                    logger.warning(f"Ошибка расчета через tools_system: {e}")
            
            # Fallback - информируем о необходимых параметрах
            return {
                'success': False,
                'output': f"Для расчета необходимо уточнить параметры: {', '.join(calc_params.keys()) if calc_params else 'объемы, расценки, регион'}",
                'required_params': calc_params or {}
            }
            
        except Exception as e:
            return {'error': f'Ошибка расчета: {str(e)}', 'success': False}
    
    def _execute_logical_step(self, step: Dict, context: RequestContext, previous_results: Dict) -> Dict[str, Any]:
        """Выполнение логического шага БЕЗ инструментов, но С РЕАЛЬНЫМ LLM"""
        action = step.get('action', '')
        
        # ИСПОЛЬЗУЕМ РЕАЛЬНУЮ LLM МОДЕЛЬ для каждого логического шага!
        try:
            if self.model_manager:
                # Формируем prompt для LLM на основе контекста и шага
                llm_prompt = self._create_llm_prompt_for_step(step, context, previous_results)
                
                # ВЫЗЫВАЕМ РЕАЛЬНУЮ LLM МОДЕЛЬ
                llm_response = self.model_manager.query("coordinator", [
                    {"role": "system", "content": "Ты эксперт по строительству. Отвечай конкретно и профессионально на русском языке. Используй знания строительных норм и практик."},
                    {"role": "user", "content": llm_prompt}
                ])
                
                logger.info(f"LLM response for step '{action}': {llm_response[:100]}...")
                
                return {
                    'success': True,
                    'output': llm_response,
                    'used_llm': True
                }
                
            else:
                logger.warning("Model manager not available for logical step")
                
        except Exception as e:
            logger.error(f"LLM execution failed for step {action}: {e}")
            # Fallback к простым ответам только при ошибке
        
        # FALLBACK логика только при отсутствии LLM
        if action == 'understand_request':
            return {
                'success': True,
                'output': f"Запрос понят как: {context.intent} в области {context.construction_domain} с уверенностью {context.confidence:.2f}",
                'used_llm': False
            }
        elif action == 'identify_parameters':
            params = list(context.entities.keys())
            return {
                'success': True,
                'output': f"Выявленные параметры: {', '.join(params) if params else 'требуется уточнение'}",
                'used_llm': False
            }
        elif action == 'basic_response':
            # Для basic_response ОБЯЗАТЕЛЬНО используем LLM
            try:
                if self.model_manager:
                    basic_prompt = f"Пользователь спросил: '{context.original_query}'. Это относится к области '{context.construction_domain}'. Дай профессиональный ответ строителя."
                    
                    llm_response = self.model_manager.query("coordinator", [
                        {"role": "system", "content": "Ты опытный инженер-строитель. Отвечай профессионально, конкретно и по делу на русском языке."},
                        {"role": "user", "content": basic_prompt}
                    ])
                    
                    return {
                        'success': True,
                        'output': llm_response,
                        'used_llm': True
                    }
            except Exception as e:
                logger.error(f"LLM failed for basic response: {e}")
                
            return {
                'success': True,
                'output': f"Обработан запрос: {context.original_query}. Область: {context.construction_domain}.",
                'used_llm': False
            }
        else:
            return {
                'success': True,
                'output': f"Выполнен шаг: {step['description']}",
                'used_llm': False
            }
    
    def _generate_contextual_suggestions(self, context: RequestContext, memory: ConversationMemory, results: Dict) -> List[str]:
        """Генерация контекстных предложений"""
        suggestions = []
        
        # Базовые предложения из контекста
        suggestions.extend(context.suggested_actions[:2])
        
        # Предложения на основе выполненных действий
        if results.get('generated_files'):
            suggestions.append("Проверить созданные документы на соответствие требованиям")
        
        if results.get('errors'):
            suggestions.append("Исправить выявленные ошибки и повторить операцию")
        
        # Предложения на основе домена
        domain = context.construction_domain
        if domain == 'safety':
            suggestions.append("Создать инструктаж для рабочих по выполнению безопасных работ")
        elif domain == 'estimates':
            suggestions.append("Проверить актуальность применяемых расценок")
        elif domain == 'earthworks':
            suggestions.append("Подготовить ППР на производство земляных работ")
        
        # Ограничиваем количество предложений
        return suggestions[:4]
    
    def _synthesize_response(self, context: RequestContext, results: Dict, suggestions: List[str]) -> Dict[str, Any]:
        """Синтез итогового ответа"""
        # Формируем основной ответ
        main_response = self._create_main_response(context, results)
        
        # Добавляем детали выполнения
        execution_summary = self._create_execution_summary(results)
        
        # Формируем проактивные предложения
        next_steps = suggestions if suggestions else ["Задача выполнена"]
        
        return {
            'response': main_response,
            'execution_summary': execution_summary,
            'suggested_next_steps': next_steps,
            'generated_files': results.get('generated_files', []),
            'success': len(results.get('errors', [])) == 0,
            'context': {
                'domain': context.construction_domain,
                'intent': context.intent,
                'confidence': context.confidence
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def _create_main_response(self, context: RequestContext, results: Dict) -> str:
        """Создание основного ответа"""
        outputs = results.get('outputs', [])
        files = results.get('generated_files', [])
        
        response_parts = []
        
        # Начинаем с подтверждения понимания
        response_parts.append(f"✅ **{context.intent.replace('_', ' ').title()}** в области **{context.construction_domain}**\n")
        
        # Добавляем результаты выполнения
        if outputs:
            response_parts.append("📋 **Результаты выполнения:**\n")
            for output in outputs[:3]:  # Не более 3 основных результатов
                if isinstance(output, str) and len(output) > 10:
                    response_parts.append(f"• {output}\n")
        
        # Добавляем информацию о файлах
        if files:
            response_parts.append(f"\n📁 **Создано файлов:** {len(files)}\n")
            for file in files:
                response_parts.append(f"• {file}\n")
        
        return "".join(response_parts)
    
    def _create_execution_summary(self, results: Dict) -> str:
        """Создание краткого резюме выполнения"""
        completed = len(results.get('completed_steps', []))
        errors = len(results.get('errors', []))
        files = len(results.get('generated_files', []))
        
        summary_parts = []
        summary_parts.append(f"Выполнено шагов: {completed}")
        
        if files > 0:
            summary_parts.append(f"Создано файлов: {files}")
        
        if errors > 0:
            summary_parts.append(f"Ошибок: {errors}")
        
        return " | ".join(summary_parts)
    
    # Вспомогательные методы
    def _summarize_search_results(self, results: List[Dict], context: RequestContext) -> str:
        """Создание краткого резюме результатов поиска"""
        if not results:
            return "Релевантной информации не найдено"
        
        summary_parts = []
        for result in results[:2]:
            content = result.get('content', '').strip()
            if content:
                summary_parts.append(content[:200] + "..." if len(content) > 200 else content)
        
        return "\n\n".join(summary_parts)
    
    def _generate_document_title(self, context: RequestContext) -> str:
        """Генерация заголовка документа"""
        domain_titles = {
            'safety': 'План мероприятий по охране труда',
            'earthworks': 'Технологическая карта земляных работ',
            'foundations': 'Проект фундаментов',
            'estimates': 'Смета на строительные работы',
            'quality': 'Программа контроля качества'
        }
        
        domain = context.construction_domain
        if domain in domain_titles:
            return domain_titles[domain]
        
        return f"Документ по запросу: {context.original_query}"
    
    def _generate_filename(self, context: RequestContext, step: Dict) -> str:
        """Генерация имени файла"""
        domain = context.construction_domain
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        
        base_name = f"{domain}_{timestamp}"
        return f"{base_name}.docx"
    
    def _extract_calculation_params(self, context: RequestContext) -> Dict[str, Any]:
        """Извлечение параметров для расчета"""
        params = {}
        
        query = context.original_query.lower()
        
        # Ищем числовые значения
        import re
        numbers = re.findall(r'\d+(?:[.,]\d+)?', query)
        if numbers:
            params['quantity'] = float(numbers[0].replace(',', '.'))
        
        # Определяем регион
        regions = ['москва', 'спб', 'екатеринбург', 'новосибирск']
        for region in regions:
            if region in query:
                params['region'] = region.title()
                break
        else:
            params['region'] = 'Москва'  # По умолчанию
        
        # Ищем коды расценок
        gesn_codes = re.findall(r'гэсн\s*[\d\-\.]+', query)
        if gesn_codes:
            params['rate_code'] = gesn_codes[0].upper()
        
        return params
    
    def _estimate_execution_time(self, steps: List[Dict]) -> str:
        """Оценка времени выполнения"""
        return f"{len(steps)*30} сек - {len(steps)} мин"
    
    def _identify_dependencies(self, steps: List[Dict]) -> List[str]:
        """Выявление зависимостей между шагами"""
        return ["Предыдущие шаги должны быть выполнены"]
    
    def _identify_expected_outputs(self, context: RequestContext) -> List[str]:
        """Определение ожидаемых результатов"""
        outputs = []
        
        if context.intent == 'create_document':
            outputs.append("Созданный документ")
        if context.intent == 'calculate':
            outputs.append("Результат расчета")
        if 'search' in context.intent:
            outputs.append("Найденная информация")
            
        return outputs or ["Ответ на запрос"]
    
    def _save_to_memory(self, memory: ConversationMemory, response: Dict):
        """Сохранение результата в память"""
        memory.conversation_history.append({
            'timestamp': datetime.now().isoformat(),
            'type': 'response',
            'success': response.get('success', False),
            'files_created': len(response.get('generated_files', [])),
            'domain': response.get('context', {}).get('domain', 'unknown')
        })
    
    def _create_llm_prompt_for_step(self, step: Dict, context: RequestContext, previous_results: Dict) -> str:
        """Создание умного промпта для LLM на основе шага и контекста"""
        action = step.get('action', '')
        description = step.get('description', '')
        
        # Собираем контекст из предыдущих шагов
        previous_outputs = []
        for output in previous_results.get('outputs', []):
            if isinstance(output, str) and len(output) > 10:
                previous_outputs.append(output[:200])  # Ограничиваем длину
        
        context_info = ""
        if previous_outputs:
            context_info = f"\n\nКонтекст из предыдущих шагов:\n" + "\n".join(previous_outputs[-2:])  # Последние 2
        
        # Добавляем RAG контекст если есть
        rag_info = ""
        if context.rag_context:
            rag_info = f"\n\nИнформация из базы знаний:\n" + "\n".join(context.rag_context[:2])
        
        # Специальные промпты для разных действий
        action_prompts = {
            'understand_request': f"Пользователь спросил: '{context.original_query}'. Определи, о чём он спрашивает в контексте строительства (область: {context.construction_domain}). Объясни понятным языком, что именно нужно сделать.",
            
            'find_solution': f"Задача: {description}. Пользователь спросил: '{context.original_query}' (область: {context.construction_domain}). Предложи конкретное решение с практическими шагами.",
            
            'provide_answer': f"На основе всей проделанной работы, дай финальный ответ на запрос пользователя: '{context.original_query}'. Ответ должен быть полным, практичным и профессиональным.",
            
            'gather_data': f"Помоги собрать необходимые данные для выполнения задачи: '{context.original_query}'. Область: {context.construction_domain}. Перечисли, какие данные, нормы и параметры нужны.",
            
            'create_structure': f"Создай структуру документа для: '{context.original_query}' (область: {context.construction_domain}). Предложи подробный план/содержание с разделами и пунктами.",
        }
        
        # Выбираем специальный промпт или создаём общий
        if action in action_prompts:
            prompt = action_prompts[action]
        else:
            prompt = f"Выполни задачу: '{description}' для запроса пользователя: '{context.original_query}' (область: {context.construction_domain}). Ответь профессионально и конкретно."
        
        # Добавляем контекст
        full_prompt = prompt + context_info + rag_info
        
        return full_prompt
    
    def _create_error_response(self, query: str, error: str) -> Dict[str, Any]:
        """Создание ответа об ошибке"""
        return {
            'response': f"❌ Произошла ошибка при обработке запроса: {query}",
            'error': error,
            'success': False,
            'suggested_next_steps': [
                "Попробуйте переформулировать запрос",
                "Уточните детали задачи",
                "Обратитесь к системному администратору"
            ],
            'timestamp': datetime.now().isoformat()
        }

# Функция для создания координатора
def create_super_smart_coordinator(model_manager=None, tools_system=None, rag_system=None):
    """Создание супер-умного координатора"""
    return SuperSmartCoordinator(
        model_manager=model_manager,
        tools_system=tools_system,
        rag_system=rag_system
    )