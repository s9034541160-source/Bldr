# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _stage14_save_to_qdrant
# Основной источник: C:\Bldr\enterprise_rag_trainer_full.py
# Дубликаты (для справки):
#   - C:\Bldr\scripts\bldr_rag_trainer.py
#   - C:\Bldr\scripts\optimized_bldr_rag_trainer.py
#================================================================================
    def _stage14_save_to_qdrant(self, chunks: List[DocumentChunk], file_path: str, file_hash: str) -> int:
        """STAGE 14: Save to Qdrant"""
        
        logger.info(f"[Stage 14/14] SAVE TO QDRANT")
        start_time = time.time()
        
        if not self.qdrant:
            logger.warning("Qdrant not available - saving to JSON fallback")
            return self._save_chunks_to_json(chunks, file_path, file_hash)
        
        saved_count = 0
        
        try:
            points = []
            
            for i, chunk in enumerate(chunks):
                if not chunk.embedding:
                    continue
                
                payload = {
                    'file_path': file_path,
                    'file_hash': file_hash,
                    'chunk_id': f"{file_hash}_{i}",
                    'section_id': chunk.section_id,
                    'chunk_type': chunk.chunk_type,
                    'content': chunk.content,
                    'content_length': len(chunk.content),
                    'word_count': len(chunk.content.split()),
                    'processed_at': datetime.now().isoformat()
                }
                
                payload.update(chunk.metadata)
                
                point = models.PointStruct(
                    id=hash(f"{file_hash}_{i}") % (2**63),
                    vector=chunk.embedding,
                    payload=payload
                )
                
                points.append(point)
            
            # Сохраняем батчами с процентными индикаторами
            batch_size = 50
            total_points = len(points)
            
            for i in range(0, len(points), batch_size):
                batch_points = points[i:i+batch_size]
                
                self.qdrant.upsert(
                    collection_name="enterprise_docs",
                    points=batch_points
                )
                
                saved_count += len(batch_points)
                
                # Логируем прогресс каждые 10%
                self._log_progress(saved_count, total_points, "Qdrant save")
            
        except Exception as e:
            logger.error(f"Qdrant save failed: {e}")
            saved_count = self._save_chunks_to_json(chunks, file_path, file_hash)
        
        elapsed = time.time() - start_time
        logger.info(f"[Stage 14/14] COMPLETE - Saved {saved_count} chunks ({elapsed:.2f}s)")
        
        return saved_count