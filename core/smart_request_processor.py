"""
СУПЕР-УМНАЯ СИСТЕМА ПОНИМАНИЯ ЗАПРОСОВ
=====================================
Интеллектуальная система, которая делает короткие запросы пользователя ПОНЯТНЫМИ для AI
"""

import re
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class RequestContext:
    """Контекст запроса пользователя"""
    original_query: str
    enriched_query: str
    intent: str
    confidence: float
    entities: Dict[str, Any]
    construction_domain: str
    suggested_actions: List[str]
    rag_context: List[str]
    priority: str  # high, medium, low

class SmartRequestProcessor:
    """
    СУПЕР-УМНЫЙ процессор запросов, который:
    1. Понимает намерения пользователя из коротких фраз
    2. Автоматически обогащает запросы контекстом из RAG
    3. Предлагает логические цепочки действий
    4. Проактивно расширяет задачи
    """
    
    def __init__(self, rag_system=None, sbert_model=None):
        self.rag_system = rag_system
        self.sbert_model = sbert_model
        
        # Словари для понимания строительной терминологии
        self.construction_patterns = {
            'earthworks': [
                'земляные работы', 'котлован', 'траншея', 'планировка', 
                'засыпка', 'разработка грунта', 'земляные', 'грунт'
            ],
            'foundations': [
                'фундамент', 'основание', 'свая', 'столбчатый', 'ленточный',
                'плитный', 'монолитный', 'сборный'
            ],
            'concrete': [
                'бетон', 'железобетон', 'арматура', 'опалубка', 'заливка',
                'твердение', 'прочность', 'марка бетона'
            ],
            'safety': [
                'охрана труда', 'безопасность', 'СИЗ', 'техника безопасности',
                'нарушения', 'травматизм', 'инструктаж'
            ],
            'quality': [
                'качество', 'контроль', 'дефекты', 'испытания', 'приемка',
                'ГОСТ', 'СП', 'СНиП', 'проверка'
            ],
            'documents': [
                'документы', 'проект', 'чертеж', 'схема', 'план', 'смета',
                'КР', 'АР', 'ПОС', 'ППР', 'технологическая карта'
            ],
            'estimates': [
                'смета', 'расчет', 'стоимость', 'цена', 'ГЭСН', 'ФЕР',
                'материалы', 'затраты', 'калькуляция'
            ]
        }
        
        # Шаблоны для распознавания намерений
        self.intent_patterns = {
            'create_document': [
                'сделай', 'создай', 'составь', 'разработай', 'подготовь',
                'напиши', 'сформируй', 'оформи'
            ],
            'analyze_document': [
                'проанализируй', 'проверь', 'изучи', 'рассмотри', 
                'найди ошибки', 'оцени'
            ],
            'search_information': [
                'найди', 'ищи', 'покажи', 'что говорит', 'какие требования',
                'нормы', 'по СП', 'согласно'
            ],
            'calculate': [
                'посчитай', 'рассчитай', 'вычисли', 'определи объем',
                'сколько нужно', 'расход'
            ],
            'check_compliance': [
                'соответствует ли', 'проверь на соответствие', 'по нормам',
                'требования', 'нарушения'
            ]
        }
        
        # Проактивные предложения
        self.proactive_suggestions = {
            'earthworks': [
                "Проверить требования СП по безопасности земляных работ",
                "Рассчитать объемы грунта и стоимость работ",
                "Подготовить ППР на земляные работы",
                "Проверить наличие разрешений на земляные работы"
            ],
            'foundations': [
                "Проверить соответствие проекта фундамента геологии участка",
                "Рассчитать арматуру и бетон для фундамента", 
                "Подготовить технологические карты на фундаментные работы",
                "Проверить требования по гидроизоляции фундамента"
            ],
            'safety': [
                "Составить инструкции по охране труда",
                "Подготовить чек-лист проверки СИЗ",
                "Создать план мероприятий по предупреждению травматизма",
                "Проверить соответствие требованиям SanPiN"
            ]
        }
        
    def process_request(self, query: str, context: Dict = None) -> RequestContext:
        """
        ОСНОВНАЯ ФУНКЦИЯ: Обработка и обогащение запроса пользователя
        """
        try:
            logger.info(f"Обрабатываем запрос: {query}")
            
            # 1. Очистка и нормализация запроса
            normalized_query = self._normalize_query(query)
            
            # 2. Определение намерения пользователя
            intent, confidence = self._detect_intent(normalized_query)
            
            # 3. Извлечение сущностей (что именно нужно)
            entities = self._extract_entities(normalized_query)
            
            # 4. Определение строительной области
            domain = self._detect_construction_domain(normalized_query)
            
            # 5. Обогащение запроса контекстом из RAG
            enriched_query, rag_context = self._enrich_with_rag_context(
                normalized_query, domain, intent
            )
            
            # 6. Генерация проактивных предложений
            suggested_actions = self._generate_proactive_suggestions(
                domain, intent, entities
            )
            
            # 7. Определение приоритета
            priority = self._determine_priority(intent, entities)
            
            return RequestContext(
                original_query=query,
                enriched_query=enriched_query,
                intent=intent,
                confidence=confidence,
                entities=entities,
                construction_domain=domain,
                suggested_actions=suggested_actions,
                rag_context=rag_context,
                priority=priority
            )
            
        except Exception as e:
            logger.error(f"Ошибка обработки запроса: {e}")
            # Fallback - базовый контекст
            return RequestContext(
                original_query=query,
                enriched_query=f"Обработать запрос: {query}",
                intent="unknown",
                confidence=0.1,
                entities={},
                construction_domain="general",
                suggested_actions=["Уточнить запрос"],
                rag_context=[],
                priority="medium"
            )
    
    def _normalize_query(self, query: str) -> str:
        """Очистка и нормализация запроса"""
        # Убираем лишние символы, приводим к нижнему регистру
        normalized = re.sub(r'[^\w\s\-]', '', query.lower())
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized
    
    def _detect_intent(self, query: str) -> Tuple[str, float]:
        """Определение намерения пользователя"""
        best_intent = "general_query"
        max_confidence = 0.0
        
        for intent, patterns in self.intent_patterns.items():
            confidence = 0.0
            for pattern in patterns:
                if pattern in query:
                    confidence += 0.8
            
            # Нормализуем по количеству паттернов
            confidence = confidence / len(patterns) if patterns else 0.0
            
            if confidence > max_confidence:
                max_confidence = confidence
                best_intent = intent
        
        # Если ничего не найдено, пытаемся определить по ключевым словам
        if max_confidence < 0.3:
            if any(word in query for word in ['что', 'как', 'где', 'когда', 'почему']):
                return "search_information", 0.6
            elif any(word in query for word in ['проблема', 'ошибка', 'не работает']):
                return "troubleshoot", 0.7
        
        return best_intent, max_confidence
    
    def _extract_entities(self, query: str) -> Dict[str, Any]:
        """Извлечение сущностей из запроса"""
        entities = {
            'document_types': [],
            'construction_elements': [],
            'materials': [],
            'regulations': [],
            'actions': []
        }
        
        # Типы документов
        doc_patterns = {
            'смета': 'estimates',
            'проект': 'project',
            'чек-лист': 'checklist',
            'инструкция': 'instruction',
            'план': 'plan',
            'отчет': 'report',
            'карта': 'technological_card'
        }
        
        for pattern, doc_type in doc_patterns.items():
            if pattern in query:
                entities['document_types'].append(doc_type)
        
        # СП, ГОСТ, СНиП
        regulations = re.findall(r'сп\s*\d+', query)
        entities['regulations'].extend(regulations)
        
        return entities
    
    def _detect_construction_domain(self, query: str) -> str:
        """Определение строительной области"""
        domain_scores = {}
        
        for domain, keywords in self.construction_patterns.items():
            score = sum(1 for keyword in keywords if keyword in query)
            if score > 0:
                domain_scores[domain] = score
        
        if domain_scores:
            return max(domain_scores, key=domain_scores.get)
        
        return 'general'
    
    def _enrich_with_rag_context(self, query: str, domain: str, intent: str) -> Tuple[str, List[str]]:
        """Обогащение запроса контекстом из RAG"""
        enriched_parts = [query]
        rag_context = []
        
        try:
            if self.rag_system:
                # Формируем поисковые запросы на основе домена
                search_queries = []
                
                if domain in self.construction_patterns:
                    # Добавляем ключевые слова домена
                    domain_keywords = ' '.join(self.construction_patterns[domain][:3])
                    search_queries.append(f"{query} {domain_keywords}")
                
                # Добавляем запросы по намерению
                if intent == 'create_document':
                    search_queries.append(f"требования оформление {query}")
                elif intent == 'check_compliance':
                    search_queries.append(f"нормы стандарты {query}")
                
                # Выполняем поиск
                for search_query in search_queries:
                    try:
                        results = self.rag_system.search_documents(
                            search_query, 
                            n_results=3,
                            doc_types=['norms', 'technical']
                        )
                        
                        if results:
                            for result in results[:2]:  # Берем топ-2
                                if result.get('content'):
                                    rag_context.append(result['content'][:200])
                    
                    except Exception as e:
                        logger.warning(f"RAG поиск не удался: {e}")
            
            # Формируем обогащенный запрос
            if rag_context:
                context_summary = " Учесть: " + "; ".join(rag_context)
                enriched_query = query + context_summary
            else:
                enriched_query = self._add_domain_context(query, domain, intent)
            
            return enriched_query, rag_context
            
        except Exception as e:
            logger.error(f"Ошибка обогащения RAG: {e}")
            return self._add_domain_context(query, domain, intent), []
    
    def _add_domain_context(self, query: str, domain: str, intent: str) -> str:
        """Добавление контекста домена без RAG"""
        context_additions = {
            'earthworks': "Учесть требования СП 48.13330 по технике безопасности и СП 22.13330 по основаниям зданий.",
            'foundations': "Учесть требования СП 22.13330 основания зданий, СП 52.13330 железобетонные конструкции.",
            'safety': "Учесть требования SanPiN, правила охраны труда в строительстве.",
            'quality': "Учесть требования ГОСТ и СП по контролю качества строительных работ.",
            'estimates': "Учесть актуальные расценки ГЭСН, ФЕР, территориальные коэффициенты."
        }
        
        if domain in context_additions:
            return f"{query} {context_additions[domain]}"
        
        return query
    
    def _generate_proactive_suggestions(self, domain: str, intent: str, entities: Dict) -> List[str]:
        """Генерация проактивных предложений"""
        suggestions = []
        
        # Базовые предложения по домену
        if domain in self.proactive_suggestions:
            suggestions.extend(self.proactive_suggestions[domain][:2])
        
        # Предложения по намерению
        intent_suggestions = {
            'create_document': [
                "Проверить актуальность нормативных требований",
                "Подготовить необходимые исходные данные"
            ],
            'analyze_document': [
                "Сравнить с требованиями действующих норм",
                "Проверить расчетные значения"
            ],
            'calculate': [
                "Проверить единицы измерения",
                "Учесть коэффициенты запаса"
            ]
        }
        
        if intent in intent_suggestions:
            suggestions.extend(intent_suggestions[intent])
        
        return suggestions[:4]  # Не более 4 предложений
    
    def _determine_priority(self, intent: str, entities: Dict) -> str:
        """Определение приоритета задачи"""
        high_priority_intents = ['check_compliance', 'analyze_document']
        high_priority_keywords = ['безопасность', 'авария', 'нарушение', 'срочно']
        
        if intent in high_priority_intents:
            return 'high'
        
        # Проверяем на ключевые слова высокого приоритета в entities
        if any(keyword in str(entities).lower() for keyword in high_priority_keywords):
            return 'high'
        
        if intent in ['create_document', 'calculate']:
            return 'medium'
        
        return 'low'

# Функции для интеграции с основной системой
def create_smart_processor(rag_system=None, sbert_model=None):
    """Создание умного процессора запросов"""
    return SmartRequestProcessor(rag_system, sbert_model)

def process_user_query(query: str, processor: SmartRequestProcessor) -> RequestContext:
    """Обработка пользовательского запроса"""
    return processor.process_request(query)