# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _stage4_document_type_detection
# Основной источник: C:\Bldr\enterprise_rag_trainer_full.py
# Дубликаты (для справки):
#   - C:\Bldr\scripts\bldr_rag_trainer.py
#   - C:\Bldr\scripts\optimized_bldr_rag_trainer.py
#================================================================================
    def _stage4_document_type_detection(self, content: str, file_path: str) -> Dict[str, Any]:
        """STAGE 4: Document Type Detection (симбиотический: regex + SBERT)"""
        
        logger.info(f"[Stage 4/14] DOCUMENT TYPE DETECTION: {Path(file_path).name}")
        start_time = time.time()
        
        # Regex анализ
        regex_result = self._regex_type_detection(content, file_path)
        
        # SBERT анализ
        sbert_result = self._sbert_type_detection(content)
        
        # Комбинируем результаты
        final_result = self._combine_type_detection(regex_result, sbert_result)
        
        elapsed = time.time() - start_time
        logger.info(f"[Stage 4/14] COMPLETE - Type: {final_result['doc_type']}, "
                   f"Subtype: {final_result['doc_subtype']}, "
                   f"Confidence: {final_result['confidence']:.2f} ({elapsed:.2f}s)")
        
        return final_result