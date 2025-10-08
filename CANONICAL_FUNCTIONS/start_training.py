# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: start_training
# Основной источник: C:\Bldr\background_rag_training.py
# Дубликаты (для справки):
#   - C:\Bldr\interactive_rag_training.py
#================================================================================
    def start_training(self, resume: bool = True):
        """Запуск полного обучения в фоне"""
        
        logger.info("🚀 Starting background RAG training...")
        
        # Register process with process tracker
        process_tracker.start_process(
            process_id=self.process_id,
            process_type=ProcessType.RAG_TRAINING,
            name="RAG Training Process",
            description="Full RAG training on all documents",
            metadata={
                "base_dir": str(self.base_dir),
                "max_workers": self.max_workers,
                "resume": resume
            }
        )
        
        # Update process tracker status
        process_tracker.update_process(
            self.process_id,
            status=ProcessStatus.RUNNING,
            progress=0,
            metadata_update={"stage": "initializing"}
        )
        
        # Загружаем прогресс если нужно
        if resume:
            self.load_progress()
        
        # Находим все файлы
        all_files = self.discover_files()
        
        if not all_files:
            logger.error("❌ No files found for training!")
            process_tracker.update_process(
                self.process_id,
                status=ProcessStatus.FAILED,
                metadata_update={"stage": "error", "error": "No files found for training"}
            )
            return
        
        # Фильтруем уже обработанные файлы при возобновлении
        if resume:
            files_to_process = [f for f in all_files if str(f) not in self.processed_files]
            logger.info(f"📁 Resuming training: {len(files_to_process)} files left to process")
        else:
            files_to_process = all_files
            self.processed_files.clear()
            self.failed_files.clear()
        
        if not files_to_process:
            logger.info("✅ All files already processed!")
            process_tracker.update_process(
                self.process_id,
                status=ProcessStatus.COMPLETED,
                progress=100,
                metadata_update={"stage": "completed", "message": "All files already processed"}
            )
            return
        
        self.stats['start_time'] = time.time()
        self.stats['files_found'] = len(all_files)
        self.running = True
        
        # Update process tracker
        process_tracker.update_process(
            self.process_id,
            progress=5,
            metadata_update={"stage": "processing", "files_to_process": len(files_to_process)}
        )
        
        # Запускаем отдельный поток для печати прогресса
        progress_thread = threading.Thread(target=self._progress_monitor, daemon=True)
        progress_thread.start()
        
        # Обрабатываем файлы в многопоточном режиме
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Отправляем задачи на обработку
                future_to_file = {
                    executor.submit(self.process_single_file, file_path): file_path 
                    for file_path in files_to_process
                }
                
                # Обрабатываем результаты по мере готовности
                for future in as_completed(future_to_file):
                    if not self.running:
                        break
                    
                    file_path = future_to_file[future]
                    self.stats['current_file'] = file_path.name
                    
                    try:
                        result = future.result(timeout=1800)  # 30 минут таймаут
                        self.update_stats(result)
                        
                        # Update process tracker with progress
                        total_files = self.stats['files_found']
                        processed_total = self.stats['files_processed'] + self.stats['files_failed']
                        progress_percent = (processed_total / total_files) * 100 if total_files > 0 else 0
                        
                        process_tracker.update_process(
                            self.process_id,
                            progress=int(progress_percent),
                            metadata_update={
                                "stage": "processing",
                                "current_file": file_path.name,
                                "files_processed": self.stats['files_processed'],
                                "files_failed": self.stats['files_failed']
                            }
                        )
                        
                        # Сохраняем прогресс каждые 10 файлов
                        if (self.stats['files_processed'] + self.stats['files_failed']) % 10 == 0:
                            self.save_progress()
                            self.save_stats()
                        
                    except Exception as e:
                        logger.error(f"❌ Task failed for {file_path.name}: {e}")
                        self.stats['files_failed'] += 1
                        self.failed_files.add(str(file_path))
                        
                        # Update process tracker with error
                        process_tracker.update_process(
                            self.process_id,
                            metadata_update={
                                "stage": "processing",
                                "error_files": len(self.failed_files),
                                "last_error": str(e)
                            }
                        )
        
        except KeyboardInterrupt:
            logger.info("⚠️ Training interrupted by user")
            process_tracker.update_process(
                self.process_id,
                status=ProcessStatus.CANCELLED,
                metadata_update={"stage": "cancelled", "message": "Training interrupted by user"}
            )
        except Exception as e:
            logger.error(f"❌ Training failed with error: {e}")
            process_tracker.update_process(
                self.process_id,
                status=ProcessStatus.FAILED,
                metadata_update={"stage": "error", "error": str(e)}
            )
        
        finally:
            self.running = False
            self.stats['end_time'] = time.time()
            
            # Сохраняем финальный прогресс и статистику
            self.save_progress()
            self.save_stats()
            
            # Update process tracker with final status
            if self.stats['files_failed'] == 0:
                process_tracker.update_process(
                    self.process_id,
                    status=ProcessStatus.COMPLETED,
                    progress=100,
                    metadata_update={"stage": "completed", "message": "Training completed successfully"}
                )
            else:
                process_tracker.update_process(
                    self.process_id,
                    status=ProcessStatus.COMPLETED,
                    progress=100,
                    metadata_update={
                        "stage": "completed_with_errors",
                        "message": f"Training completed with {self.stats['files_failed']} failed files",
                        "files_processed": self.stats['files_processed'],
                        "files_failed": self.stats['files_failed']
                    }
                )
            
            # Выводим финальный отчет
            self._print_final_report()