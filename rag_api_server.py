"""
🌐 API Server для RAG-тренера
Предоставляет REST API для фронтенда Bldr
"""

import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Optional
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import traceback

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Создаем Flask приложение
app = Flask(__name__)
CORS(app)  # Разрешаем CORS для фронтенда

# Глобальная переменная для RAG тренера
rag_trainer = None

def initialize_rag_trainer():
    """Инициализация RAG тренера"""
    global rag_trainer
    
    try:
        from enterprise_rag_trainer_full import EnterpriseRAGTrainer
        
        logger.info("🔄 Инициализация RAG тренера...")
        rag_trainer = EnterpriseRAGTrainer()
        logger.info("✅ RAG тренер инициализирован")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации RAG тренера: {e}")
        return False

@app.route('/api/health', methods=['GET'])
def health_check():
    """Проверка здоровья API"""
    return jsonify({
        "status": "healthy",
        "rag_trainer_loaded": rag_trainer is not None,
        "timestamp": time.time()
    })

@app.route('/api/analyze-file', methods=['POST'])
def analyze_single_file():
    """
    API для анализа одного файла
    POST /api/analyze-file
    Body: {"file_path": "/path/to/file.pdf", "save_to_db": false}
    """
    try:
        if not rag_trainer:
            return jsonify({"error": "RAG trainer not initialized"}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        file_path = data.get('file_path')
        save_to_db = data.get('save_to_db', False)
        
        if not file_path:
            return jsonify({"error": "file_path is required"}), 400
        
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404
        
        logger.info(f"🔍 API: Analyzing file: {os.path.basename(file_path)}")
        
        # Обрабатываем файл
        result = rag_trainer.process_single_file_ad_hoc(file_path, save_to_db=save_to_db)
        
        if result and result.get('success'):
            return jsonify({
                "success": True,
                "data": result,
                "message": "File analyzed successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get('error', 'Analysis failed') if result else 'No result'
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Error in analyze_single_file: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/analyze-project', methods=['POST'])
def analyze_project():
    """
    API для анализа проекта (несколько файлов)
    POST /api/analyze-project
    Body: {"file_paths": ["/path/to/file1.pdf", "/path/to/file2.pdf"]}
    """
    try:
        if not rag_trainer:
            return jsonify({"error": "RAG trainer not initialized"}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        file_paths = data.get('file_paths', [])
        
        if not file_paths:
            return jsonify({"error": "file_paths is required"}), 400
        
        # Проверяем существование файлов
        valid_files = []
        for file_path in file_paths:
            if os.path.exists(file_path):
                valid_files.append(file_path)
            else:
                logger.warning(f"⚠️ File not found: {file_path}")
        
        if not valid_files:
            return jsonify({"error": "No valid files found"}), 404
        
        logger.info(f"📊 API: Analyzing project with {len(valid_files)} files")
        
        # Анализируем проект
        results = rag_trainer.analyze_project_context(valid_files)
        
        return jsonify({
            "success": True,
            "data": results,
            "message": f"Project analyzed successfully ({len(results)} files)"
        })
        
    except Exception as e:
        logger.error(f"❌ Error in analyze_project: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/train-file', methods=['POST'])
def train_single_file():
    """
    API для дообучения на одном файле
    POST /api/train-file
    Body: {"file_path": "/path/to/file.pdf"}
    """
    try:
        if not rag_trainer:
            return jsonify({"error": "RAG trainer not initialized"}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        file_path = data.get('file_path')
        
        if not file_path:
            return jsonify({"error": "file_path is required"}), 400
        
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404
        
        logger.info(f"🎓 API: Training on file: {os.path.basename(file_path)}")
        
        # Дообучаем на файле (с сохранением в БД)
        result = rag_trainer.process_single_file_ad_hoc(file_path, save_to_db=True)
        
        if result and result.get('success'):
            return jsonify({
                "success": True,
                "data": result,
                "message": "File trained successfully and saved to database"
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get('error', 'Training failed') if result else 'No result'
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Error in train_single_file: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/get-file-info', methods=['GET'])
def get_file_info():
    """
    API для получения информации о файле
    GET /api/get-file-info?file_path=/path/to/file.pdf
    """
    try:
        file_path = request.args.get('file_path')
        
        if not file_path:
            return jsonify({"error": "file_path parameter is required"}), 400
        
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404
        
        # Получаем базовую информацию о файле
        file_info = {
            "file_name": os.path.basename(file_path),
            "file_path": file_path,
            "file_size": os.path.getsize(file_path),
            "file_extension": Path(file_path).suffix,
            "exists": True
        }
        
        return jsonify({
            "success": True,
            "data": file_info
        })
        
    except Exception as e:
        logger.error(f"❌ Error in get_file_info: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/list-files', methods=['GET'])
def list_files():
    """
    API для получения списка файлов в директории
    GET /api/list-files?directory=/path/to/directory&extension=.pdf
    """
    try:
        directory = request.args.get('directory', 'I:/docs/downloaded')
        extension = request.args.get('extension', '.pdf')
        
        if not os.path.exists(directory):
            return jsonify({"error": "Directory not found"}), 404
        
        files = []
        for root, dirs, filenames in os.walk(directory):
            for filename in filenames:
                if filename.endswith(extension):
                    file_path = os.path.join(root, filename)
                    files.append({
                        "file_name": filename,
                        "file_path": file_path,
                        "file_size": os.path.getsize(file_path),
                        "directory": root
                    })
        
        return jsonify({
            "success": True,
            "data": {
                "files": files,
                "count": len(files),
                "directory": directory,
                "extension": extension
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error in list_files: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

def main():
    """Запуск API сервера"""
    logger.info("🚀 Запуск RAG API Server...")
    
    # Инициализируем RAG тренер
    if not initialize_rag_trainer():
        logger.error("❌ Не удалось инициализировать RAG тренер")
        sys.exit(1)
    
    # Запускаем Flask сервер
    logger.info("🌐 API Server готов к работе!")
    logger.info("📡 Доступные endpoints:")
    logger.info("   - GET  /api/health - проверка здоровья")
    logger.info("   - POST /api/analyze-file - анализ одного файла")
    logger.info("   - POST /api/analyze-project - анализ проекта")
    logger.info("   - POST /api/train-file - дообучение на файле")
    logger.info("   - GET  /api/get-file-info - информация о файле")
    logger.info("   - GET  /api/list-files - список файлов")
    
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    main()
