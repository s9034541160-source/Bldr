#!/usr/bin/env python3
"""
Non-intrusive Metrics Collection System
Неинтрузивная система сбора метрик для RAG-обучения
"""

import os
import sys
import time
import json
import psutil
import threading
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging
import re
import hashlib
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class MetricType(Enum):
    SYSTEM = "system"
    TRAINING = "training"
    DOCUMENT = "document"
    ERROR = "error"
    PERFORMANCE = "performance"

class MetricSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class SystemMetric:
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    memory_available: float
    disk_usage: float
    disk_free: float
    gpu_usage: Optional[float] = None
    gpu_memory: Optional[float] = None
    network_io: Optional[Dict[str, float]] = None
    process_count: int = 0
    
@dataclass
class TrainingMetric:
    timestamp: datetime
    session_id: str
    stage: str
    progress: float
    documents_processed: int
    chunks_generated: int
    embeddings_created: int
    processing_speed: float
    throughput: float
    error_rate: float
    memory_peak: float
    
@dataclass
class DocumentMetric:
    timestamp: datetime
    document_id: str
    filename: str
    file_size: int
    processing_time: float
    chunks_count: int
    embeddings_count: int
    quality_score: float
    language: str
    status: str
    errors: List[str] = field(default_factory=list)
    
@dataclass
class ErrorMetric:
    timestamp: datetime
    error_type: str
    error_message: str
    severity: MetricSeverity
    component: str
    document_id: Optional[str] = None
    stack_trace: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)

class NonIntrusiveMetricsCollector:
    """Неинтрузивный сборщик метрик"""
    
    def __init__(self, db_path: str = "I:/docs/cache/metrics.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Инициализация базы данных
        self._init_database()
        
        # Состояние сборщика
        self.is_running = False
        self.collection_thread = None
        self.collection_interval = 5  # секунды
        
        # Кэш метрик в памяти
        self.metrics_cache = {
            MetricType.SYSTEM: deque(maxlen=1000),
            MetricType.TRAINING: deque(maxlen=1000),
            MetricType.DOCUMENT: deque(maxlen=5000),
            MetricType.ERROR: deque(maxlen=1000),
            MetricType.PERFORMANCE: deque(maxlen=1000)
        }
        
        # Пути для мониторинга
        self.log_paths = [
            "logs/",
            "training_logs/",
            "rag_logs/",
            "./",  # Текущая директория для логов
        ]
        
        # Паттерны для извлечения информации из логов
        self.log_patterns = {
            'training_progress': r'Progress:\s*(\d+\.?\d*)%',
            'documents_processed': r'Processed\s+(\d+)\s+documents',
            'processing_speed': r'Speed:\s*(\d+\.?\d*)\s*(docs?/s|MB/s)',
            'error': r'ERROR:?\s*(.+)',
            'warning': r'WARNING:?\s*(.+)',
            'memory_usage': r'Memory:\s*(\d+\.?\d*)\s*(MB|GB)',
            'gpu_usage': r'GPU:\s*(\d+\.?\d*)%'
        }
        
        # Отслеживание файлов
        self.monitored_files = {}
        self.file_positions = {}
        
    def _init_database(self):
        """Инициализация базы данных SQLite"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Таблица системных метрик
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME,
                        cpu_usage REAL,
                        memory_usage REAL,
                        memory_available REAL,
                        disk_usage REAL,
                        disk_free REAL,
                        gpu_usage REAL,
                        gpu_memory REAL,
                        process_count INTEGER
                    )
                ''')
                
                # Таблица метрик обучения
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS training_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME,
                        session_id TEXT,
                        stage TEXT,
                        progress REAL,
                        documents_processed INTEGER,
                        chunks_generated INTEGER,
                        embeddings_created INTEGER,
                        processing_speed REAL,
                        throughput REAL,
                        error_rate REAL,
                        memory_peak REAL
                    )
                ''')
                
                # Таблица метрик документов
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS document_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME,
                        document_id TEXT,
                        filename TEXT,
                        file_size INTEGER,
                        processing_time REAL,
                        chunks_count INTEGER,
                        embeddings_count INTEGER,
                        quality_score REAL,
                        language TEXT,
                        status TEXT,
                        errors TEXT
                    )
                ''')
                
                # Таблица ошибок
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS error_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME,
                        error_type TEXT,
                        error_message TEXT,
                        severity TEXT,
                        component TEXT,
                        document_id TEXT,
                        stack_trace TEXT,
                        context TEXT
                    )
                ''')
                
                # Индексы для быстрого поиска
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_timestamp ON system_metrics(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_training_timestamp ON training_metrics(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_document_timestamp ON document_metrics(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_error_timestamp ON error_metrics(timestamp)')
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            
    def start_collection(self):
        """Запуск сбора метрик"""
        if self.is_running:
            logger.warning("Metrics collection is already running")
            return
            
        self.is_running = True
        self.collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self.collection_thread.start()
        
        logger.info("Metrics collection started")
        
    def stop_collection(self):
        """Остановка сбора метрик"""
        self.is_running = False
        
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
            
        logger.info("Metrics collection stopped")
        
    def _collection_loop(self):
        """Основной цикл сбора метрик"""
        while self.is_running:
            try:
                # Собираем системные метрики
                self._collect_system_metrics()
                
                # Анализируем логи
                self._analyze_log_files()
                
                # Сохраняем метрики в базу данных
                self._persist_metrics()
                
                # Очищаем старые данные
                self._cleanup_old_data()
                
                time.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
                time.sleep(self.collection_interval)
                
    def _collect_system_metrics(self):
        """Сбор системных метрик"""
        try:
            # CPU и память
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Диск
            disk_usage = psutil.disk_usage('/')
            if sys.platform == "win32":
                # Для Windows проверяем диск C: и I:
                try:
                    disk_usage = psutil.disk_usage('C:')
                except:
                    disk_usage = psutil.disk_usage('/')
            
            # GPU (если доступно)
            gpu_usage = None
            gpu_memory = None
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    gpu_usage = gpu.load * 100
                    gpu_memory = gpu.memoryUtil * 100
            except ImportError:
                pass
            
            # Количество процессов
            process_count = len(psutil.pids())
            
            # Создаем метрику
            metric = SystemMetric(
                timestamp=datetime.now(),
                cpu_usage=cpu_percent,
                memory_usage=memory.percent,
                memory_available=memory.available / 1024**3,  # GB
                disk_usage=disk_usage.used / disk_usage.total * 100,
                disk_free=disk_usage.free / 1024**3,  # GB
                gpu_usage=gpu_usage,
                gpu_memory=gpu_memory,
                process_count=process_count
            )
            
            # Добавляем в кэш
            self.metrics_cache[MetricType.SYSTEM].append(metric)
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            
    def _analyze_log_files(self):
        """Анализ лог-файлов для извлечения метрик"""
        for log_dir in self.log_paths:
            log_path = Path(log_dir)
            if not log_path.exists():
                continue
                
            # Ищем лог-файлы
            for log_file in log_path.glob("*.log"):
                self._analyze_log_file(log_file)
                
            # Ищем файлы processed_files.json
            for json_file in log_path.glob("**/processed_files.json"):
                self._analyze_processed_files(json_file)
                
    def _analyze_log_file(self, log_file: Path):
        """Анализ отдельного лог-файла"""
        try:
            # Получаем позицию в файле
            file_key = str(log_file)
            current_pos = self.file_positions.get(file_key, 0)
            
            # Проверяем, изменился ли файл
            file_stat = log_file.stat()
            if file_stat.st_size < current_pos:
                # Файл был пересоздан
                current_pos = 0
                
            # Читаем новые строки
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(current_pos)
                new_lines = f.readlines()
                new_pos = f.tell()
                
            # Обновляем позицию
            self.file_positions[file_key] = new_pos
            
            # Анализируем новые строки
            for line in new_lines:
                self._parse_log_line(line.strip(), log_file.name)
                
        except Exception as e:
            logger.error(f"Error analyzing log file {log_file}: {e}")
            
    def _parse_log_line(self, line: str, source_file: str):
        """Парсинг строки лога"""
        if not line:
            return
            
        timestamp = datetime.now()
        
        # Извлекаем timestamp из строки если есть
        timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2}[\s\T]\d{2}:\d{2}:\d{2})', line)
        if timestamp_match:
            try:
                timestamp = datetime.fromisoformat(timestamp_match.group(1).replace('T', ' '))
            except:
                pass
        
        # Проверяем паттерны
        for pattern_name, pattern in self.log_patterns.items():
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                self._process_log_match(pattern_name, match, line, timestamp, source_file)
                
    def _process_log_match(self, pattern_name: str, match: re.Match, 
                          line: str, timestamp: datetime, source_file: str):
        """Обработка найденного паттерна в логе"""
        try:
            if pattern_name == 'error':
                error_metric = ErrorMetric(
                    timestamp=timestamp,
                    error_type="LogError",
                    error_message=match.group(1),
                    severity=MetricSeverity.ERROR,
                    component=source_file,
                    context={'line': line}
                )
                self.metrics_cache[MetricType.ERROR].append(error_metric)
                
            elif pattern_name == 'warning':
                error_metric = ErrorMetric(
                    timestamp=timestamp,
                    error_type="LogWarning",
                    error_message=match.group(1),
                    severity=MetricSeverity.WARNING,
                    component=source_file,
                    context={'line': line}
                )
                self.metrics_cache[MetricType.ERROR].append(error_metric)
                
            elif pattern_name == 'training_progress':
                # Создаем метрику обучения (упрощенную)
                progress = float(match.group(1))
                training_metric = TrainingMetric(
                    timestamp=timestamp,
                    session_id=self._generate_session_id(source_file),
                    stage="training",
                    progress=progress,
                    documents_processed=0,
                    chunks_generated=0,
                    embeddings_created=0,
                    processing_speed=0.0,
                    throughput=0.0,
                    error_rate=0.0,
                    memory_peak=0.0
                )
                self.metrics_cache[MetricType.TRAINING].append(training_metric)
                
        except Exception as e:
            logger.error(f"Error processing log match {pattern_name}: {e}")
            
    def _analyze_processed_files(self, json_file: Path):
        """Анализ файла processed_files.json"""
        try:
            # Проверяем, изменился ли файл
            file_key = str(json_file)
            file_stat = json_file.stat()
            
            if file_key in self.monitored_files:
                if self.monitored_files[file_key] == file_stat.st_mtime:
                    return  # Файл не изменился
                    
            self.monitored_files[file_key] = file_stat.st_mtime
            
            # Читаем и анализируем JSON
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Извлекаем метрики документов
            for doc_info in data.get('processed_documents', []):
                self._create_document_metric(doc_info)
                
        except Exception as e:
            logger.error(f"Error analyzing processed files {json_file}: {e}")
            
    def _create_document_metric(self, doc_info: Dict[str, Any]):
        """Создание метрики документа"""
        try:
            metric = DocumentMetric(
                timestamp=datetime.now(),
                document_id=doc_info.get('id', ''),
                filename=doc_info.get('filename', ''),
                file_size=doc_info.get('size', 0),
                processing_time=doc_info.get('processing_time', 0.0),
                chunks_count=doc_info.get('chunks', 0),
                embeddings_count=doc_info.get('embeddings', 0),
                quality_score=doc_info.get('quality', 0.0),
                language=doc_info.get('language', 'unknown'),
                status=doc_info.get('status', 'unknown'),
                errors=doc_info.get('errors', [])
            )
            
            self.metrics_cache[MetricType.DOCUMENT].append(metric)
            
        except Exception as e:
            logger.error(f"Error creating document metric: {e}")
            
    def _generate_session_id(self, source: str) -> str:
        """Генерация ID сессии обучения"""
        # Простая генерация на основе источника и времени
        session_data = f"{source}_{datetime.now().strftime('%Y%m%d')}"
        return hashlib.md5(session_data.encode()).hexdigest()[:8]
        
    def _persist_metrics(self):
        """Сохранение метрик в базу данных"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Сохраняем системные метрики
                system_metrics = list(self.metrics_cache[MetricType.SYSTEM])
                if system_metrics:
                    for metric in system_metrics:
                        cursor.execute('''
                            INSERT INTO system_metrics 
                            (timestamp, cpu_usage, memory_usage, memory_available, 
                             disk_usage, disk_free, gpu_usage, gpu_memory, process_count)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            metric.timestamp, metric.cpu_usage, metric.memory_usage,
                            metric.memory_available, metric.disk_usage, metric.disk_free,
                            metric.gpu_usage, metric.gpu_memory, metric.process_count
                        ))
                    
                    # Очищаем кэш после сохранения
                    self.metrics_cache[MetricType.SYSTEM].clear()
                
                # Сохраняем метрики обучения
                training_metrics = list(self.metrics_cache[MetricType.TRAINING])
                if training_metrics:
                    for metric in training_metrics:
                        cursor.execute('''
                            INSERT INTO training_metrics 
                            (timestamp, session_id, stage, progress, documents_processed,
                             chunks_generated, embeddings_created, processing_speed,
                             throughput, error_rate, memory_peak)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            metric.timestamp, metric.session_id, metric.stage,
                            metric.progress, metric.documents_processed,
                            metric.chunks_generated, metric.embeddings_created,
                            metric.processing_speed, metric.throughput,
                            metric.error_rate, metric.memory_peak
                        ))
                    
                    self.metrics_cache[MetricType.TRAINING].clear()
                
                # Сохраняем метрики документов
                document_metrics = list(self.metrics_cache[MetricType.DOCUMENT])
                if document_metrics:
                    for metric in document_metrics:
                        cursor.execute('''
                            INSERT INTO document_metrics 
                            (timestamp, document_id, filename, file_size, processing_time,
                             chunks_count, embeddings_count, quality_score, language,
                             status, errors)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            metric.timestamp, metric.document_id, metric.filename,
                            metric.file_size, metric.processing_time, metric.chunks_count,
                            metric.embeddings_count, metric.quality_score,
                            metric.language, metric.status, json.dumps(metric.errors)
                        ))
                    
                    self.metrics_cache[MetricType.DOCUMENT].clear()
                
                # Сохраняем ошибки
                error_metrics = list(self.metrics_cache[MetricType.ERROR])
                if error_metrics:
                    for metric in error_metrics:
                        cursor.execute('''
                            INSERT INTO error_metrics 
                            (timestamp, error_type, error_message, severity, component,
                             document_id, stack_trace, context)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            metric.timestamp, metric.error_type, metric.error_message,
                            metric.severity.value, metric.component, metric.document_id,
                            metric.stack_trace, json.dumps(metric.context)
                        ))
                    
                    self.metrics_cache[MetricType.ERROR].clear()
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error persisting metrics: {e}")
            
    def _cleanup_old_data(self):
        """Очистка старых данных"""
        try:
            # Удаляем данные старше 30 дней
            cutoff_date = datetime.now() - timedelta(days=30)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM system_metrics WHERE timestamp < ?', (cutoff_date,))
                cursor.execute('DELETE FROM training_metrics WHERE timestamp < ?', (cutoff_date,))
                cursor.execute('DELETE FROM document_metrics WHERE timestamp < ?', (cutoff_date,))
                cursor.execute('DELETE FROM error_metrics WHERE timestamp < ?', (cutoff_date,))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            
    def get_metrics(self, metric_type: MetricType, 
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None,
                   limit: int = 1000) -> List[Dict[str, Any]]:
        """Получение метрик из базы данных"""
        try:
            table_map = {
                MetricType.SYSTEM: 'system_metrics',
                MetricType.TRAINING: 'training_metrics',
                MetricType.DOCUMENT: 'document_metrics',
                MetricType.ERROR: 'error_metrics'
            }
            
            table_name = table_map.get(metric_type)
            if not table_name:
                return []
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # Для получения словарей
                cursor = conn.cursor()
                
                query = f'SELECT * FROM {table_name}'
                params = []
                
                conditions = []
                if start_time:
                    conditions.append('timestamp >= ?')
                    params.append(start_time)
                    
                if end_time:
                    conditions.append('timestamp <= ?')
                    params.append(end_time)
                
                if conditions:
                    query += ' WHERE ' + ' AND '.join(conditions)
                
                query += ' ORDER BY timestamp DESC LIMIT ?'
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return []
            
    def get_latest_metrics(self) -> Dict[str, Any]:
        """Получение последних метрик"""
        try:
            result = {}
            
            # Последние системные метрики
            system_metrics = self.get_metrics(MetricType.SYSTEM, limit=1)
            if system_metrics:
                result['system'] = system_metrics[0]
            
            # Последние метрики обучения
            training_metrics = self.get_metrics(MetricType.TRAINING, limit=1)
            if training_metrics:
                result['training'] = training_metrics[0]
            
            # Статистика документов за последний час
            one_hour_ago = datetime.now() - timedelta(hours=1)
            document_metrics = self.get_metrics(
                MetricType.DOCUMENT, 
                start_time=one_hour_ago
            )
            
            if document_metrics:
                result['documents'] = {
                    'total_processed': len(document_metrics),
                    'average_processing_time': sum(d.get('processing_time', 0) for d in document_metrics) / len(document_metrics),
                    'total_chunks': sum(d.get('chunks_count', 0) for d in document_metrics),
                    'average_quality': sum(d.get('quality_score', 0) for d in document_metrics) / len(document_metrics)
                }
            
            # Ошибки за последний час
            error_metrics = self.get_metrics(
                MetricType.ERROR,
                start_time=one_hour_ago
            )
            
            if error_metrics:
                result['errors'] = {
                    'total_errors': len(error_metrics),
                    'error_types': list(set(e.get('error_type', '') for e in error_metrics)),
                    'critical_errors': len([e for e in error_metrics if e.get('severity') == 'critical'])
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting latest metrics: {e}")
            return {}


# Функции для интеграции с унифицированной системой
def start_metrics_collection(**kwargs) -> Dict[str, Any]:
    """Запуск сбора метрик"""
    try:
        collector = NonIntrusiveMetricsCollector()
        collector.start_collection()
        
        return {
            'status': 'success',
            'message': 'Metrics collection started',
            'collection_interval': collector.collection_interval
        }
        
    except Exception as e:
        logger.error(f"Error starting metrics collection: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }

def get_current_metrics(**kwargs) -> Dict[str, Any]:
    """Получение текущих метрик"""
    try:
        collector = NonIntrusiveMetricsCollector()
        metrics = collector.get_latest_metrics()
        
        return {
            'status': 'success',
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting current metrics: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }

def get_metrics_history(metric_type: str, hours: int = 24, **kwargs) -> Dict[str, Any]:
    """Получение истории метрик"""
    try:
        collector = NonIntrusiveMetricsCollector()
        
        # Преобразуем строку в enum
        try:
            metric_type_enum = MetricType(metric_type.lower())
        except ValueError:
            return {
                'status': 'error',
                'error': f'Invalid metric type: {metric_type}'
            }
        
        start_time = datetime.now() - timedelta(hours=hours)
        metrics = collector.get_metrics(
            metric_type=metric_type_enum,
            start_time=start_time,
            limit=1000
        )
        
        return {
            'status': 'success',
            'metric_type': metric_type,
            'period_hours': hours,
            'total_records': len(metrics),
            'metrics': metrics
        }
        
    except Exception as e:
        logger.error(f"Error getting metrics history: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }

# Регистрация в унифицированной системе инструментов
METRICS_COLLECTION_TOOLS = {
    'start_metrics_collection': {
        'function': start_metrics_collection,
        'description': 'Запуск неинтрузивного сбора метрик системы и обучения',
        'category': 'monitoring',
        'ui_placement': 'tools',
        'parameters': {}
    },
    'get_current_metrics': {
        'function': get_current_metrics,
        'description': 'Получение текущих метрик системы',
        'category': 'monitoring',
        'ui_placement': 'dashboard',
        'parameters': {}
    },
    'get_metrics_history': {
        'function': get_metrics_history,
        'description': 'Получение истории метрик за указанный период',
        'category': 'monitoring',
        'ui_placement': 'tools',
        'parameters': {
            'metric_type': 'str - Тип метрик (system, training, document, error)',
            'hours': 'int - Количество часов истории (по умолчанию 24)'
        }
    }
}

if __name__ == "__main__":
    # Тестирование сборщика метрик
    collector = NonIntrusiveMetricsCollector()
    
    print("Starting metrics collection...")
    collector.start_collection()
    
    try:
        # Даем поработать 30 секунд
        time.sleep(30)
        
        # Получаем последние метрики
        print("\nLatest metrics:")
        latest = collector.get_latest_metrics()
        print(json.dumps(latest, indent=2, default=str))
        
        # Получаем системные метрики за последний час
        print("\nSystem metrics (last hour):")
        system_metrics = collector.get_metrics(MetricType.SYSTEM, limit=10)
        for metric in system_metrics[:3]:  # Показываем первые 3
            print(f"  {metric['timestamp']}: CPU {metric['cpu_usage']:.1f}%, Memory {metric['memory_usage']:.1f}%")
        
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        collector.stop_collection()
        print("Metrics collection stopped")