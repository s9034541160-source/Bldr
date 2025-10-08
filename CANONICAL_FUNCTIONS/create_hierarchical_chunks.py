# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: create_hierarchical_chunks
# Основной источник: C:\Bldr\enterprise_rag_trainer_full.py
# Дубликаты (для справки):
#   - C:\Bldr\recursive_hierarchical_chunker.py
#================================================================================
    def create_hierarchical_chunks(self, content: str) -> List:
        """Создание иерархических чанков"""
        
        chunks = []
        
        # Разделяем по секциям
        sections = self._detect_sections(content)
        
        for i, section in enumerate(sections):
            chunk = type('Chunk', (), {})()
            chunk.content = section['content']
            chunk.title = section.get('title', f'Раздел {i+1}')
            chunk.level = section.get('level', 1)
            chunks.append(chunk)
        
        return chunks