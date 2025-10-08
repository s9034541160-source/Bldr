# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _stage1_initial_validation
# Основной источник: C:\Bldr\enterprise_rag_trainer_full.py
# Дубликаты (для справки):
#   - C:\Bldr\scripts\bldr_rag_trainer.py
#   - C:\Bldr\scripts\optimized_bldr_rag_trainer.py
#================================================================================
    def _stage1_initial_validation(self, file_path: str) -> Dict[str, Any]:
        """STAGE 1: Initial Validation"""
        
        logger.info(f"[Stage 1/14] INITIAL VALIDATION: {Path(file_path).name}")
        start_time = time.time()
        
        result = {
            'file_exists': False,
            'file_size': 0,
            'can_read': False
        }
        
        try:
            path = Path(file_path)
            
            result['file_exists'] = path.exists()
            
            if result['file_exists']:
                result['file_size'] = path.stat().st_size
                
                try:
                    with open(path, 'rb') as f:
                        f.read(100)
                    result['can_read'] = True
                except:
                    result['can_read'] = False
        
        except Exception as e:
            logger.warning(f"Validation error: {e}")
        
        elapsed = time.time() - start_time
        
        if result['file_exists'] and result['can_read']:
            logger.info(f"[Stage 1/14] COMPLETE - File valid, size: {result['file_size']} bytes ({elapsed:.2f}s)")
        else:
            logger.warning(f"[Stage 1/14] FAILED - File invalid ({elapsed:.2f}s)")
        
        return result