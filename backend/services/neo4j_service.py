"""
Сервис для работы с Neo4j
"""

from neo4j import GraphDatabase
from backend.config.settings import settings
import logging

logger = logging.getLogger(__name__)


class Neo4jService:
    """Сервис для работы с Neo4j"""
    
    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
    
    def close(self):
        """Закрытие соединения"""
        self.driver.close()
    
    def execute_query(self, query: str, parameters: dict = None):
        """Выполнение запроса"""
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return result.data()
    
    def create_node(self, label: str, properties: dict):
        """Создание узла"""
        query = f"CREATE (n:{label} $properties) RETURN n"
        return self.execute_query(query, {"properties": properties})
    
    def create_relationship(self, from_label: str, from_prop: str, from_value: str,
                           to_label: str, to_prop: str, to_value: str,
                           rel_type: str, rel_properties: dict = None):
        """Создание связи между узлами"""
        query = (
            f"MATCH (a:{from_label} {{{from_prop}: $from_value}}), "
            f"(b:{to_label} {{{to_prop}: $to_value}}) "
            f"CREATE (a)-[r:{rel_type} $rel_props]->(b) RETURN r"
        )
        params = {
            "from_value": from_value,
            "to_value": to_value,
            "rel_props": rel_properties or {}
        }
        return self.execute_query(query, params)
    
    def find_node(self, label: str, properties: dict):
        """Поиск узла"""
        props_str = ", ".join([f"{k}: ${k}" for k in properties.keys()])
        query = f"MATCH (n:{label} {{{props_str}}}) RETURN n"
        return self.execute_query(query, properties)
    
    def init_constraints(self):
        """Инициализация ограничений и индексов"""
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
        ]
        
        for constraint in constraints:
            try:
                self.execute_query(constraint)
                logger.info(f"Created constraint: {constraint}")
            except Exception as e:
                logger.warning(f"Constraint may already exist: {e}")


# Глобальный экземпляр сервиса
neo4j_service = Neo4jService()

