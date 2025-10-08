# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _init_qdrant
# Основной источник: C:\Bldr\scripts\bldr_rag_trainer.py
# Дубликаты (для справки):
#   - C:\Bldr\scripts\optimized_bldr_rag_trainer.py
#================================================================================
    def _init_qdrant(self):
        """Initialize Qdrant collection with proper error handling"""
        if self.qdrant_client is None:
            logger.warning("Qdrant client not available, skipping initialization")
            return
            
        try:
            # Check if collection exists, create if it doesn't
            try:
                self.qdrant_client.get_collection('universal_docs')
                logger.info("Qdrant collection already exists")
            except:
                # Collection doesn't exist, create it
                self.qdrant_client.create_collection(
                    collection_name='universal_docs',
                    vectors_config=VectorParams(size=self.dimension, distance=Distance.COSINE)
                )
                logger.info("Qdrant collection created successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant collection: {e}")