#!/usr/bin/env python3
"""
File Organizer Module
Автоматическая организация файлов по папкам после определения типа документа
"""

import os
import shutil
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class DocumentFileOrganizer:
    """Организатор файлов по типам документов"""
    
    def __init__(self, base_dir: str = "I:/docs"):
        self.base_dir = Path(base_dir)
        self.downloaded_dir = self.base_dir / "downloaded"
        
        # Структура папок по типам документов
        self.folder_structure = {
            # Нормативные документы
            'norms': {
                'folder': 'norms',
                'subfolders': {
                    'gost': 'norms/gost',
                    'snip': 'norms/snip', 
                    'sp': 'norms/sp',
                    'general': 'norms/general'
                }
            },
            
            # Сметы и расчеты
            'estimates': {
                'folder': 'estimates',
                'subfolders': {
                    'gesn': 'estimates/gesn',
                    'fer': 'estimates/fer',
                    'ter': 'estimates/ter',
                    'local': 'estimates/local_estimates',
                    'summary': 'estimates/summary_estimates'
                }
            },
            
            # Проектная документация
            'projects': {
                'folder': 'projects',
                'subfolders': {
                    'ppr': 'projects/ppr',
                    'pto': 'projects/pto',
                    'drawings': 'projects/drawings',
                    'specifications': 'projects/specifications'
                }
            },
            
            # Договоры и контракты
            'contracts': {
                'folder': 'contracts',
                'subfolders': {
                    'construction': 'contracts/construction',
                    'supply': 'contracts/supply',
                    'service': 'contracts/service',
                    'subcontract': 'contracts/subcontract'
                }
            },
            
            # Отчеты и акты
            'reports': {
                'folder': 'reports',
                'subfolders': {
                    'acts': 'reports/acts',
                    'certificates': 'reports/certificates',
                    'inspections': 'reports/inspections',
                    'progress': 'reports/progress'
                }
            },
            
            # Техническая документация
            'technical': {
                'folder': 'technical',
                'subfolders': {
                    'manuals': 'technical/manuals',
                    'specifications': 'technical/specifications',
                    'catalogs': 'technical/catalogs',
                    'datasheets': 'technical/datasheets'
                }
            },
            
            # Прочие документы
            'other': {
                'folder': 'other',
                'subfolders': {
                    'letters': 'other/letters',
                    'protocols': 'other/protocols',
                    'presentations': 'other/presentations',
                    'unknown': 'other/unknown'
                }
            }
        }
        
        # Создаем все необходимые папки
        self._create_folder_structure()
        
        # Файл для отслеживания перемещений
        self.moves_log = self.base_dir / "file_moves.json"
        self.moves_history = self._load_moves_history()

    def _create_folder_structure(self):
        """Создание структуры папок"""
        logger.info("📁 Создание структуры папок для организации файлов...")
        
        created_folders = []
        
        for doc_type, config in self.folder_structure.items():
            # Создаем основную папку
            main_folder = self.base_dir / config['folder']
            main_folder.mkdir(parents=True, exist_ok=True)
            created_folders.append(str(main_folder))
            
            # Создаем подпапки
            for subfolder_key, subfolder_path in config['subfolders'].items():
                subfolder = self.base_dir / subfolder_path
                subfolder.mkdir(parents=True, exist_ok=True)
                created_folders.append(str(subfolder))
        
        logger.info(f"✅ Создано папок: {len(created_folders)}")

    def _load_moves_history(self) -> Dict:
        """Загрузка истории перемещений"""
        if self.moves_log.exists():
            try:
                with open(self.moves_log, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Ошибка загрузки истории перемещений: {e}")
        
        return {'moves': [], 'stats': {}}

    def _save_moves_history(self):
        """Сохранение истории перемещений"""
        try:
            with open(self.moves_log, 'w', encoding='utf-8') as f:
                json.dump(self.moves_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения истории перемещений: {e}")

    def organize_file(self, file_path: str, doc_type_info: Dict[str, Any], 
                     structural_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Организация файла по типу документа
        
        Args:
            file_path: Путь к файлу
            doc_type_info: Информация о типе документа из этапа 4
            structural_data: Структурные данные из этапа 5
            
        Returns:
            Dict с информацией о перемещении
        """
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                return {
                    'status': 'error',
                    'error': f'Файл не найден: {file_path}',
                    'original_path': file_path,
                    'new_path': None
                }
            
            # Определяем целевую папку
            target_folder = self._determine_target_folder(doc_type_info, structural_data, source_path)
            
            # Создаем уникальное имя файла если нужно
            target_path = self._get_unique_target_path(source_path, target_folder)
            
            # Перемещаем файл
            logger.info(f"📦 Перемещение файла: {source_path.name}")
            logger.info(f"   Из: {source_path}")
            logger.info(f"   В:  {target_path}")
            
            # Создаем целевую папку если не существует
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Перемещаем файл
            shutil.move(str(source_path), str(target_path))
            
            # Записываем в историю
            from datetime import datetime
            move_record = {
                'timestamp': datetime.now().isoformat(),
                'original_path': str(source_path),
                'new_path': str(target_path),
                'doc_type': doc_type_info.get('doc_type', 'unknown'),
                'doc_subtype': doc_type_info.get('doc_subtype', 'unknown'),
                'confidence': doc_type_info.get('confidence', 0.0),
                'file_size': target_path.stat().st_size,
                'reason': self._get_move_reason(doc_type_info, structural_data)
            }
            
            self.moves_history['moves'].append(move_record)
            self._update_stats(doc_type_info['doc_type'])
            self._save_moves_history()
            
            logger.info(f"✅ Файл успешно перемещен в: {target_path.parent.name}/{target_path.name}")
            
            return {
                'status': 'success',
                'original_path': str(source_path),
                'new_path': str(target_path),
                'target_folder': str(target_path.parent),
                'doc_type': doc_type_info.get('doc_type'),
                'move_reason': move_record['reason']
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка перемещения файла {file_path}: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'original_path': file_path,
                'new_path': None
            }

    def _determine_target_folder(self, doc_type_info: Dict, structural_data: Dict, 
                                source_path: Path) -> Path:
        """Определение целевой папки для файла"""
        
        doc_type = doc_type_info.get('doc_type', 'other')
        doc_subtype = doc_type_info.get('doc_subtype', 'general')
        filename = source_path.name.lower()
        
        # Специальная логика для нормативных документов
        if doc_type == 'norms':
            if 'гост' in filename or 'gost' in filename:
                return self.base_dir / self.folder_structure['norms']['subfolders']['gost']
            elif 'снип' in filename or 'snip' in filename:
                return self.base_dir / self.folder_structure['norms']['subfolders']['snip']
            elif any(sp_marker in filename for sp_marker in ['сп ', 'sp ', 'свод правил']):
                return self.base_dir / self.folder_structure['norms']['subfolders']['sp']
            else:
                return self.base_dir / self.folder_structure['norms']['subfolders']['general']
        
        # Специальная логика для смет
        elif doc_type == 'estimates':
            if 'гэсн' in filename or 'gesn' in filename:
                return self.base_dir / self.folder_structure['estimates']['subfolders']['gesn']
            elif 'фер' in filename or 'fer' in filename:
                return self.base_dir / self.folder_structure['estimates']['subfolders']['fer']
            elif 'тер' in filename or 'ter' in filename:
                return self.base_dir / self.folder_structure['estimates']['subfolders']['ter']
            elif 'локальн' in filename or 'local' in filename:
                return self.base_dir / self.folder_structure['estimates']['subfolders']['local']
            else:
                return self.base_dir / self.folder_structure['estimates']['subfolders']['summary']
        
        # Специальная логика для проектов
        elif doc_type == 'projects':
            if doc_subtype == 'ppr' or 'ппр' in filename:
                return self.base_dir / self.folder_structure['projects']['subfolders']['ppr']
            elif doc_subtype == 'pto' or 'пто' in filename:
                return self.base_dir / self.folder_structure['projects']['subfolders']['pto']
            elif any(drawing_marker in filename for drawing_marker in ['чертеж', 'план', 'схема']):
                return self.base_dir / self.folder_structure['projects']['subfolders']['drawings']
            else:
                return self.base_dir / self.folder_structure['projects']['subfolders']['specifications']
        
        # Для остальных типов используем базовую логику
        elif doc_type in self.folder_structure:
            # Используем подтип если есть соответствующая подпапка
            if doc_subtype in self.folder_structure[doc_type]['subfolders']:
                subfolder_path = self.folder_structure[doc_type]['subfolders'][doc_subtype]
                return self.base_dir / subfolder_path
            else:
                # Используем первую доступную подпапку
                first_subfolder = list(self.folder_structure[doc_type]['subfolders'].values())[0]
                return self.base_dir / first_subfolder
        
        # По умолчанию - в папку "other/unknown"
        return self.base_dir / self.folder_structure['other']['subfolders']['unknown']

    def _get_unique_target_path(self, source_path: Path, target_folder: Path) -> Path:
        """Получение уникального пути для файла в целевой папке"""
        
        base_name = source_path.stem
        extension = source_path.suffix
        target_path = target_folder / source_path.name
        
        # Если файл уже существует, добавляем номер
        counter = 1
        while target_path.exists():
            new_name = f"{base_name}_{counter}{extension}"
            target_path = target_folder / new_name
            counter += 1
        
        return target_path

    def _get_move_reason(self, doc_type_info: Dict, structural_data: Dict) -> str:
        """Получение причины перемещения для логирования"""
        
        doc_type = doc_type_info.get('doc_type', 'unknown')
        confidence = doc_type_info.get('confidence', 0.0)
        
        reasons = []
        
        if confidence > 0.8:
            reasons.append(f"Высокая уверенность типа ({confidence:.2f})")
        elif confidence > 0.6:
            reasons.append(f"Средняя уверенность типа ({confidence:.2f})")
        else:
            reasons.append(f"Низкая уверенность типа ({confidence:.2f})")
        
        if structural_data:
            sections = len(structural_data.get('sections', []))
            if sections > 0:
                reasons.append(f"Найдено разделов: {sections}")
        
        return "; ".join(reasons)

    def _update_stats(self, doc_type: str):
        """Обновление статистики перемещений"""
        if 'stats' not in self.moves_history:
            self.moves_history['stats'] = {}
        
        if doc_type not in self.moves_history['stats']:
            self.moves_history['stats'][doc_type] = 0
        
        self.moves_history['stats'][doc_type] += 1

    def get_organization_stats(self) -> Dict[str, Any]:
        """Получение статистики организации файлов"""
        
        stats = {
            'total_moves': len(self.moves_history.get('moves', [])),
            'by_type': self.moves_history.get('stats', {}),
            'folder_contents': {},
            'recent_moves': []
        }
        
        # Подсчет файлов в каждой папке
        for doc_type, config in self.folder_structure.items():
            for subfolder_key, subfolder_path in config['subfolders'].items():
                folder_path = self.base_dir / subfolder_path
                if folder_path.exists():
                    file_count = len(list(folder_path.glob('*.*')))
                    stats['folder_contents'][subfolder_path] = file_count
        
        # Последние 10 перемещений
        recent_moves = self.moves_history.get('moves', [])[-10:]
        stats['recent_moves'] = recent_moves
        
        return stats

    def undo_last_move(self) -> Dict[str, Any]:
        """Отмена последнего перемещения"""
        
        if not self.moves_history.get('moves'):
            return {
                'status': 'error',
                'error': 'Нет перемещений для отмены'
            }
        
        try:
            last_move = self.moves_history['moves'].pop()
            
            # Перемещаем файл обратно
            current_path = Path(last_move['new_path'])
            original_path = Path(last_move['original_path'])
            
            if current_path.exists():
                # Создаем исходную папку если не существует
                original_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(current_path), str(original_path))
                
                # Обновляем статистику
                doc_type = last_move['doc_type']
                if doc_type in self.moves_history['stats']:
                    self.moves_history['stats'][doc_type] -= 1
                    if self.moves_history['stats'][doc_type] <= 0:
                        del self.moves_history['stats'][doc_type]
                
                self._save_moves_history()
                
                logger.info(f"↩️ Отменено перемещение: {original_path.name}")
                
                return {
                    'status': 'success',
                    'restored_path': str(original_path),
                    'move_info': last_move
                }
            else:
                return {
                    'status': 'error',
                    'error': f'Файл не найден для отмены: {current_path}'
                }
                
        except Exception as e:
            logger.error(f"Ошибка отмены перемещения: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }


# Функция для интеграции с RAG-тренером
def organize_document_file(file_path: str, doc_type_info: Dict[str, Any], 
                          structural_data: Dict[str, Any] = None, 
                          base_dir: str = "I:/docs") -> Dict[str, Any]:
    """
    Организация файла документа по типу
    
    Args:
        file_path: Путь к файлу
        doc_type_info: Информация о типе документа
        structural_data: Структурные данные
        base_dir: Базовая директория
        
    Returns:
        Результат организации файла
    """
    organizer = DocumentFileOrganizer(base_dir)
    return organizer.organize_file(file_path, doc_type_info, structural_data)


if __name__ == "__main__":
    # Тестирование организатора
    organizer = DocumentFileOrganizer()
    
    # Пример использования
    test_doc_info = {
        'doc_type': 'norms',
        'doc_subtype': 'gost',
        'confidence': 0.95
    }
    
    test_structural = {
        'sections': ['Раздел 1', 'Раздел 2'],
        'paragraphs': []
    }
    
    print("📊 Статистика организации файлов:")
    stats = organizer.get_organization_stats()
    print(json.dumps(stats, ensure_ascii=False, indent=2))