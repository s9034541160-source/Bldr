/**
 * TenderAnalyzer - ПОЛНОЦЕННЫЙ комплексный анализатор тендерной документации
 * ENTERPRISE READY компонент для всестороннего анализа тендеров:
 * - Анализ документации (техзадание, требования, условия)
 * - Анализ смет и финансов
 * - Анализ чертежей и изображений  
 * - Оценка рисков и соответствия
 * - Рекомендации по участию
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
  Alert,
  Statistic,
  message,
  Row,
  Col,
  Divider,
  Space,
  Badge,
  Typography,
  List,
  Timeline,
  Rate
} from 'antd';
import { 
  FileTextOutlined,
  UploadOutlined,
  PlayCircleOutlined,
  DownloadOutlined,
  DollarCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  TrophyOutlined,
  AlertOutlined,
  CalendarOutlined,
  TeamOutlined,
  FundOutlined
} from '@ant-design/icons';
import type { RcFile, UploadFile } from 'antd/es/upload/interface';

const { Option } = Select;
const { TabPane } = Tabs;
const { Text, Paragraph, Title } = Typography;

interface TenderAnalysisParams {
  analysisDepth: string;
  includeFinancialAnalysis: boolean;
  includeRiskAssessment: boolean;
  includeComplianceCheck: boolean;
  includeCompetitorAnalysis: boolean;
  includeRecommendations: boolean;
  estimateBudget: boolean;
  checkDeadlines: boolean;
}

interface RiskFactor {
  category: string;
  level: 'low' | 'medium' | 'high';
  description: string;
  impact: number;
  probability: number;
  mitigation: string;
}

interface CompetitorInfo {
  name: string;
  experience_years: number;
  previous_wins: number;
  estimated_bid: number;
  advantages: string[];
  weaknesses: string[];
}

interface FinancialAnalysis {
  estimated_cost: number;
  profit_margin: number;
  recommended_bid: number;
  cost_breakdown: Record<string, number>;
  payment_terms: string;
  penalties: string[];
  bonuses: string[];
}

interface TenderAnalysisResult {
  summary: {
    tender_name: string;
    customer: string;
    tender_type: string;
    deadline: string;
    budget_estimate: number;
    win_probability: number;
    recommendation: 'participate' | 'skip' | 'consider';
    key_requirements: string[];
  };
  document_analysis: {
    technical_requirements: string[];
    qualification_requirements: string[];
    missing_documents: string[];
    compliance_score: number;
    complexity_level: string;
  };
  financial_analysis: FinancialAnalysis;
  risk_assessment: {
    overall_risk: 'low' | 'medium' | 'high';
    risk_factors: RiskFactor[];
    total_risk_score: number;
  };
  competitor_analysis: {
    identified_competitors: CompetitorInfo[];
    market_position: string;
    competitive_advantages: string[];
  };
  recommendations: {
    participation_advice: string;
    bid_strategy: string;
    preparation_steps: string[];
    timeline: Array<{
      task: string;
      deadline: string;
      priority: 'high' | 'medium' | 'low';
    }>;
  };
}

const TenderAnalyzer: React.FC = () => {
  const [documents, setDocuments] = useState<UploadFile[]>([]);
  const [analysisParams, setAnalysisParams] = useState<TenderAnalysisParams>({
    analysisDepth: 'comprehensive',
    includeFinancialAnalysis: true,
    includeRiskAssessment: true,
    includeComplianceCheck: true,
    includeCompetitorAnalysis: true,
    includeRecommendations: true,
    estimateBudget: true,
    checkDeadlines: true
  });
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<TenderAnalysisResult | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  // Обработка загрузки документов тендера
  const handleDocumentChange = useCallback((info: any) => {
    const { fileList } = info;
    
    const supportedDocs = fileList.filter((file: UploadFile) => {
      const isSupported = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/plain',
        'image/jpeg',
        'image/png',
        'image/tiff'
      ].includes(file.type || '');
      
      if (!isSupported && file.status !== 'removed') {
        message.error(`Файл ${file.name} не поддерживается`);
      }
      
      if (file.size && file.size > 100 * 1024 * 1024) {
        message.error(`Документ ${file.name} слишком большой (максимум 100MB)`);
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

  const startTenderAnalysis = async () => {
    if (documents.length === 0) {
      message.warning('Пожалуйста, загрузите документы тендера для анализа');
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
          formData.append('tender_documents', doc.originFileObj as RcFile);
        }
      });
      
      formData.append('analysis_params', JSON.stringify(analysisParams));

      const response = await fetch('/api/tools/analyze/tender', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`HTTP ошибка: ${response.status}`);
      }

      const result = await response.json();
      
      if (result.success) {
        setCurrentJobId(result.job_id);
        message.success('Комплексный анализ тендера запущен');
        
        const checkProgress = async () => {
          try {
            const statusResponse = await fetch(`/api/tools/jobs/${result.job_id}/status`);
            if (statusResponse.ok) {
              const statusData = await statusResponse.json();
              
              setAnalysisProgress(statusData.progress || 0);
              
              if (statusData.status === 'completed') {
                setAnalysisResult(statusData.result);
                setIsAnalyzing(false);
                message.success('Анализ тендера завершен!');
              } else if (statusData.status === 'failed') {
                setAnalysisError(statusData.error || 'Неизвестная ошибка');
                setIsAnalyzing(false);
                message.error('Ошибка анализа тендера');
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
      message.error('Ошибка при запуске анализа тендера');
    }
  };

  const downloadReport = async () => {
    if (!currentJobId) return;
    
    try {
      const response = await fetch(`/api/tools/jobs/${currentJobId}/download`);
      const blob = await response.blob();
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `tender_analysis_report.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      message.success('Отчет по анализу тендера скачан');
    } catch (error) {
      message.error('Ошибка при скачивании отчета');
    }
  };

  const getRecommendationColor = (recommendation: string) => {
    switch (recommendation) {
      case 'participate': return 'success';
      case 'skip': return 'error';
      case 'consider': return 'warning';
      default: return 'default';
    }
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low': return 'success';
      case 'medium': return 'warning';
      case 'high': return 'error';
      default: return 'default';
    }
  };

  const competitorColumns = [
    { title: 'Компания', dataIndex: 'name', key: 'name' },
    { title: 'Опыт (лет)', dataIndex: 'experience_years', key: 'experience' },
    { title: 'Прошлых побед', dataIndex: 'previous_wins', key: 'wins' },
    { title: 'Ожидаемая заявка', dataIndex: 'estimated_bid', key: 'bid',
      render: (bid: number) => `${bid.toLocaleString()} ₽` }
  ];

  const riskColumns = [
    { title: 'Категория', dataIndex: 'category', key: 'category' },
    { title: 'Уровень', dataIndex: 'level', key: 'level',
      render: (level: string) => <Tag color={getRiskColor(level)}>{level.toUpperCase()}</Tag> },
    { title: 'Воздействие', dataIndex: 'impact', key: 'impact',
      render: (impact: number) => `${impact}/10` },
    { title: 'Вероятность', dataIndex: 'probability', key: 'probability',
      render: (prob: number) => `${prob}%` }
  ];

  return (
    <div>
      <Row gutter={[24, 24]}>
        <Col span={12}>
          <Card title="📋 Загрузка документов тендера" size="small">
            <Upload.Dragger
              multiple
              accept=".pdf,.doc,.docx,.xls,.xlsx,.txt,.jpg,.jpeg,.png,.tiff"
              fileList={documents}
              onChange={handleDocumentChange}
              customRequest={customRequest}
            >
              <p className="ant-upload-drag-icon">
                <FileTextOutlined style={{ fontSize: 48, color: '#1890ff' }} />
              </p>
              <p className="ant-upload-text">
                Перетащите документы тендера для загрузки
              </p>
              <p className="ant-upload-hint">
                Поддержка: PDF, DOC, DOCX, XLS, XLSX, изображения (до 100MB)
              </p>
            </Upload.Dragger>
          </Card>
        </Col>

        <Col span={12}>
          <Card title="⚙️ Параметры анализа" size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Select
                style={{ width: '100%' }}
                value={analysisParams.analysisDepth}
                onChange={(value) => setAnalysisParams(prev => ({ ...prev, analysisDepth: value }))}
              >
                <Option value="comprehensive">Комплексный анализ</Option>
                <Option value="financial">Финансовый анализ</Option>
                <Option value="technical">Технический анализ</Option>
                <Option value="risk">Анализ рисков</Option>
                <Option value="quick">Быстрый анализ</Option>
              </Select>

              <Divider />
              
              <Space direction="vertical">
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Финансовый анализ</span>
                  <Switch checked={analysisParams.includeFinancialAnalysis}
                    onChange={(checked) => setAnalysisParams(prev => ({ ...prev, includeFinancialAnalysis: checked }))} />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Оценка рисков</span>
                  <Switch checked={analysisParams.includeRiskAssessment}
                    onChange={(checked) => setAnalysisParams(prev => ({ ...prev, includeRiskAssessment: checked }))} />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Проверка соответствия</span>
                  <Switch checked={analysisParams.includeComplianceCheck}
                    onChange={(checked) => setAnalysisParams(prev => ({ ...prev, includeComplianceCheck: checked }))} />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Анализ конкурентов</span>
                  <Switch checked={analysisParams.includeCompetitorAnalysis}
                    onChange={(checked) => setAnalysisParams(prev => ({ ...prev, includeCompetitorAnalysis: checked }))} />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Рекомендации</span>
                  <Switch checked={analysisParams.includeRecommendations}
                    onChange={(checked) => setAnalysisParams(prev => ({ ...prev, includeRecommendations: checked }))} />
                </div>
              </Space>
            </Space>
          </Card>
        </Col>
      </Row>

      <div style={{ textAlign: 'center', margin: '24px 0' }}>
        <Button type="primary" size="large" icon={<PlayCircleOutlined />}
          onClick={startTenderAnalysis} disabled={documents.length === 0 || isAnalyzing}
          loading={isAnalyzing}>
          {isAnalyzing ? 'Анализируем тендер...' : 'Начать комплексный анализ'}
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
            <p style={{ marginTop: '16px' }}>AI анализирует тендерную документацию...</p>
          </div>
        </Card>
      )}

      {analysisResult && (
        <Card title="🏆 Результаты комплексного анализа тендера"
          extra={<Button type="primary" icon={<DownloadOutlined />} onClick={downloadReport}>Скачать отчет</Button>}>
          
          {/* Основная сводка */}
          <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
            <Col span={6}>
              <Statistic title="Вероятность победы" value={analysisResult.summary.win_probability} suffix="%" />
            </Col>
            <Col span={6}>
              <Statistic title="Бюджет тендера" value={analysisResult.summary.budget_estimate} 
                formatter={(value) => `${value?.toLocaleString()} ₽`} />
            </Col>
            <Col span={6}>
              <Statistic title="Соответствие требованиям" 
                value={analysisResult.document_analysis.compliance_score} suffix="%" />
            </Col>
            <Col span={6}>
              <div style={{ textAlign: 'center' }}>
                <Title level={4} style={{ margin: 0 }}>Рекомендация</Title>
                <Tag color={getRecommendationColor(analysisResult.summary.recommendation)} 
                     style={{ fontSize: '16px', padding: '8px 16px', marginTop: '8px' }}>
                  {analysisResult.summary.recommendation === 'participate' ? 'УЧАСТВОВАТЬ' :
                   analysisResult.summary.recommendation === 'skip' ? 'НЕ УЧАСТВОВАТЬ' : 'РАССМОТРЕТЬ'}
                </Tag>
              </div>
            </Col>
          </Row>

          <Alert 
            type={analysisResult.summary.recommendation === 'participate' ? 'success' : 
                  analysisResult.summary.recommendation === 'skip' ? 'error' : 'warning'}
            message={analysisResult.recommendations.participation_advice}
            style={{ marginBottom: '24px' }}
          />

          <Tabs>
            {/* Общая информация о тендере */}
            <TabPane tab="📋 Информация о тендере" key="info">
              <Descriptions bordered column={2}>
                <Descriptions.Item label="Наименование">{analysisResult.summary.tender_name}</Descriptions.Item>
                <Descriptions.Item label="Заказчик">{analysisResult.summary.customer}</Descriptions.Item>
                <Descriptions.Item label="Тип тендера">{analysisResult.summary.tender_type}</Descriptions.Item>
                <Descriptions.Item label="Срок подачи заявок">{analysisResult.summary.deadline}</Descriptions.Item>
                <Descriptions.Item label="Сложность" span={2}>
                  <Tag color="blue">{analysisResult.document_analysis.complexity_level}</Tag>
                </Descriptions.Item>
              </Descriptions>
              
              <Divider />
              
              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <Card title="🎯 Ключевые требования" size="small">
                    <List size="small" dataSource={analysisResult.summary.key_requirements}
                      renderItem={item => <List.Item><Text>{item}</Text></List.Item>} />
                  </Card>
                </Col>
                <Col span={12}>
                  <Card title="❗ Недостающие документы" size="small">
                    <List size="small" dataSource={analysisResult.document_analysis.missing_documents}
                      renderItem={item => <List.Item><Text type="danger">{item}</Text></List.Item>} />
                  </Card>
                </Col>
              </Row>
            </TabPane>

            {/* Финансовый анализ */}
            <TabPane tab="💰 Финансовый анализ" key="financial">
              <Row gutter={[16, 16]}>
                <Col span={8}>
                  <Statistic title="Расчетная стоимость" 
                    value={analysisResult.financial_analysis.estimated_cost}
                    formatter={(value) => `${value?.toLocaleString()} ₽`} />
                </Col>
                <Col span={8}>
                  <Statistic title="Маржа прибыли" 
                    value={analysisResult.financial_analysis.profit_margin} suffix="%" />
                </Col>
                <Col span={8}>
                  <Statistic title="Рекомендуемая заявка" 
                    value={analysisResult.financial_analysis.recommended_bid}
                    formatter={(value) => `${value?.toLocaleString()} ₽`} />
                </Col>
              </Row>
              
              <Divider />
              
              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <Card title="💳 Условия оплаты" size="small">
                    <Paragraph>{analysisResult.financial_analysis.payment_terms}</Paragraph>
                  </Card>
                </Col>
                <Col span={12}>
                  <Card title="⚖️ Штрафы и бонусы" size="small">
                    <div style={{ marginBottom: '16px' }}>
                      <Text strong>Штрафы:</Text>
                      <List size="small" dataSource={analysisResult.financial_analysis.penalties}
                        renderItem={item => <List.Item><Text type="danger">{item}</Text></List.Item>} />
                    </div>
                    <div>
                      <Text strong>Бонусы:</Text>
                      <List size="small" dataSource={analysisResult.financial_analysis.bonuses}
                        renderItem={item => <List.Item><Text type="success">{item}</Text></List.Item>} />
                    </div>
                  </Card>
                </Col>
              </Row>
            </TabPane>

            {/* Анализ рисков */}
            <TabPane tab="⚠️ Анализ рисков" key="risks">
              <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
                <Col span={8}>
                  <Statistic title="Общий уровень риска" 
                    value={analysisResult.risk_assessment.overall_risk.toUpperCase()}
                    valueStyle={{ color: getRiskColor(analysisResult.risk_assessment.overall_risk) === 'success' ? '#3f8600' : 
                                        getRiskColor(analysisResult.risk_assessment.overall_risk) === 'warning' ? '#cf1322' : '#cf1322' }} />
                </Col>
                <Col span={8}>
                  <Statistic title="Оценка риска" 
                    value={analysisResult.risk_assessment.total_risk_score} suffix="/100" />
                </Col>
                <Col span={8}>
                  <Statistic title="Факторов риска" 
                    value={analysisResult.risk_assessment.risk_factors.length} />
                </Col>
              </Row>
              
              <Table columns={riskColumns} dataSource={analysisResult.risk_assessment.risk_factors}
                size="small" pagination={{ pageSize: 10 }}
                expandable={{
                  expandedRowRender: (record) => (
                    <div>
                      <Paragraph><Text strong>Описание:</Text> {record.description}</Paragraph>
                      <Paragraph><Text strong>Меры смягчения:</Text> {record.mitigation}</Paragraph>
                    </div>
                  ),
                }} />
            </TabPane>

            {/* Анализ конкурентов */}
            <TabPane tab="🏢 Конкуренты" key="competitors">
              <Alert type="info" message={`Рыночная позиция: ${analysisResult.competitor_analysis.market_position}`}
                style={{ marginBottom: '16px' }} />
              
              <Table columns={competitorColumns} dataSource={analysisResult.competitor_analysis.identified_competitors}
                size="small" pagination={{ pageSize: 5 }}
                expandable={{
                  expandedRowRender: (record) => (
                    <Row gutter={[16, 16]}>
                      <Col span={12}>
                        <Text strong>Преимущества:</Text>
                        <List size="small" dataSource={record.advantages}
                          renderItem={item => <List.Item><Text type="success">+ {item}</Text></List.Item>} />
                      </Col>
                      <Col span={12}>
                        <Text strong>Слабые стороны:</Text>
                        <List size="small" dataSource={record.weaknesses}
                          renderItem={item => <List.Item><Text type="warning">- {item}</Text></List.Item>} />
                      </Col>
                    </Row>
                  ),
                }} />
              
              <Divider />
              
              <Card title="🎯 Наши конкурентные преимущества" size="small">
                <List dataSource={analysisResult.competitor_analysis.competitive_advantages}
                  renderItem={item => <List.Item><Text type="success">✓ {item}</Text></List.Item>} />
              </Card>
            </TabPane>

            {/* Рекомендации */}
            <TabPane tab="💡 Рекомендации" key="recommendations">
              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <Card title="📋 Стратегия заявки" size="small">
                    <Paragraph>{analysisResult.recommendations.bid_strategy}</Paragraph>
                  </Card>
                  
                  <Card title="✅ Шаги подготовки" size="small" style={{ marginTop: '16px' }}>
                    <List dataSource={analysisResult.recommendations.preparation_steps}
                      renderItem={item => <List.Item><Text>• {item}</Text></List.Item>} />
                  </Card>
                </Col>
                
                <Col span={12}>
                  <Card title="📅 План действий" size="small">
                    <Timeline>
                      {analysisResult.recommendations.timeline.map((task, idx) => (
                        <Timeline.Item key={idx} 
                          color={task.priority === 'high' ? 'red' : task.priority === 'medium' ? 'orange' : 'green'}>
                          <div>
                            <Text strong>{task.task}</Text>
                            <br />
                            <Text type="secondary">До: {task.deadline}</Text>
                            <br />
                            <Tag color={task.priority === 'high' ? 'red' : task.priority === 'medium' ? 'orange' : 'green'}>
                              {task.priority === 'high' ? 'Высокий' : task.priority === 'medium' ? 'Средний' : 'Низкий'} приоритет
                            </Tag>
                          </div>
                        </Timeline.Item>
                      ))}
                    </Timeline>
                  </Card>
                </Col>
              </Row>
            </TabPane>
          </Tabs>
        </Card>
      )}

      {analysisError && (
        <Result status="error" title="Ошибка анализа тендера" subTitle={analysisError}
          extra={<Button type="primary" onClick={() => setAnalysisError(null)}>Повторить</Button>} />
      )}
    </div>
  );
};

export default TenderAnalyzer;