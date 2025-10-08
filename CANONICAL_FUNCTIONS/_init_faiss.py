# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _init_faiss
# Основной источник: C:\Bldr\scripts\bldr_rag_trainer.py
# Дубликаты (для справки):
#   - C:\Bldr\scripts\optimized_bldr_rag_trainer.py
#================================================================================
    def _init_faiss(self):
        """Initialize FAISS index"""
        try:
            if os.path.exists(self.faiss_path):
                self.index = faiss.read_index(self.faiss_path)
            else:
                self.index = faiss.IndexFlatIP(self.dimension)
                faiss.write_index(self.index, self.faiss_path)
        except Exception as e:
            logger.warning(f"FAISS initialization failed: {e}")
            # Create a mock index
            self.index = None