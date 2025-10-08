# КАНОНИЧЕСКАЯ ВЕРСИЯ функции: _stage3_local_scan_and_copy
# Основной источник: C:\Bldr\scripts\bldr_rag_trainer.py
# Дубликаты (для справки):
#   - C:\Bldr\scripts\fast_bldr_rag_trainer.py
#   - C:\Bldr\scripts\optimized_bldr_rag_trainer.py
#================================================================================
    def _stage3_local_scan_and_copy(self):
        local_files = []
        self.norms_db.mkdir(exist_ok=True)
        for ext in ['*.pdf', '*.docx', '*.xlsx', '*.jpg', '*.dwg']:
            files = glob.glob(os.path.join(self.base_dir, '**', ext), recursive=True)
            for f in tqdm(files, desc=f'Scan {ext}'):
                dest = self.norms_db / Path(f).name
                if not dest.exists():
                    try:
                        shutil.copy2(f, dest)
                        local_files.append(str(dest))
                    except Exception as e:
                        print(f'Copy error for {f}: {e}')
                else:
                    local_files.append(str(dest))
        print(f'Local scan: Copied/Found {len(local_files)} files to norms_db/')
        return local_files