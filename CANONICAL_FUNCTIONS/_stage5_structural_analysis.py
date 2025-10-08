# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _stage5_structural_analysis
# Основной источник: C:\Bldr\enterprise_rag_trainer_full.py
# Дубликаты (для справки):
#   - C:\Bldr\scripts\bldr_rag_trainer.py
#   - C:\Bldr\scripts\optimized_bldr_rag_trainer.py
#================================================================================
    def _stage5_structural_analysis(self, content: str, doc_type_info: Dict) -> Dict[str, Any]:
        """STAGE 5: SBERT-based Structural Analysis (семантическая структура)"""
        
        logger.info(f"[Stage 5/14] SBERT STRUCTURAL ANALYSIS - Type: {doc_type_info['doc_type']}")
        start_time = time.time()
        
        if not self.sbert_model or not HAS_ML_LIBS:
            logger.warning("SBERT not available, using fallback chunker")
            return self._structural_analysis_fallback(content)
        
        try:
            # SBERT семантическое разбиение на секции
            semantic_sections = self._sbert_section_detection(content, doc_type_info)
            
            # Семантическое обнаружение таблиц
            semantic_tables = self._sbert_table_detection(content)
            
            # Построение иерархической структуры через SBERT
            hierarchical_structure = self._sbert_hierarchy_analysis(semantic_sections, content)
            
            structural_data = {
                'sections': semantic_sections,
                'paragraphs_count': sum(len(s['content'].split('\n')) for s in semantic_sections),
                'tables': semantic_tables,
                'hierarchy': hierarchical_structure,
                'structural_completeness': self._calculate_structural_completeness(semantic_sections),
                'analysis_method': 'sbert_semantic'
            }
            
            # Дополнительная обработка в зависимости от типа документа
            if doc_type_info['doc_type'] == 'norms':
                structural_data = self._enhance_norms_structure(structural_data, content)
            elif doc_type_info['doc_type'] == 'ppr':
                structural_data = self._enhance_ppr_structure(structural_data, content)
            elif doc_type_info['doc_type'] == 'smeta':
                structural_data = self._enhance_smeta_structure(structural_data, content)
            
        except Exception as e:
            logger.error(f"SBERT structural analysis failed: {e}")
            structural_data = self._structural_analysis_fallback(content)
        
        elapsed = time.time() - start_time
        
        sections_count = len(structural_data.get('sections', []))
        paragraphs_count = structural_data.get('paragraphs_count', 0)
        tables_count = len(structural_data.get('tables', []))
        
        logger.info(f"[Stage 5/14] COMPLETE - Sections: {sections_count}, "
                   f"Paragraphs: {paragraphs_count}, Tables: {tables_count} ({elapsed:.2f}s)")
        
        return structural_data