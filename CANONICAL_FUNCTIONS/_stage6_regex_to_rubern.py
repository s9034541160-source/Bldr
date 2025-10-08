# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _stage6_regex_to_rubern
# Основной источник: C:\Bldr\scripts\bldr_rag_trainer.py
# Дубликаты (для справки):
#   - C:\Bldr\scripts\optimized_bldr_rag_trainer.py
#================================================================================
    def _stage6_regex_to_rubern(self, content: str, doc_type: str, structural_data: Dict[str, Any]) -> List[str]:
        """
        Stage 6: Extract work candidates (seed works) using regex based on document type and structure
        """
        sections = structural_data.get('sections', [])
        
        # Use the regex patterns function to extract seed works
        seed_works = extract_works_candidates(content, doc_type, sections)
        
        log = f'Seeds generated: {len(seed_works)} candidates extracted'
        print(f'✅ [Stage 6/14] Extract work candidates: {log}')
        
        return seed_works