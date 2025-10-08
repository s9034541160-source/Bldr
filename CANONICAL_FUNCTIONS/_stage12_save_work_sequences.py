# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _stage12_save_work_sequences
# Основной источник: C:\Bldr\enterprise_rag_trainer_full.py
# Дубликаты (для справки):
#   - C:\Bldr\scripts\bldr_rag_trainer.py
#   - C:\Bldr\scripts\optimized_bldr_rag_trainer.py
#================================================================================
    def _stage12_save_work_sequences(self, work_sequences: List[WorkSequence], file_path: str) -> int:
        """STAGE 12: Save Work Sequences (Neo4j + JSON)"""
        
        logger.info(f"[Stage 12/14] SAVE WORK SEQUENCES")
        start_time = time.time()
        
        saved_count = 0
        
        # Сохранение в JSON
        sequences_file = self.cache_dir / f"sequences_{Path(file_path).stem}.json"
        try:
            sequences_data = []
            for seq in work_sequences:
                sequences_data.append({
                    'name': seq.name,
                    'deps': seq.deps,
                    'duration': seq.duration,
                    'priority': seq.priority,
                    'quality_score': seq.quality_score,
                    'doc_type': seq.doc_type,
                    'section': seq.section
                })
            
            with open(sequences_file, 'w', encoding='utf-8') as f:
                json.dump(sequences_data, f, ensure_ascii=False, indent=2)
            
            saved_count = len(sequences_data)
            logger.info(f"Saved {saved_count} sequences to JSON: {sequences_file}")
            
        except Exception as e:
            logger.error(f"Failed to save sequences to JSON: {e}")
        
        # Сохранение в Neo4j
        if self.neo4j:
            try:
                neo4j_saved = self._save_sequences_to_neo4j(work_sequences, file_path)
                logger.info(f"Saved {neo4j_saved} sequences to Neo4j")
            except Exception as e:
                logger.warning(f"Failed to save to Neo4j: {e}")
        
        elapsed = time.time() - start_time
        logger.info(f"[Stage 12/14] COMPLETE - Saved {saved_count} sequences ({elapsed:.2f}s)")
        
        return saved_count