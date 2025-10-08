# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: process_single_file
# Основной источник: C:\Bldr\background_rag_training.py
# Дубликаты (для справки):
#   - C:\Bldr\interactive_rag_training.py
#================================================================================
    def process_single_file(self, file_path: Path) -> Dict[str, Any]:
        """Обработка одного файла с улучшенным чанкингом"""
        
        start_time = time.time()
        result = {
            'file_path': str(file_path),
            'success': False,
            'chunks_created': 0,
            'processing_time': 0,
            'error': None,
            'file_size': 0
        }
        
        try:
            # Проверяем размер файла
            if file_path.stat().st_size > 50 * 1024 * 1024:  # 50MB
                raise ValueError(f"File too large: {file_path.stat().st_size / 1024 / 1024:.1f}MB")
            
            result['file_size'] = file_path.stat().st_size
            
            # Читаем содержимое файла
            if file_path.suffix.lower() == '.txt':
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            else:
                # Для других форматов используем простое чтение
                # Добавлена поддержка PDF/DOCX через соответствующие библиотеки
                try:
                    if file_path.suffix.lower() == '.pdf':
                        # Импорт PDF обработчика
                        try:
                            import PyPDF2
                            with open(file_path, 'rb') as pdf_file:
                                pdf_reader = PyPDF2.PdfReader(pdf_file)
                                content = ''
                                for page in pdf_reader.pages:
                                    content += page.extract_text() + '\n'
                        except ImportError:
                            logger.warning("PyPDF2 not available for PDF processing")
                            raise ValueError("PDF processing library not available")
                    elif file_path.suffix.lower() in ['.docx', '.doc']:
                        # Импорт DOCX обработчика
                        try:
                            from docx import Document
                            doc = Document(str(file_path))
                            content = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
                        except ImportError:
                            logger.warning("python-docx not available for DOCX processing")
                            raise ValueError("DOCX processing library not available")
                    else:
                        # Для текстовых файлов
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                except Exception as e:
                    # Fallback для бинарных файлов
                    logger.warning(f"⚠️ Skipping file {file_path}: {str(e)}")
                    raise ValueError(f"File format not supported or processing error: {str(e)}")
            
            if not content.strip():
                raise ValueError("Empty file content")
            
            # Обрабатываем с помощью улучшенного RAG тренера
            document_result = self.rag_trainer.process_single_document(content, str(file_path))
            
            chunks_count = len(document_result.get('chunks', []))
            result['chunks_created'] = chunks_count
            result['success'] = True
            
            logger.info(f"✅ Processed {file_path.name}: {chunks_count} chunks")
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"❌ Failed to process {file_path.name}: {e}")
        
        result['processing_time'] = time.time() - start_time
        return result