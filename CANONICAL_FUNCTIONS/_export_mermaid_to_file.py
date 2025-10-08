# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _export_mermaid_to_file
# Основной источник: C:\Bldr\scripts\bldr_rag_trainer.py
# Дубликаты (для справки):
#   - C:\Bldr\scripts\optimized_bldr_rag_trainer.py
#================================================================================
    def _export_mermaid_to_file(self, mermaid_str: str, filename: str) -> str:
        """
        Export mermaid diagram string to file
        
        Args:
            mermaid_str: Mermaid diagram string
            filename: Output filename
            
        Returns:
            Path to the generated file
        """
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(mermaid_str)
        return filename