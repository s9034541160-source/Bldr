# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _generate_embeddings_with_batching
# Основной источник: C:\Bldr\scripts\bldr_rag_trainer.py
# Дубликаты (для справки):
#   - C:\Bldr\scripts\optimized_bldr_rag_trainer.py
#================================================================================
    def _generate_embeddings_with_batching(self, chunk_texts: List[str], batch_size: int = None) -> np.ndarray:
        """
        Generate embeddings with GPU/CPU optimized batching and progress tracking.
        
        Args:
            chunk_texts: List of text chunks to embed
            batch_size: Size of batches to process (auto-detected based on device)
            
        Returns:
            Array of embeddings
        """
        try:
            # Auto-detect optimal batch size based on device
            if batch_size is None:
                if hasattr(self, 'device') and self.device == 'cuda':
                    batch_size = 64  # Larger batches for GPU
                else:
                    batch_size = 16  # Smaller batches for CPU
            
            all_embeddings = []
            total_batches = (len(chunk_texts) + batch_size - 1) // batch_size
            device_name = getattr(self, 'device', 'cpu').upper()
            
            print(f'🚀 Генерируем векторы для {len(chunk_texts)} чанков в {total_batches} батчах на {device_name}...')
            
            # Process with device-optimized batching
            for i in tqdm(range(0, len(chunk_texts), batch_size), desc=f'{device_name} векторизация'):
                batch = chunk_texts[i:i + batch_size]
                try:
                    # Device-optimized encoding
                    batch_embeddings = self.embedding_model.encode(
                        batch, 
                        show_progress_bar=False,
                        batch_size=len(batch),  # Use full batch
                        device=getattr(self, 'device', 'cpu'),
                        convert_to_numpy=True,
                        normalize_embeddings=True  # Better for similarity search
                    )
                    all_embeddings.append(batch_embeddings)
                except Exception as e:
                    print(f'Error generating embeddings for batch {i//batch_size}: {e}')
                    # Create zero embeddings as fallback
                    zero_embeddings = np.zeros((len(batch), self.dimension))
                    all_embeddings.append(zero_embeddings)
            
            if all_embeddings:
                return np.vstack(all_embeddings)
            else:
                return np.array([])
                
        except Exception as e:
            print(f'Error in batch embedding generation: {e}')
            # Return zero embeddings as fallback
            return np.zeros((len(chunk_texts), self.dimension)) if chunk_texts else np.array([])