# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _log_to_neo4j
# Основной источник: C:\Bldr\core\norms_processor.py
# Дубликаты (для справки):
#   - C:\Bldr\core\celery_norms.py
#================================================================================
    def _log_to_neo4j(self, data: Dict[str, Any]):
        """
        Log processing actions to Neo4j
        
        Args:
            data: Log data
        """
        if not self.driver:
            return
        
        try:
            with self.driver.session() as session:
                session.run(
                    """
                    CREATE (l:UpdateLog {
                        timestamp: datetime(),
                        action: $action,
                        data: $data
                    })
                    """,
                    action=data.get('action', 'unknown'),
                    data=json.dumps(data, ensure_ascii=False)
                )
        except Exception as e:
            logger.error(f"Error logging to Neo4j: {e}")