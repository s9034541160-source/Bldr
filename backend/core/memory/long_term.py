"""
Долгосрочная память для агентов (Neo4j)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from backend.services.neo4j_service import neo4j_service
import logging

logger = logging.getLogger(__name__)


class LongTermMemory:
    """Долгосрочная память для хранения важных фактов в Neo4j"""
    
    def __init__(self, user_id: Optional[str] = None):
        """
        Args:
            user_id: ID пользователя (опционально)
        """
        self.user_id = user_id
    
    def store_fact(
        self,
        fact_type: str,
        subject: str,
        predicate: str,
        object_value: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Сохранение факта в долгосрочную память
        
        Args:
            fact_type: Тип факта (например, "project_info", "user_preference")
            subject: Субъект (например, "Project_123")
            predicate: Предикат (например, "has_status")
            object_value: Объект (например, "in_progress")
            metadata: Дополнительные метаданные
        """
        try:
            # Создание узла субъекта
            subject_node = f"{fact_type}_{subject}"
            neo4j_service.create_node(
                label=fact_type,
                properties={
                    "id": subject,
                    "name": subject,
                    **(metadata or {})
                }
            )
            
            # Создание узла объекта если нужно
            object_node = f"{predicate}_{object_value}"
            
            # Создание связи
            neo4j_service.create_relationship(
                from_label=fact_type,
                from_prop="id",
                from_value=subject,
                to_label="Fact",
                to_prop="value",
                to_value=object_value,
                rel_type=predicate.upper(),
                rel_properties={
                    "created_at": datetime.utcnow().isoformat(),
                    "user_id": self.user_id
                } if self.user_id else {
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Stored fact: {subject} {predicate} {object_value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store fact: {e}")
            return False
    
    def retrieve_facts(
        self,
        fact_type: Optional[str] = None,
        subject: Optional[str] = None,
        predicate: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Поиск фактов в долгосрочной памяти
        
        Args:
            fact_type: Тип факта для фильтрации
            subject: Субъект для фильтрации
            predicate: Предикат для фильтрации
            
        Returns:
            Список найденных фактов
        """
        try:
            query_parts = []
            
            if fact_type and subject:
                query = f"""
                MATCH (s:{fact_type} {{id: $subject}})-[r]->(o)
                RETURN s, r, o
                """
                results = neo4j_service.execute_query(query, {"subject": subject})
            elif fact_type:
                query = f"""
                MATCH (s:{fact_type})-[r]->(o)
                RETURN s, r, o
                LIMIT 100
                """
                results = neo4j_service.execute_query(query)
            else:
                query = """
                MATCH (s)-[r]->(o)
                RETURN s, r, o
                LIMIT 100
                """
                results = neo4j_service.execute_query(query)
            
            facts = []
            for result in results:
                facts.append({
                    "subject": result.get("s", {}),
                    "predicate": result.get("r", {}).get("type", ""),
                    "object": result.get("o", {})
                })
            
            return facts
            
        except Exception as e:
            logger.error(f"Failed to retrieve facts: {e}")
            return []
    
    def extract_knowledge_from_dialogue(
        self,
        dialogue_history: List[Dict[str, Any]],
        user_id: Optional[str] = None
    ) -> int:
        """
        Извлечение знаний из диалога и сохранение в долгосрочную память
        
        Args:
            dialogue_history: История диалога
            user_id: ID пользователя
            
        Returns:
            Количество извлеченных фактов
        """
        # TODO: Использовать LLM для извлечения фактов из диалога
        # Пока простая реализация - сохранение ключевых моментов
        
        facts_count = 0
        
        for message in dialogue_history:
            content = message.get("content", "")
            role = message.get("role", "")
            
            # Простое извлечение: ищем упоминания проектов, статусов и т.д.
            # В будущем можно использовать LLM для более умного извлечения
            
            if "проект" in content.lower() or "project" in content.lower():
                # Попытка извлечь информацию о проекте
                # Это упрощенная версия, в реальности нужен NLP
                pass
        
        return facts_count
    
    def search_memory(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Поиск в долгосрочной памяти
        
        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов
        """
        try:
            # Простой поиск по метаданным узлов
            # В будущем можно использовать полнотекстовый поиск Neo4j
            query_cypher = """
            MATCH (n)
            WHERE n.name CONTAINS $query OR n.id CONTAINS $query
            RETURN n
            LIMIT $limit
            """
            
            results = neo4j_service.execute_query(
                query_cypher,
                {"query": query, "limit": limit}
            )
            
            return [r.get("n", {}) for r in results]
            
        except Exception as e:
            logger.error(f"Failed to search memory: {e}")
            return []

