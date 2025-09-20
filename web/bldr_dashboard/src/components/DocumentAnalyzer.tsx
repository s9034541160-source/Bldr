/**
 * DocumentAnalyzer - ПОЛНОЦЕННЫЙ анализатор документов для TypeScript/Ant Design
 * ENTERPRISE READY компонент для анализа проектных документов, PDF, DOC, DOCX
 */

import React, { useState, useCallback } from 'react';
import { 
  Card, 
  Upload, 
  Button, 
  Select, 
  Switch, 
  Progress, 
  Result, 
  Descriptions, 
  Table, 
  Tabs,
  Tag,
  Tree,
  message,
  Row,
  Col,
  Divider,
  Space,
  Badge,
  Typography,
  List
} from 'antd';
import { 
  FileTextOutlined,
  UploadOutlined,
  PlayCircleOutlined,
  DownloadOutlined,
  TableOutlined,
  CheckCircleOutlined,
  FileSearchOutlined,
  AuditOutlined,
  DatabaseOutlined
} from '@ant-design/icons';
import type { RcFile, UploadFile } from 'antd/es/upload/interface';

const { Option } = Select;
const { TabPane } = Tabs;
const { Text, Paragraph } = Typography;

interface AnalysisParams {
  analysisType: string;
  extractData: boolean;
  checkCompliance: boolean;
  extractTables: boolean;
  recognizeEntities: boolean;
  language: string;
  structuralAnalysis: boolean;
}

interface ExtractedEntity {
  text: string;
  type: string;
  confidence: number;
  position: [number, number];
}

interface ExtractedTable {
  title: string;
  headers: string[];
  rows: string[][];
  page: number;
  confidence: number;
}

interface AnalysisResult {
  summary: {
    documents: Array<{
      filename: string;
      pages: number;
      language: string;
      document_type: string;
      entities_found: ExtractedEntity[];
      tables_extracted: ExtractedTable[];
      structure_analysis: {
        sections: string[];
        headings: string[];
        lists_count: number;
        images_count: number;
      };
    }>;
  };
  compliance_check: {
    norms_compliance: string;
    missing_sections: string[];
    recommendations: string[];
    score: number;
  };
  extracted_data: {
    key_parameters: Record<string, any>;
    specifications: Record<string, any>;
    materials: string[];
    dimensions: string[];
  };
}

const DocumentAnalyzer: React.FC = () => {
  const [documents, setDocuments] = useState<UploadFile[]>([]);
  const [analysisParams, setAnalysisParams] = useState<AnalysisParams>({
    analysisType: 'full',
    extractData: true,
    checkCompliance: true,
    extractTables: true,
    recognizeEntities: true,
    language: 'ru',
    structuralAnalysis: true
  });
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  // Обработка загрузки документов
  const handleDocumentChange = useCallback((info: any) => {
    const { fileList } = info;
    
    const supportedDocs = fileList.filter((file: UploadFile) => {
      const isSupported = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain',
        'text/rtf'
      ].includes(file.type || '');
      
      if (!isSupported && file.status !== 'removed') {
        message.error(`Файл ${file.name} не поддерживается`);
      }
      
      if (file.size && file.size > 50 * 1024 * 1024) {
        message.error(`Документ ${file.name} слишком большой (максимум 50MB)`);
        return false;
      }
      
      return isSupported;
    });
    
    setDocuments(supportedDocs);
  }, []);

  const customRequest = ({ onSuccess }: any) => {
    setTimeout(() => {
      onSuccess({});
    }, 0);
  };

  const startAnalysis = async () => {
    if (documents.length === 0) {
      message.warning('Пожалуйста, загрузите документы для анализа');
      return;
    }

    setIsAnalyzing(true);
    setAnalysisProgress(0);
    setAnalysisResult(null);
    setAnalysisError(null);

    try {
      const formData = new FormData();
      
      documents.forEach((doc) => {
        if (doc.originFileObj) {
          formData.append('documents', doc.originFileObj as RcFile);
        }
      });
      
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
        message.success('Анализ документов запущен');
        
        const checkProgress = async () => {
          try {
            const statusResponse = await fetch(`/api/tools/jobs/${result.job_id}/status`);
            if (statusResponse.ok) {
              const statusData = await statusResponse.json();
              
              setAnalysisProgress(statusData.progress || 0);
              
              if (statusData.status === 'completed') {
                setAnalysisResult(statusData.result);
                setIsAnalyzing(false);
                message.success('Анализ документов завершен!');
              } else if (statusData.status === 'failed') {
                setAnalysisError(statusData.error || 'Неизвестная ошибка');
                setIsAnalyzing(false);
                message.error('Ошибка анализа документов');
              } else {
                setTimeout(checkProgress, 2000);
              }
            }
          } catch (error) {
            console.error('Ошибка проверки статуса:', error);
            setTimeout(checkProgress, 5000);
          }
        };
        
        checkProgress();
        
      } else {
        throw new Error(result.message || 'Неизвестная ошибка');
      }

    } catch (error) {
      console.error('Ошибка запуска анализа:', error);
      setAnalysisError(error instanceof Error ? error.message : 'Неизвестная ошибка');
      setIsAnalyzing(false);
      message.error('Ошибка при запуске анализа');
    }
  };

  const downloadResult = async () => {
    if (!currentJobId) return;
    
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
      
      message.success('Отчет по анализу скачан');
    } catch (error) {
      message.error('Ошибка при скачивании отчета');
    }
  };

  const entityColumns = [
    { title: 'Текст', dataIndex: 'text', key: 'text' },
    { title: 'Тип', dataIndex: 'type', key: 'type',
      render: (type: string) => <Tag color="blue">{type}</Tag> },
    { title: 'Уверенность', dataIndex: 'confidence', key: 'confidence',
      render: (conf: number) => `${Math.round(conf * 100)}%` }
  ];

  const tableColumns = [
    { title: 'Название', dataIndex: 'title', key: 'title' },
    { title: 'Колонок', dataIndex: 'headers', key: 'headers',
      render: (headers: string[]) => headers.length },
    { title: 'Строк', dataIndex: 'rows', key: 'rows',
      render: (rows: string[][]) => rows.length },
    { title: 'Страница', dataIndex: 'page', key: 'page' }
  ];

  return (
    <div>
      <Row gutter={[24, 24]}>
        <Col span={12}>
          <Card title="📄 Загрузка документов" size="small">
            <Upload.Dragger
              multiple
              accept=".pdf,.doc,.docx,.txt,.rtf"
              fileList={documents}
              onChange={handleDocumentChange}
              customRequest={customRequest}
            >
              <p className="ant-upload-drag-icon">
                <FileTextOutlined style={{ fontSize: 48, color: '#52c41a' }} />
              </p>
              <p className="ant-upload-text">
                Перетащите документы для загрузки
              </p>
              <p className="ant-upload-hint">
                Поддержка: PDF, DOC, DOCX, TXT, RTF (до 50MB)
              </p>
            </Upload.Dragger>
          </Card>
        </Col>

        <Col span={12}>
          <Card title="⚙️ Параметры анализа" size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Select
                style={{ width: '100%' }}
                value={analysisParams.analysisType}
                onChange={(value) => setAnalysisParams(prev => ({ ...prev, analysisType: value }))}
              >
                <Option value="full">Полный анализ</Option>
                <Option value="structure">Структурный анализ</Option>
                <Option value="content">Анализ содержания</Option>
                <Option value="compliance">Проверка соответствия</Option>
              </Select>
              
              <Select
                style={{ width: '100%' }}
                value={analysisParams.language}
                onChange={(value) => setAnalysisParams(prev => ({ ...prev, language: value }))}
              >
                <Option value="ru">Русский</Option>
                <Option value="en">English</Option>
                <Option value="auto">Автоопределение</Option>
              </Select>

              <Divider />
              
              <Space direction="vertical">
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Извлечение данных</span>
                  <Switch checked={analysisParams.extractData}
                    onChange={(checked) => setAnalysisParams(prev => ({ ...prev, extractData: checked }))} />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Проверка соответствия</span>
                  <Switch checked={analysisParams.checkCompliance}
                    onChange={(checked) => setAnalysisParams(prev => ({ ...prev, checkCompliance: checked }))} />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Извлечение таблиц</span>
                  <Switch checked={analysisParams.extractTables}
                    onChange={(checked) => setAnalysisParams(prev => ({ ...prev, extractTables: checked }))} />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Распознавание сущностей</span>
                  <Switch checked={analysisParams.recognizeEntities}
                    onChange={(checked) => setAnalysisParams(prev => ({ ...prev, recognizeEntities: checked }))} />
                </div>
              </Space>
            </Space>
          </Card>
        </Col>
      </Row>

      <div style={{ textAlign: 'center', margin: '24px 0' }}>
        <Button type="primary" size="large" icon={<PlayCircleOutlined />}
          onClick={startAnalysis} disabled={documents.length === 0 || isAnalyzing}
          loading={isAnalyzing}>
          {isAnalyzing ? 'Анализируем документы...' : 'Начать анализ'}
        </Button>
        {documents.length > 0 && (
          <div style={{ marginTop: '8px', color: '#666' }}>
            К анализу: {documents.length} документ(ов)
          </div>
        )}
      </div>

      {isAnalyzing && (
        <Card style={{ marginBottom: '24px' }}>
          <div style={{ textAlign: 'center' }}>
            <Progress type="circle" percent={analysisProgress} status="active" />
            <p style={{ marginTop: '16px' }}>AI анализирует структуру документов...</p>
          </div>
        </Card>
      )}

      {analysisResult && (
        <Card title="✅ Результаты анализа документов"
          extra={<Button type="primary" icon={<DownloadOutlined />} onClick={downloadResult}>Скачать отчет</Button>}>
          
          <Descriptions bordered column={3} style={{ marginBottom: '24px' }}>
            <Descriptions.Item label="Обработано">{analysisResult.summary.documents.length} документ(ов)</Descriptions.Item>
            <Descriptions.Item label="Оценка соответствия">
              <Badge status={analysisResult.compliance_check.score > 80 ? 'success' : 'warning'}
                text={`${analysisResult.compliance_check.score}%`} />
            </Descriptions.Item>
            <Descriptions.Item label="Соответствие нормам">
              {analysisResult.compliance_check.norms_compliance}
            </Descriptions.Item>
          </Descriptions>

          <Tabs>
            {analysisResult.summary.documents.map((doc, idx) => (
              <TabPane tab={`${doc.filename} (${doc.pages} стр.)`} key={idx.toString()}>
                <Row gutter={[16, 16]}>
                  <Col span={12}>
                    <Card title="📋 Структура документа" size="small">
                      <Descriptions size="small" column={1}>
                        <Descriptions.Item label="Язык">{doc.language}</Descriptions.Item>
                        <Descriptions.Item label="Тип">{doc.document_type}</Descriptions.Item>
                        <Descriptions.Item label="Разделов">{doc.structure_analysis.sections.length}</Descriptions.Item>
                        <Descriptions.Item label="Заголовков">{doc.structure_analysis.headings.length}</Descriptions.Item>
                      </Descriptions>
                    </Card>
                    
                    {doc.entities_found.length > 0 && (
                      <Card title="🏷️ Найденные сущности" size="small" style={{ marginTop: '16px' }}>
                        <Table columns={entityColumns} dataSource={doc.entities_found}
                          size="small" pagination={{ pageSize: 5 }} />
                      </Card>
                    )}
                  </Col>
                  
                  <Col span={12}>
                    {doc.tables_extracted.length > 0 && (
                      <Card title="📋 Извлеченные таблицы" size="small">
                        <Table columns={tableColumns} dataSource={doc.tables_extracted}
                          size="small" pagination={{ pageSize: 5 }} />
                      </Card>
                    )}
                    
                    {doc.structure_analysis.sections.length > 0 && (
                      <Card title="🗂️ Разделы" size="small" style={{ marginTop: '16px' }}>
                        <List size="small" dataSource={doc.structure_analysis.sections}
                          renderItem={item => <List.Item><Text>{item}</Text></List.Item>} />
                      </Card>
                    )}
                  </Col>
                </Row>
              </TabPane>
            ))}
          </Tabs>
          
          {analysisResult.compliance_check.recommendations.length > 0 && (
            <Card title="💡 Рекомендации" style={{ marginTop: '16px' }}>
              <List dataSource={analysisResult.compliance_check.recommendations}
                renderItem={item => <List.Item>{item}</List.Item>} />
            </Card>
          )}
        </Card>
      )}

      {analysisError && (
        <Result status="error" title="Ошибка анализа" subTitle={analysisError}
          extra={<Button type="primary" onClick={() => setAnalysisError(null)}>Повторить</Button>} />
      )}
    </div>
  );
};

export default DocumentAnalyzer;
