# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _stage3_text_extraction
# Основной источник: C:\Bldr\enterprise_rag_trainer_full.py
# Дубликаты (для справки):
#   - C:\Bldr\scripts\bldr_rag_trainer.py
#   - C:\Bldr\scripts\optimized_bldr_rag_trainer.py
#================================================================================
    def _stage3_text_extraction(self, file_path: str) -> str:
        """STAGE 3: Text Extraction - ПОЛНАЯ РЕАЛИЗАЦИЯ"""
        
        logger.info(f"[Stage 3/14] TEXT EXTRACTION: {Path(file_path).name}")
        start_time = time.time()
        
        content = ""
        file_ext = Path(file_path).suffix.lower()
        
        try:
            if file_ext == '.pdf':
                content = self._extract_from_pdf_enterprise(file_path)
            elif file_ext in ['.docx', '.doc']:
                content = self._extract_from_docx_enterprise(file_path)
            elif file_ext in ['.txt', '.rtf']:
                content = self._extract_from_txt_enterprise(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                content = self._extract_from_excel_enterprise(file_path)
            else:
                logger.warning(f"Unsupported file format: {file_ext}")
                
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
        
        if content:
            content = self._clean_text(content)
        
        elapsed = time.time() - start_time
        char_count = len(content)
        
        if char_count > 50:
            logger.info(f"[Stage 3/14] COMPLETE - Extracted {char_count} characters ({elapsed:.2f}s)")
        else:
            logger.warning(f"[Stage 3/14] FAILED - Only {char_count} characters extracted ({elapsed:.2f}s)")
        
        return content