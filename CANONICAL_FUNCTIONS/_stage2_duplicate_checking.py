# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _stage2_duplicate_checking
# Основной источник: C:\Bldr\enterprise_rag_trainer_full.py
# Дубликаты (для справки):
#   - C:\Bldr\scripts\bldr_rag_trainer.py
#   - C:\Bldr\scripts\optimized_bldr_rag_trainer.py
#================================================================================
    def _stage2_duplicate_checking(self, file_path: str) -> Dict[str, Any]:
        """STAGE 2: Duplicate Checking"""
        
        logger.info(f"[Stage 2/14] DUPLICATE CHECKING: {Path(file_path).name}")
        start_time = time.time()
        
        file_hash = self._calculate_file_hash(file_path)
        is_duplicate = file_hash in self.processed_files
        
        # Проверяем в Qdrant
        if not is_duplicate and self.qdrant:
            try:
                search_result = self.qdrant.scroll(
                    collection_name="enterprise_docs",
                    scroll_filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="file_hash",
                                match=models.MatchValue(value=file_hash)
                            )
                        ]
                    ),
                    limit=1
                )
                is_duplicate = len(search_result[0]) > 0
                
            except Exception as e:
                logger.warning(f"Qdrant duplicate check failed: {e}")
        
        result = {
            'is_duplicate': is_duplicate,
            'file_hash': file_hash
        }
        
        elapsed = time.time() - start_time
        
        if is_duplicate:
            logger.info(f"[Stage 2/14] DUPLICATE FOUND - Hash: {file_hash[:16]}... ({elapsed:.2f}s)")
        else:
            logger.info(f"[Stage 2/14] UNIQUE FILE - Hash: {file_hash[:16]}... ({elapsed:.2f}s)")
        
        return result