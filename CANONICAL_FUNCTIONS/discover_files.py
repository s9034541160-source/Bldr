# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: discover_files
# Основной источник: C:\Bldr\background_rag_training.py
# Дубликаты (для справки):
#   - C:\Bldr\interactive_rag_training.py
#================================================================================
    def discover_files(self) -> List[Path]:
        """Поиск всех документов для обработки"""
        
        logger.info("🔍 Discovering files for training...")
        
        extensions = ['*.pdf', '*.docx', '*.doc', '*.txt', '*.rtf']
        all_files = []
        
        for ext in extensions:
            try:
                files = list(self.base_dir.rglob(ext))
                all_files.extend(files)
                logger.info(f"  📄 Found {len(files)} {ext} files")
            except Exception as e:
                logger.warning(f"⚠️ Error searching for {ext}: {e}")
        
        # Фильтруем дубликаты и недоступные файлы
        unique_files = []
        seen_names = set()
        
        for file_path in all_files:
            if file_path.name.lower() not in seen_names and file_path.exists():
                unique_files.append(file_path)
                seen_names.add(file_path.name.lower())
        
        logger.info(f"📊 Total unique files discovered: {len(unique_files)}")
        self.stats['files_found'] = len(unique_files)
        
        return unique_files