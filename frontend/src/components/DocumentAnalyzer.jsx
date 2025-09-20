/**
 * DocumentAnalyzer - компонент для анализа проектных документов
 * Поддерживает загрузку PDF, DOC, DOCX, TXT файлов
 */

import React, { useState, useRef, useEffect } from 'react';
import { Upload, FileText, Settings, Play, Download, Trash2, Eye, AlertCircle, Clock, CheckCircle2 } from 'lucide-react';

const DocumentAnalyzer = () => {
  // State для загруженных документов
  const [documents, setDocuments] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  
  // State для параметров анализа
  const [analysisParams, setAnalysisParams] = useState({
    analysisType: 'full',
    extractData: true,
    checkCompliance: false,
    extractTables: true,
    recognizeEntities: false,
    language: 'ru'
  });
  
  // State для выполнения анализа
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [currentJobId, setCurrentJobId] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analysisError, setAnalysisError] = useState(null);
  
  const fileInputRef = useRef();
  const wsRef = useRef();

  // Поддерживаемые типы файлов
  const supportedTypes = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'text/rtf'
  ];

  // WebSocket подключение
  useEffect(() => {
    const connectWebSocket = () => {
      const wsUrl = `ws://localhost:8000/ws/`;
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('WebSocket подключен для анализа документов');
        // Подписаться на уведомления о задачах
        ws.send(JSON.stringify({
          type: 'subscribe',
          subscription_type: 'jobs'
        }));
      };
      
      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        
        if (message.type === 'job_update' && message.job_id === currentJobId) {
          setAnalysisProgress(message.data.progress);
          
          if (message.data.status === 'completed') {
            setIsAnalyzing(false);
            setAnalysisResult(message.data.result);
            setCurrentJobId(null);
          } else if (message.data.status === 'failed') {
            setIsAnalyzing(false);
            setAnalysisError(message.data.error);
            setCurrentJobId(null);
          }
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket ошибка:', error);
      };
      
      ws.onclose = () => {
        console.log('WebSocket отключен, переподключение...');
        setTimeout(connectWebSocket, 3000);
      };
      
      wsRef.current = ws;
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [currentJobId]);

  // Обработка выбора файлов
  const handleFileSelect = async (event) => {
    const files = Array.from(event.target.files);
    
    if (files.length === 0) return;
    
    setIsUploading(true);
    
    try {
      const newDocuments = await Promise.all(
        files.map(async (file) => {
          // Проверка типа файла
          if (!supportedTypes.includes(file.type)) {
            throw new Error(`Неподдерживаемый тип файла: ${file.name}`);
          }
          
          // Проверка размера файла (50MB лимит)
          if (file.size > 50 * 1024 * 1024) {
            throw new Error(`Файл слишком большой: ${file.name}`);
          }
          
          const preview = await generateDocumentPreview(file);
          
          return {
            id: Math.random().toString(36).substr(2, 9),
            file: file,
            name: file.name,
            size: file.size,
            type: file.type,
            preview: preview,
            uploadTime: new Date()
          };
        })
      );
      
      setDocuments(prev => [...prev, ...newDocuments]);
    } catch (error) {
      console.error('Ошибка загрузки файлов:', error);
      alert(`Ошибка: ${error.message}`);
    } finally {
      setIsUploading(false);
      // Очистить input
      event.target.value = '';
    }
  };

  // Генерация превью для документа
  const generateDocumentPreview = async (file) => {
    return new Promise((resolve) => {
      if (file.type === 'application/pdf') {
        resolve({
          type: 'pdf',
          pageCount: 'Определение...',
          icon: '📄'
        });
      } else if (file.type.includes('word') || file.type === 'application/msword') {
        resolve({
          type: 'word',
          icon: '📝',
          description: 'Документ Word'
        });
      } else if (file.type === 'text/plain') {
        resolve({
          type: 'text',
          icon: '📃',
          description: 'Текстовый файл'
        });
      } else {
        resolve({
          type: 'unknown',
          icon: '📋',
          description: 'Документ'
        });
      }
    });
  };

  // Удаление документа
  const removeDocument = (documentId) => {
    setDocuments(prev => prev.filter(doc => doc.id !== documentId));
  };

  // Запуск анализа
  const startAnalysis = async () => {
    if (documents.length === 0) {
      alert('Пожалуйста, загрузите документы для анализа');
      return;
    }
    
    setIsAnalyzing(true);
    setAnalysisProgress(0);
    setAnalysisResult(null);
    setAnalysisError(null);
    
    try {
      const formData = new FormData();
      
      // Добавить файлы
      documents.forEach(doc => {
        formData.append('documents', doc.file);
      });
      
      // Добавить параметры
      formData.append('params', JSON.stringify(analysisParams));
      
      const response = await fetch('/api/tools/analyze/documents', {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ошибка: ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result.success) {
        setCurrentJobId(result.job_id);
        
        // Подписаться на обновления этой задачи
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({
            type: 'subscribe',
            job_id: result.job_id
          }));
        }
      } else {
        throw new Error(result.message || 'Неизвестная ошибка');
      }
      
    } catch (error) {
      console.error('Ошибка запуска анализа:', error);
      setAnalysisError(error.message);
      setIsAnalyzing(false);
    }
  };

  // Отмена анализа
  const cancelAnalysis = async () => {
    if (!currentJobId) return;
    
    try {
      await fetch(`/api/tools/jobs/${currentJobId}/cancel`, {
        method: 'POST'
      });
      
      setIsAnalyzing(false);
      setCurrentJobId(null);
      setAnalysisProgress(0);
    } catch (error) {
      console.error('Ошибка отмены анализа:', error);
    }
  };

  // Скачивание результата
  const downloadResult = async () => {
    if (!analysisResult || !currentJobId) return;
    
    try {
      const response = await fetch(`/api/tools/jobs/${currentJobId}/download`);
      const blob = await response.blob();
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `document_analysis_result.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Ошибка скачивания:', error);
      alert('Ошибка при скачивании результата');
    }
  };

  // Форматирование размера файла
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="document-analyzer">
      <style jsx>{`
        .document-analyzer {
          max-width: 1200px;
          margin: 0 auto;
          padding: 20px;
        }
        
        .analyzer-header {
          margin-bottom: 30px;
        }
        
        .analyzer-title {
          font-size: 28px;
          font-weight: bold;
          color: #2c3e50;
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 8px;
        }
        
        .analyzer-subtitle {
          color: #7f8c8d;
          font-size: 16px;
        }
        
        .analyzer-content {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 30px;
        }
        
        .upload-section {
          background: #f8f9fa;
          border-radius: 12px;
          padding: 25px;
        }
        
        .section-title {
          font-size: 20px;
          font-weight: 600;
          color: #34495e;
          margin-bottom: 20px;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .upload-area {
          border: 2px dashed #bdc3c7;
          border-radius: 8px;
          padding: 40px;
          text-align: center;
          background: #fff;
          cursor: pointer;
          transition: all 0.3s ease;
        }
        
        .upload-area:hover {
          border-color: #3498db;
          background: #ecf0f1;
        }
        
        .upload-area.uploading {
          background: #e3f2fd;
          border-color: #2196f3;
        }
        
        .upload-icon {
          font-size: 48px;
          margin-bottom: 15px;
        }
        
        .upload-text {
          font-size: 16px;
          color: #34495e;
          margin-bottom: 8px;
        }
        
        .upload-hint {
          font-size: 14px;
          color: #95a5a6;
        }
        
        .hidden-input {
          display: none;
        }
        
        .document-list {
          margin-top: 20px;
        }
        
        .document-item {
          background: #fff;
          border: 1px solid #e0e6ed;
          border-radius: 8px;
          padding: 15px;
          margin-bottom: 10px;
          display: flex;
          align-items: center;
          gap: 12px;
        }
        
        .document-icon {
          font-size: 24px;
        }
        
        .document-info {
          flex: 1;
        }
        
        .document-name {
          font-weight: 500;
          color: #2c3e50;
          margin-bottom: 4px;
        }
        
        .document-details {
          font-size: 12px;
          color: #7f8c8d;
        }
        
        .document-actions {
          display: flex;
          gap: 8px;
        }
        
        .action-btn {
          background: none;
          border: none;
          cursor: pointer;
          padding: 8px;
          border-radius: 4px;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: background-color 0.2s;
        }
        
        .action-btn:hover {
          background: #f1f2f6;
        }
        
        .action-btn.danger:hover {
          background: #fee;
          color: #e74c3c;
        }
        
        .params-section {
          background: #fff;
          border-radius: 12px;
          border: 1px solid #e0e6ed;
          padding: 25px;
        }
        
        .param-group {
          margin-bottom: 20px;
        }
        
        .param-label {
          display: block;
          font-weight: 500;
          color: #34495e;
          margin-bottom: 8px;
        }
        
        .param-select, .param-input {
          width: 100%;
          padding: 10px;
          border: 1px solid #ddd;
          border-radius: 6px;
          font-size: 14px;
        }
        
        .param-checkbox {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
        }
        
        .param-checkbox input {
          margin: 0;
        }
        
        .analysis-controls {
          grid-column: 1 / -1;
          margin-top: 20px;
          text-align: center;
        }
        
        .start-btn, .cancel-btn {
          background: #3498db;
          color: white;
          border: none;
          padding: 15px 30px;
          font-size: 16px;
          border-radius: 8px;
          cursor: pointer;
          display: inline-flex;
          align-items: center;
          gap: 8px;
          transition: background-color 0.3s;
          margin: 0 10px;
        }
        
        .start-btn:hover {
          background: #2980b9;
        }
        
        .start-btn:disabled {
          background: #95a5a6;
          cursor: not-allowed;
        }
        
        .cancel-btn {
          background: #e74c3c;
        }
        
        .cancel-btn:hover {
          background: #c0392b;
        }
        
        .progress-section {
          grid-column: 1 / -1;
          background: #fff;
          border-radius: 12px;
          border: 1px solid #e0e6ed;
          padding: 25px;
          margin-top: 20px;
        }
        
        .progress-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 15px;
        }
        
        .progress-title {
          font-size: 18px;
          font-weight: 600;
          color: #34495e;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .progress-bar {
          background: #ecf0f1;
          border-radius: 10px;
          height: 20px;
          overflow: hidden;
          margin-bottom: 10px;
        }
        
        .progress-fill {
          background: linear-gradient(90deg, #3498db, #2ecc71);
          height: 100%;
          transition: width 0.3s ease;
          border-radius: 10px;
        }
        
        .progress-text {
          text-align: center;
          color: #7f8c8d;
          font-size: 14px;
        }
        
        .result-section {
          grid-column: 1 / -1;
          margin-top: 20px;
        }
        
        .result-card {
          background: #fff;
          border-radius: 12px;
          border: 1px solid #e0e6ed;
          padding: 25px;
        }
        
        .result-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 20px;
        }
        
        .result-title {
          font-size: 20px;
          font-weight: 600;
          color: #27ae60;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .download-btn {
          background: #27ae60;
          color: white;
          border: none;
          padding: 10px 20px;
          border-radius: 6px;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
        }
        
        .result-summary {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 20px;
          margin-bottom: 25px;
        }
        
        .summary-card {
          background: #f8f9fa;
          padding: 20px;
          border-radius: 8px;
        }
        
        .summary-label {
          font-size: 14px;
          color: #7f8c8d;
          margin-bottom: 8px;
        }
        
        .summary-value {
          font-size: 24px;
          font-weight: bold;
          color: #2c3e50;
        }
        
        .error-section {
          grid-column: 1 / -1;
          background: #fff;
          border-radius: 12px;
          border: 1px solid #e74c3c;
          padding: 25px;
          margin-top: 20px;
        }
        
        .error-title {
          font-size: 18px;
          font-weight: 600;
          color: #e74c3c;
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 10px;
        }
        
        .error-text {
          color: #c0392b;
          background: #fdf2f2;
          padding: 15px;
          border-radius: 6px;
          font-family: monospace;
        }
        
        @media (max-width: 768px) {
          .analyzer-content {
            grid-template-columns: 1fr;
            gap: 20px;
          }
          
          .result-summary {
            grid-template-columns: 1fr;
          }
        }
      `}</style>

      <div className="analyzer-header">
        <h1 className="analyzer-title">
          <FileText size={32} />
          Анализ документов
        </h1>
        <p className="analyzer-subtitle">
          Загрузите проектную документацию для автоматического анализа и извлечения данных
        </p>
      </div>

      <div className="analyzer-content">
        {/* Секция загрузки */}
        <div className="upload-section">
          <h2 className="section-title">
            <Upload size={20} />
            Загрузка документов
          </h2>
          
          <div 
            className={`upload-area ${isUploading ? 'uploading' : ''}`}
            onClick={() => fileInputRef.current?.click()}
          >
            <div className="upload-icon">📁</div>
            <div className="upload-text">
              {isUploading ? 'Загрузка файлов...' : 'Нажмите для выбора документов'}
            </div>
            <div className="upload-hint">
              Поддерживаются: PDF, DOC, DOCX, TXT (до 50MB)
            </div>
          </div>
          
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.doc,.docx,.txt,.rtf"
            onChange={handleFileSelect}
            className="hidden-input"
          />
          
          {documents.length > 0 && (
            <div className="document-list">
              {documents.map(doc => (
                <div key={doc.id} className="document-item">
                  <div className="document-icon">
                    {doc.preview?.icon || '📄'}
                  </div>
                  <div className="document-info">
                    <div className="document-name">{doc.name}</div>
                    <div className="document-details">
                      {formatFileSize(doc.size)} • {doc.preview?.description || 'Документ'}
                    </div>
                  </div>
                  <div className="document-actions">
                    <button className="action-btn" title="Предпросмотр">
                      <Eye size={16} />
                    </button>
                    <button 
                      className="action-btn danger" 
                      onClick={() => removeDocument(doc.id)}
                      title="Удалить"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Секция параметров */}
        <div className="params-section">
          <h2 className="section-title">
            <Settings size={20} />
            Параметры анализа
          </h2>
          
          <div className="param-group">
            <label className="param-label">Тип анализа</label>
            <select
              className="param-select"
              value={analysisParams.analysisType}
              onChange={(e) => setAnalysisParams(prev => ({
                ...prev,
                analysisType: e.target.value
              }))}
            >
              <option value="full">Полный анализ</option>
              <option value="structure">Структурный анализ</option>
              <option value="content">Анализ содержания</option>
              <option value="metadata">Анализ метаданных</option>
            </select>
          </div>
          
          <div className="param-group">
            <label className="param-label">Язык документов</label>
            <select
              className="param-select"
              value={analysisParams.language}
              onChange={(e) => setAnalysisParams(prev => ({
                ...prev,
                language: e.target.value
              }))}
            >
              <option value="ru">Русский</option>
              <option value="en">English</option>
              <option value="auto">Автоопределение</option>
            </select>
          </div>
          
          <div className="param-group">
            <div className="param-checkbox">
              <input
                type="checkbox"
                id="extractData"
                checked={analysisParams.extractData}
                onChange={(e) => setAnalysisParams(prev => ({
                  ...prev,
                  extractData: e.target.checked
                }))}
              />
              <label htmlFor="extractData">Извлечение данных</label>
            </div>
            
            <div className="param-checkbox">
              <input
                type="checkbox"
                id="checkCompliance"
                checked={analysisParams.checkCompliance}
                onChange={(e) => setAnalysisParams(prev => ({
                  ...prev,
                  checkCompliance: e.target.checked
                }))}
              />
              <label htmlFor="checkCompliance">Проверка соответствия нормам</label>
            </div>
            
            <div className="param-checkbox">
              <input
                type="checkbox"
                id="extractTables"
                checked={analysisParams.extractTables}
                onChange={(e) => setAnalysisParams(prev => ({
                  ...prev,
                  extractTables: e.target.checked
                }))}
              />
              <label htmlFor="extractTables">Извлечение таблиц</label>
            </div>
            
            <div className="param-checkbox">
              <input
                type="checkbox"
                id="recognizeEntities"
                checked={analysisParams.recognizeEntities}
                onChange={(e) => setAnalysisParams(prev => ({
                  ...prev,
                  recognizeEntities: e.target.checked
                }))}
              />
              <label htmlFor="recognizeEntities">Распознавание сущностей</label>
            </div>
          </div>
        </div>

        {/* Кнопки управления */}
        <div className="analysis-controls">
          {!isAnalyzing ? (
            <button 
              className="start-btn" 
              onClick={startAnalysis}
              disabled={documents.length === 0}
            >
              <Play size={20} />
              Начать анализ документов
            </button>
          ) : (
            <button className="cancel-btn" onClick={cancelAnalysis}>
              Отменить анализ
            </button>
          )}
        </div>

        {/* Прогресс анализа */}
        {isAnalyzing && (
          <div className="progress-section">
            <div className="progress-header">
              <div className="progress-title">
                <Clock size={20} />
                Выполнение анализа...
              </div>
              <div>{analysisProgress}%</div>
            </div>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${analysisProgress}%` }}
              />
            </div>
            <div className="progress-text">
              Анализируем {documents.length} документ(ов)...
            </div>
          </div>
        )}

        {/* Результаты */}
        {analysisResult && (
          <div className="result-section">
            <div className="result-card">
              <div className="result-header">
                <div className="result-title">
                  <CheckCircle2 size={24} />
                  Анализ завершен
                </div>
                <button className="download-btn" onClick={downloadResult}>
                  <Download size={16} />
                  Скачать отчет
                </button>
              </div>
              
              <div className="result-summary">
                <div className="summary-card">
                  <div className="summary-label">Время выполнения</div>
                  <div className="summary-value">{analysisResult.execution_time}с</div>
                </div>
                <div className="summary-card">
                  <div className="summary-label">Обработано документов</div>
                  <div className="summary-value">{documents.length}</div>
                </div>
                <div className="summary-card">
                  <div className="summary-label">Статус</div>
                  <div className="summary-value" style={{ color: '#27ae60' }}>Успешно</div>
                </div>
              </div>
              
              {analysisResult.summary && (
                <div style={{ marginTop: '20px' }}>
                  <h3>Результат анализа:</h3>
                  <pre style={{ 
                    background: '#f8f9fa', 
                    padding: '15px', 
                    borderRadius: '6px',
                    overflow: 'auto',
                    fontSize: '14px'
                  }}>
                    {JSON.stringify(analysisResult.summary, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Ошибки */}
        {analysisError && (
          <div className="error-section">
            <div className="error-title">
              <AlertCircle size={20} />
              Ошибка анализа
            </div>
            <div className="error-text">{analysisError}</div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentAnalyzer;