# namespace:ai
from typing import Any, Dict, List
import time
import os
import sys
from pathlib import Path
from core.tools.base_tool import ToolManifest, ToolInterface, ToolParam, ToolParamType

# Создаем Pydantic модели для универсального представления
coordinator_interface = ToolInterface(
    purpose="Профессиональное обучение RAG системы с полным пайплайном обработки документов, извлечения структуры, генерации эмбеддингов и сохранения в векторную и графовую базы данных",
    input_requirements={
        "base_dir": ToolParam(
            name="base_dir",
            type=ToolParamType.STRING,
            required=False,
            description="Базовая директория с документами для обработки"
        ),
        "max_files": ToolParam(
            name="max_files",
            type=ToolParamType.NUMBER,
            required=False,
            description="Максимальное количество файлов для обработки"
        ),
        "force_cuda": ToolParam(
            name="force_cuda",
            type=ToolParamType.BOOLEAN,
            required=False,
            default=True,
            description="Принудительное использование CUDA для SBERT"
        ),
        "reset_databases": ToolParam(
            name="reset_databases",
            type=ToolParamType.BOOLEAN,
            required=False,
            default=False,
            description="Сбросить базы данных перед обучением"
        ),
        "include_file_organization": ToolParam(
            name="include_file_organization",
            type=ToolParamType.BOOLEAN,
            required=False,
            default=True,
            description="Включить организацию файлов по категориям"
        ),
        "chunking_strategy": ToolParam(
            name="chunking_strategy",
            type=ToolParamType.ENUM,
            required=False,
            default="smart",
            description="Стратегия разбиения на чанки",
            enum=[
                {"value": "smart", "label": "Умное разбиение (1 пункт = 1 чанк)"},
                {"value": "fixed", "label": "Фиксированный размер"},
                {"value": "semantic", "label": "Семантическое разбиение"}
            ]
        ),
        "processing_mode": ToolParam(
            name="processing_mode",
            type=ToolParamType.ENUM,
            required=False,
            default="comprehensive",
            description="Режим обработки",
            enum=[
                {"value": "fast", "label": "Быстрая обработка"},
                {"value": "comprehensive", "label": "Комплексная обработка"},
                {"value": "expert", "label": "Экспертная обработка"}
            ]
        )
    },
    execution_flow=[
        "1. Инициализация RAG тренера с CUDA поддержкой",
        "2. Подключение к Qdrant и Neo4j базам данных",
        "3. Сканирование директории с документами",
        "4. Валидация и проверка дубликатов файлов",
        "5. Извлечение текста из документов (PDF, DOCX, Excel)",
        "6. Определение типа документов и структуры",
        "7. Анализ структуры с помощью SBERT",
        "8. Извлечение последовательностей работ",
        "9. Сохранение зависимостей в Neo4j",
        "10. Умное разбиение на чанки",
        "11. Генерация эмбеддингов и сохранение в Qdrant",
        "12. Организация файлов по категориям",
        "13. Генерация отчета о результатах"
    ],
    output_format={
        "structure": {
            "status": "success/error",
            "data": {
                "training_summary": "object - сводка по обучению",
                "files_processed": "number - количество обработанных файлов",
                "chunks_created": "number - количество созданных чанков",
                "works_extracted": "number - количество извлеченных работ",
                "dependencies_saved": "number - количество сохраненных зависимостей",
                "file_path": "string - путь к отчету"
            },
            "execution_time": "float in seconds"
        },
        "result_fields": {
            "training_summary": "object - детальная статистика обучения",
            "files_processed": "number - количество успешно обработанных файлов",
            "chunks_created": "number - количество созданных векторных чанков",
            "works_extracted": "number - количество извлеченных работ",
            "dependencies_saved": "number - количество сохраненных зависимостей",
            "file_path": "string - путь к детальному отчету"
        }
    },
    usage_guidelines={
        "for_coordinator": [
            "Используйте для обучения RAG системы на новых документах",
            "Указывайте директорию с документами для обработки",
            "Настраивайте режим обработки в зависимости от требований",
            "Используйте CUDA для ускорения обработки"
        ],
        "for_models": [
            "Инструмент возвращает детальную статистику обучения",
            "Используйте training_summary для анализа результатов",
            "Проверяйте количество обработанных файлов и чанков",
            "Результат содержит все необходимые метрики качества"
        ]
    },
    integration_notes={
        "dependencies": ["Qdrant", "Neo4j", "SBERT", "CUDA", "File system"],
        "performance": "Длительная операция: 10-60 минут в зависимости от объема",
        "reliability": "Очень высокая - проверенный пайплайн обработки",
        "scalability": "Поддерживает обработку тысяч документов"
    }
)

manifest = ToolManifest(
    name="enterprise_rag_trainer",
    version="1.0.0",
    title="🧠 Enterprise RAG Trainer",
    description="Профессиональное обучение RAG системы с полным пайплайном обработки документов, извлечения структуры, генерации эмбеддингов и сохранения в векторную и графовую базы данных.",
    category="ai",
    ui_placement="dashboard",
    enabled=True,
    system=True,  # Системный инструмент
    entrypoint="tools.ai.enterprise_rag_trainer:execute",
    params=[
        ToolParam(
            name="base_dir",
            type=ToolParamType.STRING,
            required=False,
            description="Базовая директория с документами",
            ui={
                "placeholder": "Укажите путь к папке с документами или оставьте пустым для I:/docs/downloaded"
            }
        ),
        ToolParam(
            name="max_files",
            type=ToolParamType.NUMBER,
            required=False,
            description="Максимальное количество файлов",
            ui={
                "min": 1,
                "max": 10000,
                "step": 1
            }
        ),
        ToolParam(
            name="force_cuda",
            type=ToolParamType.BOOLEAN,
            required=False,
            default=True,
            description="Принудительное использование CUDA",
            ui={
                "switch": True
            }
        ),
        ToolParam(
            name="reset_databases",
            type=ToolParamType.BOOLEAN,
            required=False,
            default=False,
            description="Сбросить базы данных",
            ui={
                "switch": True
            }
        ),
        ToolParam(
            name="include_file_organization",
            type=ToolParamType.BOOLEAN,
            required=False,
            default=True,
            description="Включить организацию файлов",
            ui={
                "switch": True
            }
        ),
        ToolParam(
            name="chunking_strategy",
            type=ToolParamType.ENUM,
            required=False,
            default="smart",
            description="Стратегия разбиения на чанки",
            enum=[
                {"value": "smart", "label": "Умное разбиение (1 пункт = 1 чанк)"},
                {"value": "fixed", "label": "Фиксированный размер"},
                {"value": "semantic", "label": "Семантическое разбиение"}
            ]
        ),
        ToolParam(
            name="processing_mode",
            type=ToolParamType.ENUM,
            required=False,
            default="comprehensive",
            description="Режим обработки",
            enum=[
                {"value": "fast", "label": "Быстрая обработка"},
                {"value": "comprehensive", "label": "Комплексная обработка"},
                {"value": "expert", "label": "Экспертная обработка"}
            ]
        )
    ],
    outputs=["training_summary", "files_processed", "chunks_created", "works_extracted", "dependencies_saved"],
    permissions=["read:filesystem", "write:qdrant", "write:neo4j", "read:files"],
    tags=["rag", "training", "ai", "enterprise", "system"],
    result_display={
        "type": "training_report",
        "title": "Отчет о обучении RAG системы",
        "description": "Детальная статистика процесса обучения",
        "features": {
            "exportable": True,
            "printable": True,
            "interactive": True,
            "charts": True
        }
    },
    documentation={
        "examples": [
            {
                "title": "Быстрое обучение",
                "base_dir": "I:/docs/downloaded",
                "max_files": 100,
                "processing_mode": "fast",
                "force_cuda": True
            },
            {
                "title": "Полное обучение",
                "base_dir": "I:/docs/downloaded",
                "processing_mode": "comprehensive",
                "include_file_organization": True
            }
        ],
        "tips": [
            "Используйте CUDA для ускорения обработки",
            "Начинайте с небольшого количества файлов для тестирования",
            "Проверяйте доступность баз данных перед запуском"
        ]
    },
    coordinator_interface=coordinator_interface
)

def execute(**kwargs) -> Dict[str, Any]:
    """Execute enterprise-level RAG training with full pipeline."""
    start_time = time.time()
    
    try:
        # Parse parameters with defaults
        base_dir = kwargs.get('base_dir', 'I:/docs/downloaded')
        max_files = kwargs.get('max_files', None)
        force_cuda = kwargs.get('force_cuda', True)
        reset_databases = kwargs.get('reset_databases', False)
        include_file_organization = kwargs.get('include_file_organization', True)
        chunking_strategy = kwargs.get('chunking_strategy', 'smart')
        processing_mode = kwargs.get('processing_mode', 'comprehensive')
        
        # Set environment variables
        if force_cuda:
            os.environ['FORCE_CUDA'] = '1'
        
        # Reset databases if requested
        if reset_databases:
            _reset_rag_databases()
        
        # Import and initialize trainer
        try:
            from enterprise_rag_trainer_full import EnterpriseRAGTrainer
            trainer = EnterpriseRAGTrainer(base_dir=base_dir)
        except ImportError as e:
            return {
                'status': 'error',
                'error': f'Не удалось импортировать RAG тренер: {str(e)}',
                'execution_time': time.time() - start_time
            }
        
        # Configure trainer based on parameters
        if max_files:
            trainer.max_files = max_files
        
        # Set chunking strategy
        if chunking_strategy == 'smart':
            trainer.chunking_strategy = 'hierarchical'
        elif chunking_strategy == 'fixed':
            trainer.chunking_strategy = 'fixed_size'
        else:
            trainer.chunking_strategy = 'semantic'
        
        # Set processing mode
        if processing_mode == 'fast':
            trainer.quality_threshold = 0.7
            trainer.enable_ocr = False
        elif processing_mode == 'expert':
            trainer.quality_threshold = 0.9
            trainer.enable_ocr = True
        else:  # comprehensive
            trainer.quality_threshold = 0.8
            trainer.enable_ocr = True
        
        # Start training
        logger.info(f"🚀 Starting RAG training with mode: {processing_mode}")
        training_start_time = time.time()
        
        try:
            trainer.train(max_files=max_files)
            training_successful = True
        except Exception as training_error:
            logger.error(f"Training failed: {training_error}")
            training_successful = False
        
        training_time = time.time() - training_start_time
        
        # Generate training summary
        training_summary = _generate_training_summary(trainer, training_successful, training_time)
        
        # Generate report file
        report_path = _generate_training_report(trainer, training_summary, base_dir)
        
        # Generate metadata
        metadata = {
            'base_dir': base_dir,
            'max_files': max_files,
            'force_cuda': force_cuda,
            'reset_databases': reset_databases,
            'chunking_strategy': chunking_strategy,
            'processing_mode': processing_mode,
            'training_successful': training_successful,
            'trained_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'report_path': report_path
        }
        
        execution_time = time.time() - start_time
        
        return {
            'status': 'success' if training_successful else 'error',
            'data': {
                'training_summary': training_summary,
                'files_processed': training_summary.get('files_processed', 0),
                'chunks_created': training_summary.get('chunks_created', 0),
                'works_extracted': training_summary.get('works_extracted', 0),
                'dependencies_saved': training_summary.get('dependencies_saved', 0),
                'file_path': report_path,
                'metadata': metadata
            },
            'execution_time': execution_time,
            'result_type': 'training_report',
            'result_title': f'🧠 Обучение RAG системы: {training_summary.get("files_processed", 0)} файлов',
            'result_table': _create_training_table(training_summary),
            'metadata': metadata
        }
        
    except Exception as e:
        return { 
            'status': 'error', 
            'error': str(e),
            'execution_time': time.time() - start_time
        }


def _reset_rag_databases():
    """Reset RAG databases before training."""
    try:
        from quick_reset_rag import main as reset_main
        reset_main()
        logger.info("✅ RAG databases reset successfully")
    except Exception as e:
        logger.warning(f"⚠️ Failed to reset databases: {e}")


def _generate_training_summary(trainer, training_successful: bool, training_time: float) -> Dict[str, Any]:
    """Generate comprehensive training summary."""
    try:
        stats = getattr(trainer, 'stats', {})
        
        return {
            'training_successful': training_successful,
            'files_processed': stats.get('files_processed', 0),
            'files_failed': stats.get('files_failed', 0),
            'total_chunks': stats.get('total_chunks', 0),
            'total_works': stats.get('total_works', 0),
            'training_time': training_time,
            'files_per_minute': stats.get('files_processed', 0) / (training_time / 60) if training_time > 0 else 0,
            'chunks_per_file': stats.get('total_chunks', 0) / stats.get('files_processed', 1) if stats.get('files_processed', 0) > 0 else 0,
            'works_per_file': stats.get('total_works', 0) / stats.get('files_processed', 1) if stats.get('files_processed', 0) > 0 else 0,
            'success_rate': (stats.get('files_processed', 0) / (stats.get('files_processed', 0) + stats.get('files_failed', 0))) * 100 if (stats.get('files_processed', 0) + stats.get('files_failed', 0)) > 0 else 0,
            'cuda_enabled': os.environ.get('FORCE_CUDA') == '1',
            'databases_status': _check_databases_status()
        }
    except Exception as e:
        logger.error(f"Error generating training summary: {e}")
        return {
            'training_successful': training_successful,
            'files_processed': 0,
            'files_failed': 0,
            'total_chunks': 0,
            'total_works': 0,
            'training_time': training_time,
            'error': str(e)
        }


def _check_databases_status() -> Dict[str, Any]:
    """Check status of RAG databases."""
    status = {'qdrant': False, 'neo4j': False}
    
    try:
        # Check Qdrant
        from qdrant_client import QdrantClient
        client = QdrantClient(host='localhost', port=6333)
        collections = client.get_collections()
        status['qdrant'] = True
    except Exception as e:
        logger.warning(f"Qdrant not available: {e}")
    
    try:
        # Check Neo4j
        import neo4j
        driver = neo4j.GraphDatabase.driver('neo4j://127.0.0.1:7687', auth=('neo4j', 'neopassword'))
        with driver.session() as session:
            session.run("RETURN 1")
        driver.close()
        status['neo4j'] = True
    except Exception as e:
        logger.warning(f"Neo4j not available: {e}")
    
    return status


def _generate_training_report(trainer, training_summary: Dict[str, Any], base_dir: str) -> str:
    """Generate detailed training report."""
    try:
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        report_dir = Path(base_dir) / "reports"
        report_dir.mkdir(exist_ok=True)
        
        report_path = report_dir / f"rag_training_report_{timestamp}.json"
        
        report_data = {
            'training_summary': training_summary,
            'trainer_stats': getattr(trainer, 'stats', {}),
            'configuration': {
                'base_dir': base_dir,
                'cuda_enabled': os.environ.get('FORCE_CUDA') == '1',
                'chunking_strategy': getattr(trainer, 'chunking_strategy', 'smart'),
                'quality_threshold': getattr(trainer, 'quality_threshold', 0.8)
            },
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        import json
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 Training report saved: {report_path}")
        return str(report_path)
        
    except Exception as e:
        logger.error(f"Error generating training report: {e}")
        return ""


def _create_training_table(training_summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Create training results table."""
    table_data = [
        {
            'metric': 'Файлов обработано',
            'value': training_summary.get('files_processed', 0),
            'status': 'success'
        },
        {
            'metric': 'Файлов с ошибками',
            'value': training_summary.get('files_failed', 0),
            'status': 'warning' if training_summary.get('files_failed', 0) > 0 else 'success'
        },
        {
            'metric': 'Чанков создано',
            'value': training_summary.get('total_chunks', 0),
            'status': 'info'
        },
        {
            'metric': 'Работ извлечено',
            'value': training_summary.get('total_works', 0),
            'status': 'info'
        },
        {
            'metric': 'Время обучения',
            'value': f"{training_summary.get('training_time', 0):.1f} сек",
            'status': 'info'
        },
        {
            'metric': 'Скорость обработки',
            'value': f"{training_summary.get('files_per_minute', 0):.1f} файлов/мин",
            'status': 'info'
        },
        {
            'metric': 'Процент успеха',
            'value': f"{training_summary.get('success_rate', 0):.1f}%",
            'status': 'success' if training_summary.get('success_rate', 0) > 80 else 'warning'
        }
    ]
    
    return table_data
