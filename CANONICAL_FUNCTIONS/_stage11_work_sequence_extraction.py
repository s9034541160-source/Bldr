# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _stage11_work_sequence_extraction
# Основной источник: C:\Bldr\enterprise_rag_trainer_full.py
# Дубликаты (для справки):
#   - C:\Bldr\scripts\bldr_rag_trainer.py
#   - C:\Bldr\scripts\optimized_bldr_rag_trainer.py
#================================================================================
    def _stage11_work_sequence_extraction(self, sbert_data: Dict, doc_type_info: Dict, 
                                         metadata: DocumentMetadata) -> List[WorkSequence]:
        """STAGE 11: Work Sequence Extraction"""
        
        logger.info(f"[Stage 11/14] WORK SEQUENCE EXTRACTION")
        start_time = time.time()
        
        work_sequences = []
        works = sbert_data.get('works', [])
        dependencies = sbert_data.get('dependencies', [])
        
        for work in works:
            work_deps = []
            for dep in dependencies:
                if dep['to'] == work['id']:
                    work_deps.append(dep['from'])
            
            priority = self._calculate_work_priority(work, work_deps, doc_type_info)
            duration = self._estimate_work_duration(work['name'])
            section = work.get('section', 'general')
            
            sequence = WorkSequence(
                name=work['name'],
                deps=work_deps,
                duration=duration,
                priority=priority,
                quality_score=work['confidence'],
                doc_type=doc_type_info['doc_type'],
                section=section
            )
            
            work_sequences.append(sequence)
        
        work_sequences.sort(key=lambda x: x.priority, reverse=True)
        
        elapsed = time.time() - start_time
        logger.info(f"[Stage 11/14] COMPLETE - Created {len(work_sequences)} work sequences ({elapsed:.2f}s)")
        
        return work_sequences