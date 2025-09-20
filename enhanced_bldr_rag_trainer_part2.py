# -*- coding: utf-8 -*-
"""
🚀 ENHANCED BLDR RAG TRAINER V3 - ЧАСТЬ 2
==========================================
Полные 15 этапов обработки с интеграцией всех улучшений

ЭТАПЫ ОБРАБОТКИ:
Stage 0: 📂 Сканирование и сортировка файлов (+ умная очередь)
Stage 1: 📄 Предобработка НТД (+ обновленная база)
Stage 2: ✅ Валидация файлов
Stage 3: 🔍 Проверка дубликатов 
Stage 4: 📖 Извлечение текста (PDF + DJVU + OCR)
Stage 5: 🎯 Детекция типа документа (+ SBERT)
Stage 6: 🏗️ Структурный анализ
Stage 7: 📝 Генерация Rubern-разметки  
Stage 8: 🏷️ Извлечение метаданных
Stage 9: 🎯 Контроль качества (+ мониторинг)
Stage 10: 📋 Типоспецифическая обработка
Stage 11: ⚙️ Извлечение последовательностей работ (+ SBERT)
Stage 12: 💾 Сохранение в Neo4j
Stage 13: 🧩 Разбиение на чанки (+ умный чанкинг)
Stage 14: 🎯 Векторизация и индексирование (+ кэширование)
"""

# Импорт базового класса из первой части
from enhanced_bldr_rag_trainer import EnhancedBldrRAGTrainer, logger, WorkSequence
import asyncio
import time
import glob
import os
import hashlib
from pathlib import Path
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm

# Добавляем основные методы обработки к классу
class EnhancedBldrRAGTrainerComplete(EnhancedBldrRAGTrainer):
    
    def train(self, max_files=None):
        """
        🚀 ГЛАВНЫЙ МЕТОД: Полный цикл обучения со всеми 15 этапами и улучшениями
        """
        logger.info("🚀 Starting Enhanced Bldr RAG Trainer v3 - Full 15-Stage Pipeline")
        
        try:
            # STAGE 0: Enhanced file scanning with smart queue
            all_files = self._stage_0_smart_file_scanning(max_files)
            if not all_files:
                logger.warning("❌ No files found for processing")
                return
            
            logger.info(f"📊 Total files to process: {len(all_files)}")
            
            # Process files with enhanced parallel processing
            if self.enable_parallel_processing and len(all_files) > 3:
                self._parallel_batch_processing(all_files)
            else:
                self._sequential_processing(all_files)
            
            # Generate final report
            self._generate_final_report()
            
            logger.info("🎉 Enhanced RAG training completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Training failed: {e}")
            self.performance_monitor.log_error(str(e), "main_training_loop")
            raise

    def _stage_0_smart_file_scanning(self, max_files=None):
        """
        STAGE 0: 📂 Enhanced file scanning with smart queue prioritization
        УЛУЧШЕНИЕ 7: Умная очередь с приоритизацией
        """
        stage_start = time.time()
        logger.info("Stage 0: 📂 Smart file scanning and prioritization")
        
        # Scan for all supported files
        file_patterns = ['*.pdf', '*.docx', '*.doc', '*.djvu', '*.txt']
        all_files = []
        
        for pattern in file_patterns:
            files = glob.glob(os.path.join(self.base_dir, '**', pattern), recursive=True)
            all_files.extend(files)
        
        if not all_files:
            logger.warning("No files found for processing")
            return []
        
        # Remove already processed files
        unprocessed_files = [
            f for f in all_files 
            if self._get_file_hash(f) not in self.processed_files
        ]
        
        logger.info(f"Found {len(all_files)} total files, {len(unprocessed_files)} unprocessed")
        
        # УЛУЧШЕНИЕ 7: Smart queue prioritization
        prioritized_files = self.smart_queue.sort_files(unprocessed_files)
        
        # Apply max_files limit
        if max_files and len(prioritized_files) > max_files:
            prioritized_files = prioritized_files[:max_files]
            logger.info(f"Limited to top {max_files} priority files")
        
        # Log prioritization results
        high_priority = len([f for f in prioritized_files if f[1] >= 8])
        medium_priority = len([f for f in prioritized_files if 4 <= f[1] < 8])
        low_priority = len([f for f in prioritized_files if f[1] < 4])
        
        logger.info(f"📊 Priority distribution - High: {high_priority}, Medium: {medium_priority}, Low: {low_priority}")
        
        stage_time = time.time() - stage_start
        self.performance_monitor.stats['stage_timings'].setdefault('stage_0_scanning', []).append(stage_time)
        
        return prioritized_files

    def _parallel_batch_processing(self, prioritized_files):
        """
        УЛУЧШЕНИЕ 9: Параллельная обработка файлов
        УЛУЧШЕНИЕ 6: Batch-обработка
        """
        logger.info(f"🚀 Starting parallel batch processing with {self.max_workers} workers")
        
        # Split files into batches
        batch_size = max(1, len(prioritized_files) // self.max_workers)
        batches = [prioritized_files[i:i + batch_size] 
                  for i in range(0, len(prioritized_files), batch_size)]
        
        logger.info(f"📦 Created {len(batches)} batches of ~{batch_size} files each")
        
        # Process batches in parallel
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all batches
            future_to_batch = {
                executor.submit(self._process_file_batch, batch, batch_idx): batch_idx 
                for batch_idx, batch in enumerate(batches)
            }
            
            # Process results as they complete
            for future in as_completed(future_to_batch):
                batch_idx = future_to_batch[future]
                try:
                    batch_results = future.result()
                    logger.info(f"✅ Batch {batch_idx + 1}/{len(batches)} completed: {batch_results['processed']} files processed")
                except Exception as e:
                    logger.error(f"❌ Batch {batch_idx + 1} failed: {e}")

    def _process_file_batch(self, file_batch, batch_idx):
        """Process a batch of files (used in parallel processing)"""
        batch_results = {'processed': 0, 'failed': 0, 'errors': []}
        
        logger.info(f"📦 Processing batch {batch_idx + 1} with {len(file_batch)} files")
        
        for file_path, priority in file_batch:
            try:
                success = self.process_single_file(file_path, priority)
                if success:
                    batch_results['processed'] += 1
                else:
                    batch_results['failed'] += 1
            except Exception as e:
                batch_results['failed'] += 1
                batch_results['errors'].append(str(e))
                logger.error(f"❌ Failed to process {file_path}: {e}")
        
        return batch_results

    def _sequential_processing(self, prioritized_files):
        """Sequential processing for smaller file sets"""
        logger.info(f"📋 Starting sequential processing of {len(prioritized_files)} files")
        
        processed_count = 0
        failed_count = 0
        
        for file_path, priority in tqdm(prioritized_files, desc="Processing files"):
            try:
                success = self.process_single_file(file_path, priority)
                if success:
                    processed_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                failed_count += 1
                logger.error(f"❌ Failed to process {file_path}: {e}")
        
        logger.info(f"✅ Sequential processing completed: {processed_count} success, {failed_count} failed")

    def process_single_file(self, file_path, priority=1):
        """
        🎯 ПОЛНАЯ ОБРАБОТКА ОДНОГО ФАЙЛА: Все 15 этапов с улучшениями
        """
        file_start_time = time.time()
        file_hash = self._get_file_hash(file_path)
        stages_timing = {}
        
        logger.info(f"🔄 Processing: {Path(file_path).name} (Priority: {priority})")
        
        try:
            # STAGE 1: NTD Preprocessing (УЛУЧШЕНИЕ 3)
            stage_1_start = time.time()
            preprocessed_path = self._stage_1_ntd_preprocessing(file_path)
            stages_timing['stage_1_ntd'] = time.time() - stage_1_start
            
            # STAGE 2: File Validation
            stage_2_start = time.time()
            validation_result = self._stage_2_file_validation(preprocessed_path)
            if not validation_result['is_valid']:
                logger.warning(f"⚠️ File validation failed: {validation_result['reason']}")
                return False
            stages_timing['stage_2_validation'] = time.time() - stage_2_start
            
            # STAGE 3: Duplicate Check
            stage_3_start = time.time()
            if self._stage_3_duplicate_check(file_hash, file_path):
                logger.info(f"⏭️ File already processed, skipping")
                return True
            stages_timing['stage_3_duplicate'] = time.time() - stage_3_start
            
            # STAGE 4: Enhanced Text Extraction
            stage_4_start = time.time()
            content = self._stage_4_enhanced_text_extraction(preprocessed_path)
            if not content or len(content.strip()) < 100:
                logger.warning("⚠️ Insufficient content extracted")
                return False
            stages_timing['stage_4_extraction'] = time.time() - stage_4_start
            
            # STAGE 5: Enhanced Document Type Detection (УЛУЧШЕНИЕ 1)
            stage_5_start = time.time()
            doc_type_info = self._stage_5_enhanced_document_type_detection(content, file_path)
            stages_timing['stage_5_detection'] = time.time() - stage_5_start
            
            # STAGE 6: Structural Analysis
            stage_6_start = time.time()
            doc_structure = self._stage_6_structural_analysis(content, doc_type_info)
            stages_timing['stage_6_structure'] = time.time() - stage_6_start
            
            # STAGE 7: Rubern Markup Generation
            stage_7_start = time.time()
            rubern_markup = self._stage_7_rubern_markup_generation(content, doc_structure, doc_type_info)
            stages_timing['stage_7_rubern'] = time.time() - stage_7_start
            
            # STAGE 8: Enhanced Metadata Extraction
            stage_8_start = time.time()
            metadata = self._stage_8_enhanced_metadata_extraction(content, doc_structure, file_path, doc_type_info)
            stages_timing['stage_8_metadata'] = time.time() - stage_8_start
            
            # STAGE 9: Enhanced Quality Control (УЛУЧШЕНИЕ 10)
            stage_9_start = time.time()
            quality_score = self._stage_9_enhanced_quality_control(content, doc_structure, metadata)
            stages_timing['stage_9_quality'] = time.time() - stage_9_start
            
            # STAGE 10: Type-specific Processing
            stage_10_start = time.time()
            type_specific_data = self._stage_10_type_specific_processing(
                content, doc_type_info, doc_structure, rubern_markup
            )
            stages_timing['stage_10_typespec'] = time.time() - stage_10_start
            
            # STAGE 11: Enhanced Work Sequence Extraction (УЛУЧШЕНИЕ 1)
            stage_11_start = time.time()
            work_sequences = self._stage_11_enhanced_work_extraction(
                content, doc_type_info, doc_structure, type_specific_data
            )
            stages_timing['stage_11_works'] = time.time() - stage_11_start
            
            # STAGE 12: Neo4j Storage
            stage_12_start = time.time()
            neo4j_saved = self._stage_12_neo4j_storage(work_sequences, metadata, file_path)
            stages_timing['stage_12_neo4j'] = time.time() - stage_12_start
            
            # STAGE 13: Enhanced Document Chunking (УЛУЧШЕНИЕ 5)
            stage_13_start = time.time()
            chunks = self._stage_13_enhanced_chunking(content, doc_structure, doc_type_info['doc_type'])
            stages_timing['stage_13_chunking'] = time.time() - stage_13_start
            
            # STAGE 14: Enhanced Vectorization and Indexing (УЛУЧШЕНИЕ 4,8)
            stage_14_start = time.time()
            vectorization_result = self._stage_14_enhanced_vectorization(chunks, metadata, file_path)
            stages_timing['stage_14_vectorization'] = time.time() - stage_14_start
            
            # Enhanced categorization (УЛУЧШЕНИЕ 2)
            category, category_confidence = self.document_categorizer.categorize_document(
                content, Path(file_path).name, doc_type_info['doc_type'], 
                [ws.name for ws in work_sequences]
            )
            
            # Update processed files registry
            self.processed_files[file_hash] = {
                'file_path': file_path,
                'processed_at': datetime.now().isoformat(),
                'doc_type': doc_type_info['doc_type'],
                'category': category,
                'quality_score': quality_score,
                'chunks_count': len(chunks),
                'works_count': len(work_sequences),
                'priority': priority,
                'processing_time': time.time() - file_start_time,
                'stages_timing': stages_timing
            }
            
            # Log performance metrics (УЛУЧШЕНИЕ 10)
            total_processing_time = time.time() - file_start_time
            self.performance_monitor.log_document(total_processing_time, quality_score, stages_timing)
            
            logger.info(f"✅ Completed: {Path(file_path).name} (Quality: {quality_score:.2f}, Time: {total_processing_time:.1f}s)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Processing failed for {file_path}: {e}")
            self.performance_monitor.log_error(str(e), file_path)
            return False
        
        finally:
            # Always save processed files registry
            self._save_processed_files()

    def _stage_1_ntd_preprocessing(self, file_path):
        """
        STAGE 1: 📄 NTD Preprocessing with updated database
        УЛУЧШЕНИЕ 3: Обновленная база НТД
        """
        if self.normative_db and self.normative_checker:
            try:
                preprocessed_path = ntd_preprocess(
                    file_path, self.normative_db, self.normative_checker, self.base_dir
                )
                logger.debug(f"NTD preprocessing completed: {preprocessed_path}")
                return preprocessed_path
            except Exception as e:
                logger.warning(f"NTD preprocessing failed: {e}")
        
        return file_path

    def _stage_2_file_validation(self, file_path):
        """STAGE 2: ✅ Enhanced file validation"""
        try:
            file_path_obj = Path(file_path)
            
            # Check file exists and is readable
            if not file_path_obj.exists():
                return {'is_valid': False, 'reason': 'File does not exist'}
            
            if not file_path_obj.is_file():
                return {'is_valid': False, 'reason': 'Path is not a file'}
            
            # Check file size (min 1KB, max 100MB)
            file_size = file_path_obj.stat().st_size
            if file_size < 1024:
                return {'is_valid': False, 'reason': 'File too small (< 1KB)'}
            
            if file_size > 100 * 1024 * 1024:
                return {'is_valid': False, 'reason': 'File too large (> 100MB)'}
            
            # Check file extension
            supported_extensions = {'.pdf', '.docx', '.doc', '.djvu', '.txt'}
            if file_path_obj.suffix.lower() not in supported_extensions:
                return {'is_valid': False, 'reason': f'Unsupported file type: {file_path_obj.suffix}'}
            
            # Try to read file (basic corruption check)
            try:
                with open(file_path, 'rb') as f:
                    f.read(1024)  # Read first 1KB
            except Exception as e:
                return {'is_valid': False, 'reason': f'Cannot read file: {e}'}
            
            return {'is_valid': True, 'reason': 'File validation passed', 'size': file_size}
            
        except Exception as e:
            return {'is_valid': False, 'reason': f'Validation error: {e}'}

    def _stage_3_duplicate_check(self, file_hash, file_path):
        """STAGE 3: 🔍 Enhanced duplicate detection"""
        if file_hash in self.processed_files:
            processed_info = self.processed_files[file_hash]
            logger.debug(f"Duplicate found: {file_path} already processed at {processed_info.get('processed_at')}")
            return True
        return False

    def _stage_4_enhanced_text_extraction(self, file_path):
        """STAGE 4: 📖 Enhanced text extraction with OCR fallback"""
        file_ext = Path(file_path).suffix.lower()
        
        try:
            if file_ext == '.pdf':
                return self._extract_from_pdf(file_path)
            elif file_ext in ['.docx', '.doc']:
                return self._extract_from_docx(file_path)
            elif file_ext == '.djvu':
                return self._extract_from_djvu(file_path)
            elif file_ext == '.txt':
                return self._extract_from_txt(file_path)
            else:
                logger.warning(f"Unsupported file format: {file_ext}")
                return ""
                
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return ""

    def _extract_from_pdf(self, file_path):
        """Enhanced PDF text extraction with OCR fallback"""
        try:
            # Try PyPDF2 first (fast)
            with open(file_path, 'rb') as file:
                reader = PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                
                if len(text.strip()) > 100:
                    return text
            
            # Fallback to langchain loader
            loader = PyPDFLoader(file_path)
            pages = loader.load()
            text = "\n".join([page.page_content for page in pages])
            
            if len(text.strip()) > 100:
                return text
            
            # OCR fallback for scanned PDFs
            logger.info(f"Attempting OCR for scanned PDF: {file_path}")
            return self._ocr_fallback(file_path)
            
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            return self._ocr_fallback(file_path)

    def _extract_from_docx(self, file_path):
        """Enhanced DOCX text extraction"""
        try:
            # Try langchain loader first
            loader = Docx2txtLoader(file_path)
            doc = loader.load()
            text = "\n".join([page.page_content for page in doc])
            
            if len(text.strip()) > 50:
                return text
            
            # Fallback to python-docx
            doc = Document(file_path)
            paragraphs = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    paragraphs.append(paragraph.text)
            
            return "\n".join(paragraphs)
            
        except Exception as e:
            logger.error(f"DOCX extraction error: {e}")
            return ""

    def _extract_from_djvu(self, file_path):
        """DJVU extraction with OCR"""
        try:
            # DJVU requires specialized tools, fallback to OCR
            logger.info(f"Processing DJVU file with OCR: {file_path}")
            return self._ocr_fallback(file_path)
        except Exception as e:
            logger.error(f"DJVU extraction error: {e}")
            return ""

    def _extract_from_txt(self, file_path):
        """Simple text file extraction"""
        try:
            encodings = ['utf-8', 'cp1251', 'latin-1']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            
            # If all encodings fail
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
                
        except Exception as e:
            logger.error(f"TXT extraction error: {e}")
            return ""

    def _ocr_fallback(self, file_path):
        """OCR fallback for scanned documents"""
        try:
            # This is a placeholder - actual OCR would require tesseract
            logger.warning(f"OCR fallback attempted for {file_path} (not implemented)")
            return ""
        except Exception as e:
            logger.error(f"OCR fallback error: {e}")
            return ""

    def _stage_5_enhanced_document_type_detection(self, content, file_path):
        """
        STAGE 5: 🎯 Enhanced document type detection
        Combining regex patterns with SBERT semantic analysis
        """
        # Use existing regex-based detection as baseline
        baseline_result = detect_document_type_with_symbiosis(content, file_path)
        
        # Enhance with semantic analysis
        filename = Path(file_path).name.lower()
        enhanced_confidence = baseline_result.get('confidence', 50.0)
        
        # Semantic enhancement using document categorizer
        try:
            category, cat_confidence = self.document_categorizer.categorize_document(
                content, filename, baseline_result.get('doc_type', 'unknown')
            )
            
            # Boost confidence if categorizer agrees
            if cat_confidence > 0.8:
                enhanced_confidence = min(enhanced_confidence + 15.0, 95.0)
            elif cat_confidence > 0.6:
                enhanced_confidence = min(enhanced_confidence + 10.0, 90.0)
                
        except Exception as e:
            logger.warning(f"Semantic document type detection failed: {e}")
        
        return {
            'doc_type': baseline_result.get('doc_type', 'unknown'),
            'doc_subtype': baseline_result.get('doc_subtype', ''),
            'confidence': enhanced_confidence,
            'regex_score': baseline_result.get('regex_score', 0.0),
            'rubern_score': baseline_result.get('rubern_score', 0.0),
            'semantic_boost': enhanced_confidence - baseline_result.get('confidence', 50.0)
        }

    def _stage_6_structural_analysis(self, content, doc_type_info):
        """STAGE 6: 🏗️ Enhanced structural analysis"""
        try:
            structure = {
                'sections': [],
                'tables': [],
                'lists': [],
                'figures': [],
                'headers': []
            }
            
            # Extract section numbers
            section_patterns = [
                r'\b(\d+\.\d+(?:\.\d+)*)\s+([^\n]{10,100})',  # Numbered sections
                r'^([A-ZА-Я][^.\n]{20,100})\s*$',  # Header-style sections
            ]
            
            for pattern in section_patterns:
                matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
                for match in matches[:20]:  # Limit sections
                    if isinstance(match, tuple):
                        structure['sections'].append(match[0])
                    else:
                        structure['sections'].append(match)
            
            # Extract tables (simple detection)
            table_patterns = [
                r'\|[^|\n]+\|',  # Pipe tables
                r'(?:Таблица|Table)\s+(\d+(?:\.\d+)*)',  # Table references
            ]
            
            for pattern in table_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                structure['tables'].extend(matches[:10])
            
            # Extract lists
            list_items = re.findall(r'^\s*[-•*]\s+(.+)$', content, re.MULTILINE)
            structure['lists'] = list_items[:20]
            
            # Document length analysis
            structure['word_count'] = len(content.split())
            structure['char_count'] = len(content)
            structure['paragraph_count'] = len([p for p in content.split('\n\n') if p.strip()])
            
            return structure
            
        except Exception as e:
            logger.error(f"Structural analysis failed: {e}")
            return {'sections': [], 'tables': [], 'lists': [], 'word_count': 0}

    def _stage_7_rubern_markup_generation(self, content, doc_structure, doc_type_info):
        """STAGE 7: 📝 Rubern markup generation"""
        try:
            # Use light Rubern scanning
            rubern_results = light_rubern_scan(content)
            
            # Enhance with structure information
            markup = {
                'rubern_scan': rubern_results,
                'structure_integration': {
                    'sections_count': len(doc_structure.get('sections', [])),
                    'tables_count': len(doc_structure.get('tables', [])),
                    'lists_count': len(doc_structure.get('lists', [])),
                },
                'doc_type_alignment': doc_type_info['doc_type'],
                'confidence': doc_type_info['confidence']
            }
            
            return markup
            
        except Exception as e:
            logger.error(f"Rubern markup generation failed: {e}")
            return {'rubern_scan': {}, 'structure_integration': {}}

    def _get_file_hash(self, file_path):
        """Generate hash for file duplicate detection"""
        try:
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                buf = f.read(65536)  # Read in 64kb chunks
                while len(buf) > 0:
                    hasher.update(buf)
                    buf = f.read(65536)
            return hasher.hexdigest()
        except Exception:
            # Fallback to path-based hash
            return hashlib.md5(str(file_path).encode()).hexdigest()

# Продолжение в части 3...
print("✅ Enhanced Bldr RAG Trainer v3 - Part 2 Created")
print("🚀 Содержит: Stages 0-7 с интеграцией улучшений")
print("📝 Следующий шаг: создание части 3 с остальными этапами")