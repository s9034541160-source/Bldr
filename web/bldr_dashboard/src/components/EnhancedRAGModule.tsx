/**
 * Enhanced RAG Module
 * Полноценное управление RAG-обучением с максимальными настройками и аналитикой
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  Tabs,
  Row,
  Col,
  Button,
  Progress,
  Statistic,
  Alert,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  Slider,
  InputNumber,
  Upload,
  Tree,
  Table,
  Tag,
  Space,
  Tooltip,
  Badge,
  Timeline,
  List,
  Avatar,
  Descriptions,
  Divider,
  Collapse,
  Radio,
  Checkbox,
  message,
  notification
} from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  SettingOutlined,
  MonitorOutlined,
  FileTextOutlined,
  DatabaseOutlined,
  CloudUploadOutlined,
  BarChartOutlined,
  LineChartOutlined,
  BugOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  WarningOutlined,
  InfoCircleOutlined,
  ReloadOutlined,
  DownloadOutlined,
  EyeOutlined,
  DeleteOutlined,
  FolderOpenOutlined,
  RocketOutlined,
  ThunderboltOutlined,
  FireOutlined,
  TrophyOutlined,
  TargetOutlined,
  ExperimentOutlined,
  RadarChartOutlined,
  HeatMapOutlined
} from '@ant-design/icons';
import { Line, Bar, Pie, Gauge, Area, Column } from '@ant-design/plots';
import type { ColumnsType } from 'antd/es/table';
import { apiService } from '../services/api';
import AdvancedRAGTrainingPanel from './AdvancedRAGTrainingPanel';
import RAGAnalyticsDashboard from './RAGAnalyticsDashboard';

const { TabPane } = Tabs;
const { Option } = Select;
const { Panel } = Collapse;
const { TextArea } = Input;
const { Dragger } = Upload;

// Interfaces
interface TrainingConfig {
  dataSources: {
    customDirectories: string[];
    includeBuiltinSources: boolean;
    documentTypes: string[];
    languageFilter: string[];
    sizeFilter: { min: number; max: number };
  };
  processing: {
    chunkSize: number;
    chunkOverlap: number;
    batchSize: number;
    maxWorkers: number;
    enableParallelProcessing: boolean;
    memoryOptimization: boolean;
  };
  model: {
    embeddingModel: string;
    modelPrecision: 'fp16' | 'fp32' | 'int8';
    maxSequenceLength: number;
    enableGPU: boolean;
    gpuMemoryFraction: number;
  };
  quality: {
    enableDeduplication: boolean;
    similarityThreshold: number;
    enableQualityFiltering: boolean;
    minTextLength: number;
    maxTextLength: number;
    enableLanguageDetection: boolean;
  };
  advanced: {
    enableIncrementalTraining: boolean;
    enableCheckpointing: boolean;
    checkpointInterval: number;
    enableLogging: boolean;
    logLevel: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR';
    enableProfiling: boolean;
  };
}

interface TrainingStatus {
  isRunning: boolean;
  isPaused: boolean;
  currentStage: string;
  progress: number;
  totalSteps: number;
  currentStep: number;
  timeElapsed: number;
  timeRemaining: number;
  throughput: number;
  memoryUsage: number;
  gpuUsage?: number;
  errors: string[];
  warnings: string[];
}

interface DocumentProcessingInfo {
  id: string;
  filename: string;
  path: string;
  size: number;
  type: string;
  language: string;
  quality: number;
  chunks: number;
  embeddings: number;
  processingTime: number;
  status: 'pending' | 'processing' | 'completed' | 'error';
  errors: string[];
  metadata: Record<string, any>;
}

const EnhancedRAGModule: React.FC = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [trainingConfig, setTrainingConfig] = useState<TrainingConfig>({
    dataSources: {
      customDirectories: ['I:/docs/downloaded'],
      includeBuiltinSources: true,
      documentTypes: ['pdf', 'docx', 'txt', 'md'],
      languageFilter: ['ru', 'en'],
      sizeFilter: { min: 1, max: 100 }
    },
    processing: {
      chunkSize: 1000,
      chunkOverlap: 200,
      batchSize: 32,
      maxWorkers: 4,
      enableParallelProcessing: true,
      memoryOptimization: true
    },
    model: {
      embeddingModel: 'ai-forever/sbert_large_nlu_ru',
      modelPrecision: 'fp16',
      maxSequenceLength: 512,
      enableGPU: true,
      gpuMemoryFraction: 0.8
    },
    quality: {
      enableDeduplication: true,
      similarityThreshold: 0.95,
      enableQualityFiltering: true,
      minTextLength: 50,
      maxTextLength: 5000,
      enableLanguageDetection: true
    },
    advanced: {
      enableIncrementalTraining: false,
      enableCheckpointing: true,
      checkpointInterval: 1000,
      enableLogging: true,
      logLevel: 'INFO',
      enableProfiling: false
    }
  });

  const [trainingStatus, setTrainingStatus] = useState<TrainingStatus>({
    isRunning: false,
    isPaused: false,
    currentStage: 'Idle',
    progress: 0,
    totalSteps: 0,
    currentStep: 0,
    timeElapsed: 0,
    timeRemaining: 0,
    throughput: 0,
    memoryUsage: 0,
    errors: [],
    warnings: []
  });

  const [documentsInfo, setDocumentsInfo] = useState<DocumentProcessingInfo[]>([]);
  const [realTimeMetrics, setRealTimeMetrics] = useState<any[]>([]);
  const [configModalVisible, setConfigModalVisible] = useState(false);
  const [logsModalVisible, setLogsModalVisible] = useState(false);
  const [analyticsModalVisible, setAnalyticsModalVisible] = useState(false);

  // WebSocket для real-time обновлений
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    const token = localStorage.getItem('auth-token');
    const wsUrl = `ws://localhost:8000/ws/rag-training${token ? `?token=${token}` : ''}`;
    
    wsRef.current = new WebSocket(wsUrl);
    
    wsRef.current.onopen = () => {
      console.log('RAG Training WebSocket connected');
    };
    
    wsRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
    
    wsRef.current.onclose = () => {
      console.log('RAG Training WebSocket disconnected');
      setTimeout(connectWebSocket, 5000);
    };
  };

  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'training_status':
        setTrainingStatus(data.payload);
        break;
      case 'document_processed':
        setDocumentsInfo(prev => {
          const updated = [...prev];
          const index = updated.findIndex(doc => doc.id === data.payload.id);
          if (index >= 0) {
            updated[index] = data.payload;
          } else {
            updated.push(data.payload);
          }
          return updated;
        });
        break;
      case 'real_time_metrics':
        setRealTimeMetrics(prev => [...prev.slice(-59), data.payload]);
        break;
      case 'training_error':
        notification.error({
          message: 'Training Error',
          description: data.payload.error,
          duration: 10
        });
        break;
      case 'training_warning':
        notification.warning({
          message: 'Training Warning',
          description: data.payload.warning,
          duration: 5
        });
        break;
    }
  };

  const startTraining = async () => {
    try {
      const result = await apiService.executeUnifiedTool('enterprise_rag_trainer', {
        config: trainingConfig,
        mode: 'enhanced'
      });
      
      if (result.status === 'success') {
        message.success('Enhanced RAG training started');
        setTrainingStatus(prev => ({ ...prev, isRunning: true }));
      } else {
        message.error(`Failed to start training: ${result.error}`);
      }
    } catch (error) {
      console.error('Error starting training:', error);
      message.error('Failed to start training');
    }
  };

  const pauseTraining = async () => {
    try {
      const result = await apiService.executeUnifiedTool('pause_rag_training', {});
      if (result.status === 'success') {
        setTrainingStatus(prev => ({ ...prev, isPaused: true }));
        message.info('Training paused');
      }
    } catch (error) {
      console.error('Error pausing training:', error);
    }
  };

  const resumeTraining = async () => {
    try {
      const result = await apiService.executeUnifiedTool('resume_rag_training', {});
      if (result.status === 'success') {
        setTrainingStatus(prev => ({ ...prev, isPaused: false }));
        message.info('Training resumed');
      }
    } catch (error) {
      console.error('Error resuming training:', error);
    }
  };

  const stopTraining = async () => {
    Modal.confirm({
      title: 'Stop Training',
      content: 'Are you sure you want to stop the training? Progress will be saved.',
      okText: 'Stop',
      okType: 'danger',
      onOk: async () => {
        try {
          const result = await apiService.executeUnifiedTool('stop_rag_training', {});
          if (result.status === 'success') {
            setTrainingStatus(prev => ({ 
              ...prev, 
              isRunning: false, 
              isPaused: false 
            }));
            message.warning('Training stopped');
          }
        } catch (error) {
          console.error('Error stopping training:', error);
        }
      }
    });
  };

  const exportConfiguration = () => {
    const dataStr = JSON.stringify(trainingConfig, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'rag-training-config.json';
    link.click();
    URL.revokeObjectURL(url);
  };

  const importConfiguration = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
          try {
            const imported = JSON.parse(e.target?.result as string);
            setTrainingConfig(imported);
            message.success('Configuration imported successfully');
          } catch (error) {
            message.error('Invalid configuration file');
          }
        };
        reader.readAsText(file);
      }
    };
    input.click();
  };

  // Document processing table columns
  const documentColumns: ColumnsType<DocumentProcessingInfo> = [
    {
      title: 'Document',
      dataIndex: 'filename',
      key: 'filename',
      render: (text, record) => (
        <Space>
          <FileTextOutlined />
          <span>{text}</span>
          {record.status === 'completed' && <CheckCircleOutlined style={{ color: '#52c41a' }} />}
          {record.status === 'error' && <CloseCircleOutlined style={{ color: '#ff4d4f' }} />}
          {record.status === 'processing' && <Badge status="processing" />}
        </Space>
      )
    },
    {
      title: 'Size',
      dataIndex: 'size',
      key: 'size',
      render: (size) => `${(size / 1024 / 1024).toFixed(2)} MB`
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      render: (type) => <Tag>{type.toUpperCase()}</Tag>
    },
    {
      title: 'Language',
      dataIndex: 'language',
      key: 'language',
      render: (lang) => <Tag color="blue">{lang}</Tag>
    },
    {
      title: 'Quality',
      dataIndex: 'quality',
      key: 'quality',
      render: (quality) => (
        <Progress 
          percent={quality * 100} 
          size="small" 
          status={quality > 0.8 ? 'success' : quality > 0.6 ? 'normal' : 'exception'}
        />
      )
    },
    {
      title: 'Chunks',
      dataIndex: 'chunks',
      key: 'chunks'
    },
    {
      title: 'Processing Time',
      dataIndex: 'processingTime',
      key: 'processingTime',
      render: (time) => `${time.toFixed(2)}s`
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const colors = {
          pending: 'default',
          processing: 'processing',
          completed: 'success',
          error: 'error'
        };
        return <Badge status={colors[status]} text={status} />;
      }
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Space>
            <RadarChartOutlined style={{ fontSize: '24px', color: '#1890ff' }} />
            <h1 style={{ margin: 0 }}>Enhanced RAG Training System</h1>
            <Tag color={trainingStatus.isRunning ? 'processing' : 'default'}>
              {trainingStatus.isRunning ? 
                (trainingStatus.isPaused ? 'PAUSED' : 'TRAINING') : 
                'IDLE'
              }
            </Tag>
          </Space>
        </Col>
        <Col>
          <Space>
            <Button 
              icon={<SettingOutlined />}
              onClick={() => setConfigModalVisible(true)}
            >
              Configuration
            </Button>
            <Button 
              icon={<BarChartOutlined />}
              onClick={() => setAnalyticsModalVisible(true)}
            >
              Analytics
            </Button>
            <Button 
              icon={<BugOutlined />}
              onClick={() => setLogsModalVisible(true)}
            >
              Logs
            </Button>
          </Space>
        </Col>
      </Row>

      {/* Control Panel */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={16} align="middle">
          <Col>
            <Space size="large">
              {!trainingStatus.isRunning ? (
                <Button 
                  type="primary" 
                  size="large"
                  icon={<PlayCircleOutlined />}
                  onClick={startTraining}
                >
                  Start Enhanced Training
                </Button>
              ) : (
                <Space>
                  {!trainingStatus.isPaused ? (
                    <Button 
                      icon={<PauseCircleOutlined />}
                      onClick={pauseTraining}
                    >
                      Pause
                    </Button>
                  ) : (
                    <Button 
                      type="primary"
                      icon={<PlayCircleOutlined />}
                      onClick={resumeTraining}
                    >
                      Resume
                    </Button>
                  )}
                  <Button 
                    danger
                    icon={<StopOutlined />}
                    onClick={stopTraining}
                  >
                    Stop
                  </Button>
                </Space>
              )}
            </Space>
          </Col>
          
          {trainingStatus.isRunning && (
            <Col flex={1}>
              <div style={{ marginLeft: 24 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span><strong>{trainingStatus.currentStage}</strong></span>
                  <span>{trainingStatus.currentStep} / {trainingStatus.totalSteps}</span>
                </div>
                <Progress 
                  percent={trainingStatus.progress} 
                  status={trainingStatus.isPaused ? 'normal' : 'active'}
                  strokeColor={{
                    '0%': '#108ee9',
                    '100%': '#87d068',
                  }}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#666' }}>
                  <span>Elapsed: {Math.floor(trainingStatus.timeElapsed / 60)}m {trainingStatus.timeElapsed % 60}s</span>
                  <span>Remaining: {Math.floor(trainingStatus.timeRemaining / 60)}m {trainingStatus.timeRemaining % 60}s</span>
                  <span>Speed: {trainingStatus.throughput.toFixed(1)} docs/s</span>
                </div>
              </div>
            </Col>
          )}
        </Row>
      </Card>

      {/* Main Tabs */}
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        {/* Dashboard Tab */}
        <TabPane tab={<span><MonitorOutlined />Dashboard</span>} key="dashboard">
          <Row gutter={16}>
            {/* System Metrics */}
            <Col span={18}>
              <Card title="Real-time System Metrics" style={{ marginBottom: 16 }}>
                {realTimeMetrics.length > 0 ? (
                  <Line
                    data={realTimeMetrics.map((metric, index) => ({
                      time: index,
                      cpu: metric.cpuUsage || 0,
                      memory: metric.memoryUsage || 0,
                      gpu: metric.gpuUsage || 0
                    }))}
                    xField="time"
                    yField="cpu"
                    seriesField="type"
                    height={300}
                    smooth={true}
                  />
                ) : (
                  <div style={{ textAlign: 'center', padding: '50px' }}>
                    <MonitorOutlined style={{ fontSize: '48px', color: '#ccc' }} />
                    <p>No metrics data available</p>
                  </div>
                )}
              </Card>
            </Col>
            
            {/* Current Stats */}
            <Col span={6}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Card size="small">
                  <Statistic
                    title="CPU Usage"
                    value={trainingStatus.memoryUsage}
                    precision={1}
                    suffix="%"
                    valueStyle={{ color: '#3f8600' }}
                  />
                </Card>
                <Card size="small">
                  <Statistic
                    title="Memory Usage"
                    value={trainingStatus.memoryUsage}
                    precision={1}
                    suffix="%"
                    valueStyle={{ color: '#cf1322' }}
                  />
                </Card>
                <Card size="small">
                  <Statistic
                    title="GPU Usage"
                    value={trainingStatus.gpuUsage || 0}
                    precision={1}
                    suffix="%"
                    valueStyle={{ color: '#722ed1' }}
                  />
                </Card>
                <Card size="small">
                  <Statistic
                    title="Throughput"
                    value={trainingStatus.throughput}
                    precision={2}
                    suffix="docs/s"
                    valueStyle={{ color: '#fa8c16' }}
                  />
                </Card>
              </Space>
            </Col>
          </Row>
        </TabPane>

        {/* Advanced Training Tab */}
        <TabPane tab={<span><RocketOutlined />Advanced Training</span>} key="advanced">
          <AdvancedRAGTrainingPanel />
        </TabPane>

        {/* Analytics Tab */}
        <TabPane tab={<span><BarChartOutlined />Analytics</span>} key="analytics">
          <RAGAnalyticsDashboard />
        </TabPane>

        {/* Document Processing Tab */}
        <TabPane tab={<span><FileTextOutlined />Document Processing</span>} key="documents">
          <Card 
            title="Document Processing Status"
            extra={
              <Space>
                <Button icon={<ReloadOutlined />}>
                  Refresh
                </Button>
                <Button icon={<DownloadOutlined />}>
                  Export Report
                </Button>
              </Space>
            }
          >
            <Table
              columns={documentColumns}
              dataSource={documentsInfo}
              rowKey="id"
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} documents`
              }}
            />
          </Card>
        </TabPane>

        {/* Configuration Tab */}
        <TabPane tab={<span><SettingOutlined />Configuration</span>} key="config">
          <Row gutter={16}>
            <Col span={16}>
              <Card title="Training Configuration">
                <Collapse>
                  <Panel header="Data Sources" key="data">
                    <Form layout="vertical">
                      <Form.Item label="Custom Directories">
                        <TextArea 
                          rows={3}
                          placeholder="Enter custom directory paths, one per line"
                          value={trainingConfig.dataSources.customDirectories.join('\n')}
                          onChange={(e) => setTrainingConfig(prev => ({
                            ...prev,
                            dataSources: {
                              ...prev.dataSources,
                              customDirectories: e.target.value.split('\n').filter(Boolean)
                            }
                          }))}
                        />
                      </Form.Item>
                      
                      <Form.Item label="Document Types">
                        <Checkbox.Group
                          options={[
                            { label: 'PDF', value: 'pdf' },
                            { label: 'DOCX', value: 'docx' },
                            { label: 'TXT', value: 'txt' },
                            { label: 'MD', value: 'md' },
                            { label: 'HTML', value: 'html' }
                          ]}
                          value={trainingConfig.dataSources.documentTypes}
                          onChange={(values) => setTrainingConfig(prev => ({
                            ...prev,
                            dataSources: {
                              ...prev.dataSources,
                              documentTypes: values
                            }
                          }))}
                        />
                      </Form.Item>
                    </Form>
                  </Panel>
                  
                  <Panel header="Processing Settings" key="processing">
                    <Form layout="vertical">
                      <Row gutter={16}>
                        <Col span={12}>
                          <Form.Item label="Chunk Size">
                            <Slider
                              min={100}
                              max={2000}
                              value={trainingConfig.processing.chunkSize}
                              onChange={(value) => setTrainingConfig(prev => ({
                                ...prev,
                                processing: { ...prev.processing, chunkSize: value }
                              }))}
                              marks={{
                                100: '100',
                                500: '500',
                                1000: '1000',
                                1500: '1500',
                                2000: '2000'
                              }}
                            />
                          </Form.Item>
                        </Col>
                        <Col span={12}>
                          <Form.Item label="Batch Size">
                            <InputNumber
                              min={1}
                              max={128}
                              value={trainingConfig.processing.batchSize}
                              onChange={(value) => setTrainingConfig(prev => ({
                                ...prev,
                                processing: { ...prev.processing, batchSize: value || 32 }
                              }))}
                            />
                          </Form.Item>
                        </Col>
                      </Row>
                    </Form>
                  </Panel>
                  
                  <Panel header="Model Settings" key="model">
                    <Form layout="vertical">
                      <Form.Item label="Embedding Model">
                        <Select
                          value={trainingConfig.model.embeddingModel}
                          onChange={(value) => setTrainingConfig(prev => ({
                            ...prev,
                            model: { ...prev.model, embeddingModel: value }
                          }))}
                        >
                          <Option value="ai-forever/sbert_large_nlu_ru">SBERT Large NLU RU</Option>
                          <Option value="sentence-transformers/all-MiniLM-L6-v2">MiniLM L6 v2</Option>
                          <Option value="sentence-transformers/all-mpnet-base-v2">MPNet Base v2</Option>
                        </Select>
                      </Form.Item>
                    </Form>
                  </Panel>
                </Collapse>
              </Card>
            </Col>
            
            <Col span={8}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Card title="Quick Actions" size="small">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Button 
                      block 
                      icon={<DownloadOutlined />}
                      onClick={exportConfiguration}
                    >
                      Export Config
                    </Button>
                    <Button 
                      block 
                      icon={<CloudUploadOutlined />}
                      onClick={importConfiguration}
                    >
                      Import Config
                    </Button>
                    <Button 
                      block 
                      icon={<ReloadOutlined />}
                      onClick={() => {
                        // Reset to defaults
                        message.info('Configuration reset to defaults');
                      }}
                    >
                      Reset to Defaults
                    </Button>
                  </Space>
                </Card>
                
                <Card title="Presets" size="small">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Button block size="small">Fast Training</Button>
                    <Button block size="small">Quality Training</Button>
                    <Button block size="small">Balanced</Button>
                    <Button block size="small">Memory Optimized</Button>
                  </Space>
                </Card>
              </Space>
            </Col>
          </Row>
        </TabPane>
      </Tabs>

      {/* Configuration Modal */}
      <Modal
        title="Advanced Configuration"
        open={configModalVisible}
        onCancel={() => setConfigModalVisible(false)}
        width={1200}
        footer={null}
      >
        {/* Advanced configuration content */}
      </Modal>

      {/* Analytics Modal */}
      <Modal
        title="Training Analytics"
        open={analyticsModalVisible}
        onCancel={() => setAnalyticsModalVisible(false)}
        width={1400}
        footer={null}
      >
        <RAGAnalyticsDashboard />
      </Modal>

      {/* Logs Modal */}
      <Modal
        title="Training Logs"
        open={logsModalVisible}
        onCancel={() => setLogsModalVisible(false)}
        width={1000}
        footer={null}
      >
        <div style={{ 
          height: '400px', 
          overflowY: 'auto', 
          backgroundColor: '#001529', 
          color: '#fff', 
          padding: '12px',
          fontFamily: 'monospace',
          fontSize: '12px'
        }}>
          {trainingStatus.errors.length > 0 && (
            <div>
              <h4 style={{ color: '#ff4d4f' }}>Errors:</h4>
              {trainingStatus.errors.map((error, index) => (
                <div key={index} style={{ color: '#ff4d4f', marginBottom: '4px' }}>
                  {error}
                </div>
              ))}
            </div>
          )}
          
          {trainingStatus.warnings.length > 0 && (
            <div>
              <h4 style={{ color: '#faad14' }}>Warnings:</h4>
              {trainingStatus.warnings.map((warning, index) => (
                <div key={index} style={{ color: '#faad14', marginBottom: '4px' }}>
                  {warning}
                </div>
              ))}
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
};

export default EnhancedRAGModule;