# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _save_processed_files
# Основной источник: C:\Bldr\scripts\bldr_rag_trainer.py
# Дубликаты (для справки):
#   - C:\Bldr\scripts\fast_bldr_rag_trainer.py
#   - C:\Bldr\scripts\optimized_bldr_rag_trainer.py
#================================================================================
    def _save_processed_files(self):
        processed_file = self.reports_dir / 'processed_files.json'
        with open(processed_file, 'w') as f:
            json.dump(self.processed_files, f)