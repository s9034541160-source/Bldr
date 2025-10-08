# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: get_metrics
# Основной источник: C:\Bldr\core\metrics_collector.py
# Дубликаты (для справки):
#   - C:\Bldr\enterprise_rag_trainer_full.py
#================================================================================
    def get_metrics(self, metric_type: MetricType, 
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None,
                   limit: int = 1000) -> List[Dict[str, Any]]:
        """Получение метрик из базы данных"""
        try:
            table_map = {
                MetricType.SYSTEM: 'system_metrics',
                MetricType.TRAINING: 'training_metrics',
                MetricType.DOCUMENT: 'document_metrics',
                MetricType.ERROR: 'error_metrics'
            }
            
            table_name = table_map.get(metric_type)
            if not table_name:
                return []
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # Для получения словарей
                cursor = conn.cursor()
                
                query = f'SELECT * FROM {table_name}'
                params = []
                
                conditions = []
                if start_time:
                    conditions.append('timestamp >= ?')
                    params.append(start_time)
                    
                if end_time:
                    conditions.append('timestamp <= ?')
                    params.append(end_time)
                
                if conditions:
                    query += ' WHERE ' + ' AND '.join(conditions)
                
                query += ' ORDER BY timestamp DESC LIMIT ?'
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return []