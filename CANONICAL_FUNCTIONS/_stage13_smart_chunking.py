# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _stage13_smart_chunking
# Основной источник: C:\Bldr\enterprise_rag_trainer_full.py
# Дубликаты (для справки):
#   - C:\Bldr\scripts\bldr_rag_trainer.py
#   - C:\Bldr\scripts\optimized_bldr_rag_trainer.py
#================================================================================
    def _stage13_smart_chunking(self, content: str, structural_data: Dict, 
                               metadata: DocumentMetadata, doc_type_info: Dict) -> List[DocumentChunk]:
        """STAGE 13: Smart Chunking (1 пункт = 1 чанк)"""
        
        logger.info(f"[Stage 13/14] SMART CHUNKING - 1 section = 1 chunk")
        start_time = time.time()
        
        chunks = []
        
        # Создаем чанки из секций
        for i, section in enumerate(structural_data.get('sections', [])):
            if not section.get('content') or len(section['content'].strip()) < 20:
                continue
            
            chunk_metadata = {
                'section_id': f"section_{i}",
                'section_title': section.get('title', f'Секция {i+1}'),
                'section_level': section.get('level', 1),
                'doc_type': doc_type_info['doc_type'],
                'doc_subtype': doc_type_info['doc_subtype'],
                'confidence': doc_type_info['confidence'],
                'start_line': section.get('start_line', 0),
                'end_line': section.get('end_line', 0)
            }
            
            if metadata.materials:
                chunk_metadata['materials'] = metadata.materials[:5]
            if metadata.dates:
                chunk_metadata['dates'] = metadata.dates[:3]
            
            chunk = DocumentChunk(
                content=section['content'].strip(),
                metadata=chunk_metadata,
                section_id=f"section_{i}",
                chunk_type="section"
            )
            
            chunks.append(chunk)
        
        # Чанки из таблиц
        for i, table in enumerate(structural_data.get('tables', [])):
            if not table.get('content') or len(table['content'].strip()) < 10:
                continue
            
            table_metadata = {
                'table_id': f"table_{i}",
                'table_title': table.get('title', f'Таблица {i+1}'),
                'doc_type': doc_type_info['doc_type'],
                'chunk_type': 'table'
            }
            
            if metadata.finances:
                table_metadata['finances'] = metadata.finances
            
            chunk = DocumentChunk(
                content=table['content'].strip(),
                metadata=table_metadata,
                section_id=f"table_{i}",
                chunk_type="table"
            )
            
            chunks.append(chunk)
        
        # Fallback чанки если секций мало
        if len(chunks) < 3:
            additional_chunks = self._create_fallback_chunks(content, doc_type_info, metadata)
            chunks.extend(additional_chunks)
        
        # Генерируем эмбеддинги
        chunks_with_embeddings = self._generate_chunk_embeddings(chunks)
        
        elapsed = time.time() - start_time
        logger.info(f"[Stage 13/14] COMPLETE - Created {len(chunks_with_embeddings)} chunks ({elapsed:.2f}s)")
        
        return chunks_with_embeddings