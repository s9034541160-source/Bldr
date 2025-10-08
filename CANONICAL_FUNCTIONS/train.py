# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: train
# Основной источник: C:\Bldr\enterprise_rag_trainer_full.py
# Дубликаты (для справки):
#   - C:\Bldr\working_frontend_rag_integration.py
#   - C:\Bldr\scripts\bldr_rag_trainer.py
#   - C:\Bldr\scripts\optimized_bldr_rag_trainer.py
#================================================================================
    def train(self, max_files: Optional[int] = None):
        """
        Главный метод обучения с правильными этапами
        
        Args:
            max_files: Максимальное количество файлов для обработки
        """
        
        logger.info("=== STARTING ENTERPRISE RAG TRAINING ===")
        logger.info(f"Max files: {max_files if max_files else 'ALL'}")
        
        start_time = time.time()
        
        try:
            # ===== STAGE 0: Smart File Scanning + NTD Preprocessing =====
            all_files = self._stage_0_smart_file_scanning_and_preprocessing(max_files)
            
            if not all_files:
                logger.warning("No files found for processing")
                return
            
            self.stats['files_found'] = len(all_files)
            logger.info(f"Total files to process: {len(all_files)}")
            
            # Обработка каждого файла через полный пайплайн
            for i, file_path in enumerate(all_files, 1):
                logger.info(f"\n=== PROCESSING FILE {i}/{len(all_files)}: {Path(file_path).name} ===")
                
                try:
                    success = self._process_single_file(file_path)
                    if success:
                        self.stats['files_processed'] += 1
                        logger.info(f"File processed successfully: {Path(file_path).name}")
                    else:
                        self.stats['files_failed'] += 1
                        logger.warning(f"File processing failed: {Path(file_path).name}")
                        
                except Exception as e:
                    self.stats['files_failed'] += 1
                    logger.error(f"Error processing file {file_path}: {e}")
                    logger.error(traceback.format_exc())
            
            # Генерация финального отчета
            self._generate_final_report(time.time() - start_time)
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            logger.error(traceback.format_exc())
            raise