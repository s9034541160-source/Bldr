# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _load_processed_files
# Основной источник: C:\Bldr\enterprise_rag_trainer_full.py
# Дубликаты (для справки):
#   - C:\Bldr\scripts\bldr_rag_trainer.py
#   - C:\Bldr\scripts\fast_bldr_rag_trainer.py
#   - C:\Bldr\scripts\optimized_bldr_rag_trainer.py
#================================================================================
    def _load_processed_files(self):
        """Загрузка списка обработанных файлов"""
        
        try:
            if self.processed_files_json.exists():
                with open(self.processed_files_json, 'r', encoding='utf-8') as f:
                    self.processed_files = json.load(f)
                logger.info(f"Loaded {len(self.processed_files)} processed files")
            else:
                self.processed_files = {}
                logger.info("No processed files found - starting fresh")
        except Exception as e:
            logger.error(f"Failed to load processed files: {e}")
            self.processed_files = {}