# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: process_document
# Основной источник: C:\Bldr\integrated_structure_chunking_system.py
# Дубликаты (для справки):
#   - C:\Bldr\scripts\bldr_rag_trainer.py
#   - C:\Bldr\scripts\optimized_bldr_rag_trainer.py
#================================================================================
    def process_document(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        🔧 ПОЛНАЯ ОБРАБОТКА ДОКУМЕНТА
        
        Возвращает структуру, совместимую с фронтендом:
        - document_info: метаданные для UI
        - sections: иерархия разделов
        - chunks: интеллектуальные чанки 
        - tables: таблицы с данными
        - statistics: статистика документа
        """
        
        # 1. Извлекаем структуру документа
        document_structure = self.structure_extractor.extract_complete_structure(content, file_path)
        
        # 2. Создаем интеллектуальные чанки
        smart_chunks = self.intelligent_chunker.create_intelligent_chunks(document_structure)
        
        # 3. Формируем API-совместимую структуру
        api_compatible_result = {
            # Метаданные документа (для UI)
            'document_info': {
                'title': document_structure['metadata']['document_title'],
                'number': document_structure['metadata']['document_number'],
                'type': document_structure['metadata']['document_type'],
                'organization': document_structure['metadata']['organization'],
                'approval_date': document_structure['metadata']['approval_date'],
                'file_name': document_structure['metadata']['file_info']['file_name'],
                'file_size': document_structure['metadata']['file_info']['file_size'],
                'keywords': document_structure['metadata']['keywords']
            },
            
            # Иерархия разделов (для навигации)
            'sections': self._format_sections_for_api(document_structure['sections_hierarchy']),
            
            # Интеллектуальные чанки (для RAG)
            'chunks': [chunk.to_dict() for chunk in smart_chunks],
            
            # Таблицы (для специальной обработки)
            'tables': document_structure['tables'],
            
            # Списки
            'lists': document_structure['lists'],
            
            # Статистика
            'statistics': {
                **document_structure['statistics'],
                'chunks_created': len(smart_chunks),
                'avg_chunk_quality': np.mean([chunk.quality_score for chunk in smart_chunks]) if smart_chunks else 0,
                'chunk_types_distribution': self._get_chunk_types_stats(smart_chunks)
            },
            
            # Техническая информация
            'processing_info': {
                'extracted_at': document_structure['extraction_info']['extracted_at'],
                'processor_version': 'Integrated_v3.0',
                'structure_quality': document_structure['extraction_info']['quality_score'],
                'chunking_quality': np.mean([chunk.quality_score for chunk in smart_chunks]) if smart_chunks else 0,
                'total_elements': len(document_structure['elements']),
                'processing_method': 'intelligent_structure_based'
            }
        }
        
        return api_compatible_result