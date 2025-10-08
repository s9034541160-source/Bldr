# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _stage10_type_specific_processing
# Основной источник: C:\Bldr\enterprise_rag_trainer_full.py
# Дубликаты (для справки):
#   - C:\Bldr\scripts\bldr_rag_trainer.py
#   - C:\Bldr\scripts\optimized_bldr_rag_trainer.py
#================================================================================
    def _stage10_type_specific_processing(self, content: str, doc_type_info: Dict,
                                         structural_data: Dict, sbert_data: Dict) -> Dict[str, Any]:
        """STAGE 10: Type-specific Processing"""
        
        logger.info(f"[Stage 10/14] TYPE-SPECIFIC PROCESSING - Type: {doc_type_info['doc_type']}")
        start_time = time.time()
        
        doc_type = doc_type_info['doc_type']
        result = {}
        
        if doc_type == 'norms':
            result = self._process_norms_specific(content, structural_data, sbert_data)
        elif doc_type == 'ppr':
            result = self._process_ppr_specific(content, structural_data, sbert_data)
        elif doc_type == 'smeta':
            result = self._process_smeta_specific(content, structural_data, sbert_data)
        else:
            result = self._process_generic_specific(content, structural_data, sbert_data)
        
        elapsed = time.time() - start_time
        processed_items = len(result.get('processed_items', []))
        
        logger.info(f"[Stage 10/14] COMPLETE - Processed {processed_items} type-specific items ({elapsed:.2f}s)")
        
        return result