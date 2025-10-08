# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _stage8_metadata_extraction
# Основной источник: C:\Bldr\enterprise_rag_trainer_full.py
# Дубликаты (для справки):
#   - C:\Bldr\scripts\bldr_rag_trainer.py
#   - C:\Bldr\scripts\optimized_bldr_rag_trainer.py
#================================================================================
    def _stage8_metadata_extraction(self, content: str, structural_data: Dict, 
                                    doc_type_info: Dict) -> DocumentMetadata:
        """STAGE 8: Metadata Extraction (ТОЛЬКО из структуры Stage 5)"""
        
        logger.info(f"[Stage 8/14] METADATA EXTRACTION - Type: {doc_type_info['doc_type']}")
        start_time = time.time()
        
        metadata = DocumentMetadata()
        
        if 'sections' in structural_data:
            metadata = self._extract_from_sections(structural_data['sections'], metadata)
        
        if 'tables' in structural_data:
            metadata = self._extract_from_tables(structural_data['tables'], metadata)
        
        if doc_type_info['doc_type'] == 'norms' and 'norm_elements' in structural_data:
            metadata = self._extract_norms_metadata(structural_data['norm_elements'], metadata)
        elif doc_type_info['doc_type'] == 'smeta' and 'smeta_items' in structural_data:
            metadata = self._extract_smeta_metadata(structural_data['smeta_items'], metadata)
        elif doc_type_info['doc_type'] == 'ppr' and 'ppr_stages' in structural_data:
            metadata = self._extract_ppr_metadata(structural_data['ppr_stages'], metadata)
        
        metadata.quality_score = self._calculate_metadata_quality(metadata)
        
        elapsed = time.time() - start_time
        logger.info(f"[Stage 8/14] COMPLETE - Materials: {len(metadata.materials)}, "
                   f"Finances: {len(metadata.finances)}, Dates: {len(metadata.dates)}, "
                   f"Quality: {metadata.quality_score:.2f} ({elapsed:.2f}s)")
        
        return metadata