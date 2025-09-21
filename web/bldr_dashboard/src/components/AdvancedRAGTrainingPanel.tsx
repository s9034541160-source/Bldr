/**
 * Advanced RAG Training Panel
 * Comprehensive RAG training management with real-time analytics and maximum control
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  Row,
  Col,
  Button,
  Progress,
  Statistic,
  Table,
  Tag,
  Select,
  InputNumber,
  Switch,
  Slider,
  Form,
  Input,
  Tabs,
  Alert,
  Modal,
  Tooltip,
  Space,
  Divider,
  Timeline,
  Badge,
  Spin,
  message,
  Upload,
  Tree,
  Collapse,
  Radio,
  Checkbox,
  DatePicker,
  List,
  Avatar
} from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  SettingOutlined,
  BarChartOutlined,
  FileTextOutlined,
  DatabaseOutlined,
  MonitorOutlined,
  ExperimentOutlined,
  CloudUploadOutlined,
  FolderOpenOutlined,
  LineChartOutlined,
  ThunderboltOutlined,
  BugOutlined,
  SaveOutlined,
  LoadingOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  WarningOutlined,
  InfoCircleOutlined,
  DownloadOutlined,
  EyeOutlined,
  DeleteOutlined,
  ReloadOutlined,
  FilterOutlined,
  SearchOutlined,
  RocketOutlined,
  FireOutlined,
  TrophyOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { Line, Bar, Pie, Gauge } from '@ant-design/plots';
import { apiService } from '../services/api';
import { useStore } from '../store';

const { TabPane } = Tabs;
const { Option } = Select;
const { Panel } = Collapse;
const { RangePicker } = DatePicker;
const { TextArea } = Input;

// Interfaces for training data
interface TrainingConfig {
  // Data Sources
  dataSources: {
    customDirectories: string[];
    includeBuiltinSources: boolean;
    documentTypes: string[];
    languageFilter: string[];
    dateRange: [string, string] | null;
    sizeFilter: { min: number; max: number };
  };
  
  // Processing Settings
  processing: {
    chunkSize: number;
    chunkOverlap: number;
    batchSize: number;
    maxWorkers: number;
    enableParallelProcessing: boolean;
    memoryOptimization: boolean;
  };
  
  // Model Settings
  model: {
    embeddingModel: string;
    modelPrecision: 'fp16' | 'fp32' | 'int8';
    maxSequenceLength: number;
    enableGPU: boolean;
    gpuMemoryFraction: number;
  };
  
  // Quality Settings
  quality: {
    enableDeduplication: boolean;
    similarityThreshold: number;
    enableQualityFiltering: boolean;
    minTextLength: number;
    maxTextLength: number;
    enableLanguageDetection: boolean;
  };
  
  // Advanced Settings
  advanced: {
    enableIncrementalTraining: boolean;
    enableCheckpointing: boolean;
    checkpointInterval: number;
    enableLogging: boolean;
    logLevel: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR';
    enableProfiling: boolean;
  };
}

interface TrainingProgress {
  stage: string;
  substage?: string;
  progress: number;
  totalSteps: number;
  currentStep: number;
  timeElapsed: number;
  timeRemaining: number;
  throughput: number;
  memoryUsage: number;
  gpuUsage?: number;
  log: string;
  errors: string[];
  warnings: string[];
}

interface TrainingMetrics {
  documentsProcessed: number;
  chunksGenerated: number;
  embeddingsCreated: number;
  duplicatesRemoved: number;
  qualityFiltered: number;
  averageChunkSize: number;
  processingSpeed: number;
  memoryPeak: number;
  errorRate: number;
}

interface DocumentAnalysis {
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
}

interface RealTimeStats {
  timestamp: string;
  cpuUsage: number;
  memoryUsage: number;
  gpuUsage?: number;
  diskIO: number;
  networkIO: number;
  throughput: number;
  queueSize: number;
}

const AdvancedRAGTrainingPanel: React.FC = () => {
  // Main state
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isTraining, setIsTraining] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [trainingProgress, setTrainingProgress] = useState<TrainingProgress | null>(null);
  const [trainingMetrics, setTrainingMetrics] = useState<TrainingMetrics | null>(null);
  
  // Configuration state
  const [trainingConfig, setTrainingConfig] = useState<TrainingConfig>({
    dataSources: {
      customDirectories: [],
      includeBuiltinSources: true,
      documentTypes: ['pdf', 'docx', 'txt', 'md'],
      languageFilter: ['ru', 'en'],
      dateRange: null,
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
  
  // Analytics state
  const [documentAnalysis, setDocumentAnalysis] = useState<DocumentAnalysis[]>([]);
  const [realTimeStats, setRealTimeStats] = useState<RealTimeStats[]>([]);
  const [performanceHistory, setPerformanceHistory] = useState<any[]>([]);
  
  // UI state
  const [configModalVisible, setConfigModalVisible] = useState(false);
  const [analyticsModalVisible, setAnalyticsModalVisible] = useState(false);
  const [selectedDocuments, setSelectedDocuments] = useState<string[]>([]);
  const [logFilter, setLogFilter] = useState('all');
  const [autoRefresh, setAutoRefresh] = useState(true);
  
  // WebSocket and intervals
  const wsRef = useRef<WebSocket | null>(null);
  const statsIntervalRef = useRef<NodeJS.Timeout | null>(null);
  
  // Initialize WebSocket connection for real-time updates
  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (statsIntervalRef.current) {
        clearInterval(statsIntervalRef.current);
      }
    };
  }, []);
  
  // Auto-refresh stats
  useEffect(() => {
    if (autoRefresh && isTraining) {
      statsIntervalRef.current = setInterval(() => {
        fetchRealTimeStats();
      }, 1000);
    } else if (statsIntervalRef.current) {
      clearInterval(statsIntervalRef.current);
    }
    
    return () => {
      if (statsIntervalRef.current) {
        clearInterval(statsIntervalRef.current);
      }
    };
  }, [autoRefresh, isTraining]);
  
  const connectWebSocket = () => {
    // Get token from localStorage with correct key
    const token = localStorage.getItem('auth-token');
    const wsUrl = `ws://localhost:3001/ws${token ? `?token=${token}` : ''}`;
    
    wsRef.current = new WebSocket(wsUrl);
    
    wsRef.current.onopen = () => {
      console.log('Training WebSocket connected');
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
      console.log('Training WebSocket disconnected');
      // Attempt to reconnect after 5 seconds
      setTimeout(connectWebSocket, 5000);
    };
    
    wsRef.current.onerror = (error) => {
      console.error('Training WebSocket error:', error);
    };
  };
  
  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'training_progress':
        setTrainingProgress(data.payload);
        break;
      case 'training_metrics':
        setTrainingMetrics(data.payload);
        break;
      case 'document_analysis':
        setDocumentAnalysis(prev => {
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
      case 'real_time_stats':
        setRealTimeStats(prev => [...prev.slice(-59), data.payload]);
        break;
      case 'training_started':
        setIsTraining(true);
        setIsPaused(false);
        message.success('Training started successfully');
        break;
      case 'training_paused':
        setIsPaused(true);
        message.info('Training paused');
        break;
      case 'training_resumed':
        setIsPaused(false);
        message.info('Training resumed');
        break;
      case 'training_stopped':
        setIsTraining(false);
        setIsPaused(false);
        message.warning('Training stopped');
        break;
      case 'training_completed':
        setIsTraining(false);
        setIsPaused(false);
        message.success('Training completed successfully!');
        break;
      case 'training_error':
        setIsTraining(false);
        setIsPaused(false);
        message.error(`Training error: ${data.payload.error}`);
        break;
    }
  };
  
  const fetchRealTimeStats = async () => {
    try {
      const stats = await apiService.executeUnifiedTool('get_training_stats', {});
      if (stats.status === 'success' && stats.data) {
        setRealTimeStats(prev => [...prev.slice(-59), {
          ...stats.data,
          timestamp: new Date().toISOString()
        }]);
      }
    } catch (error) {
      console.error('Error fetching real-time stats:', error);
    }
  };
  
  const startTraining = async () => {
    try {
      const result = await apiService.executeUnifiedTool('enterprise_rag_trainer', {
        config: trainingConfig,
        mode: 'advanced'
      });
      
      if (result.status === 'success') {
        setIsTraining(true);
        message.success('Advanced RAG training started');
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
      const result = await apiService.executeUnifiedTool('pause_training', {});
      if (result.status === 'success') {
        setIsPaused(true);
      }
    } catch (error) {
      console.error('Error pausing training:', error);
    }
  };
  
  const resumeTraining = async () => {
    try {
      const result = await apiService.executeUnifiedTool('resume_training', {});
      if (result.status === 'success') {
        setIsPaused(false);
      }
    } catch (error) {
      console.error('Error resuming training:', error);
    }
  };
  
  const stopTraining = async () => {
    Modal.confirm({
      title: 'Stop Training',
      content: 'Are you sure you want to stop the training? All progress will be lost.',
      okText: 'Stop',
      okType: 'danger',
      onOk: async () => {
        try {
          const result = await apiService.executeUnifiedTool('stop_training', {});
          if (result.status === 'success') {
            setIsTraining(false);
            setIsPaused(false);
          }
        } catch (error) {
          console.error('Error stopping training:', error);
        }
      }
    });
  };
  
  const saveConfiguration = () => {
    localStorage.setItem('rag_training_config', JSON.stringify(trainingConfig));
    message.success('Configuration saved');
  };
  
  const loadConfiguration = () => {
    const saved = localStorage.getItem('rag_training_config');
    if (saved) {
      setTrainingConfig(JSON.parse(saved));
      message.success('Configuration loaded');
    }
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
  
  // Performance chart data
  const performanceChartData = realTimeStats.map((stat, index) => ({
    time: index,
    cpu: stat.cpuUsage,
    memory: stat.memoryUsage,
    gpu: stat.gpuUsage || 0,
    throughput: stat.throughput
  }));
  
  // Document analysis columns
  const documentColumns: ColumnsType<DocumentAnalysis> = [
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
          {record.status === 'processing' && <LoadingOutlined style={{ color: '#1890ff' }} />}
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
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Tooltip title="View Details">
            <Button 
              type="text" 
              icon={<EyeOutlined />} 
              onClick={() => showDocumentDetails(record)}
            />
          </Tooltip>
          {record.errors.length > 0 && (
            <Tooltip title="View Errors">
              <Button 
                type="text" 
                icon={<BugOutlined />} 
                danger
                onClick={() => showDocumentErrors(record)}
              />
            </Tooltip>
          )}
        </Space>
      )
    }
  ];
  
  const showDocumentDetails = (document: DocumentAnalysis) => {
    Modal.info({
      title: `Document Details: ${document.filename}`,
      width: 800,
      content: (
        <div>
          <Descriptions column={2}>
            <Descriptions.Item label="Path">{document.path}</Descriptions.Item>
            <Descriptions.Item label="Size">{(document.size / 1024 / 1024).toFixed(2)} MB</Descriptions.Item>
            <Descriptions.Item label="Type">{document.type}</Descriptions.Item>
            <Descriptions.Item label="Language">{document.language}</Descriptions.Item>
            <Descriptions.Item label="Quality Score">{(document.quality * 100).toFixed(1)}%</Descriptions.Item>
            <Descriptions.Item label="Chunks Generated">{document.chunks}</Descriptions.Item>
            <Descriptions.Item label="Embeddings Created">{document.embeddings}</Descriptions.Item>
            <Descriptions.Item label="Processing Time">{document.processingTime.toFixed(2)}s</Descriptions.Item>
          </Descriptions>
        </div>
      )
    });
  };
  
  const showDocumentErrors = (document: DocumentAnalysis) => {
    Modal.error({
      title: `Errors for: ${document.filename}`,
      content: (
        <List
          dataSource={document.errors}
          renderItem={(error, index) => (
            <List.Item>
              <List.Item.Meta
                avatar={<Avatar icon={<BugOutlined />} />}
                title={`Error ${index + 1}`}
                description={error}
              />
            </List.Item>
          )}
        />
      )
    });
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Space>
            <RocketOutlined style={{ fontSize: '24px', color: '#1890ff' }} />
            <h1 style={{ margin: 0 }}>Advanced RAG Training Control Center</h1>
            <Tag color={isTraining ? 'processing' : 'default'}>
              {isTraining ? (isPaused ? 'PAUSED' : 'TRAINING') : 'IDLE'}
            </Tag>
          </Space>
        </Col>
        <Col>
          <Space>
            <Switch 
              checked={autoRefresh} 
              onChange={setAutoRefresh}
              checkedChildren="Auto Refresh"
              unCheckedChildren="Manual"
            />
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
          </Space>
        </Col>
      </Row>

      {/* Control Panel */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={16} align="middle">
          <Col>
            <Space size="large">
              {!isTraining ? (
                <Button 
                  type="primary" 
                  size="large"
                  icon={<PlayCircleOutlined />}
                  onClick={startTraining}
                >
                  Start Training
                </Button>
              ) : (
                <Space>
                  {!isPaused ? (
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
          
          {trainingProgress && (
            <Col flex={1}>
              <div style={{ marginLeft: 24 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span><strong>{trainingProgress.stage}</strong></span>
                  <span>{trainingProgress.currentStep} / {trainingProgress.totalSteps}</span>
                </div>
                <Progress 
                  percent={trainingProgress.progress} 
                  status={isPaused ? 'normal' : 'active'}
                  strokeColor={{
                    '0%': '#108ee9',
                    '100%': '#87d068',
                  }}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#666' }}>
                  <span>Elapsed: {Math.floor(trainingProgress.timeElapsed / 60)}m {trainingProgress.timeElapsed % 60}s</span>
                  <span>Remaining: {Math.floor(trainingProgress.timeRemaining / 60)}m {trainingProgress.timeRemaining % 60}s</span>
                  <span>Speed: {trainingProgress.throughput.toFixed(1)} docs/s</span>
                </div>
              </div>
            </Col>
          )}
        </Row>
      </Card>

      {/* Main Content Tabs */}
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        {/* Dashboard Tab */}
        <TabPane tab={<span><MonitorOutlined />Dashboard</span>} key="dashboard">
          <Row gutter={16}>
            {/* Real-time Metrics */}
            <Col span={18}>
              <Card title="Real-time Performance" style={{ marginBottom: 16 }}>
                {realTimeStats.length > 0 ? (
                  <Line
                    data={performanceChartData}
                    xField="time"
                    yField="cpu"
                    seriesField="type"
                    height={300}
                    smooth={true}
                    animation={{
                      appear: {
                        animation: 'path-in',
                        duration: 1000,
                      },
                    }}
                  />
                ) : (
                  <div style={{ textAlign: 'center', padding: '50px' }}>
                    <MonitorOutlined style={{ fontSize: '48px', color: '#ccc' }} />
                    <p>No performance data available</p>
                  </div>
                )}
              </Card>
            </Col>
            
            {/* System Stats */}
            <Col span={6}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Card size="small">
                  <Statistic
                    title="CPU Usage"
                    value={realTimeStats[realTimeStats.length - 1]?.cpuUsage || 0}
                    precision={1}
                    suffix="%"
                    valueStyle={{ color: '#3f8600' }}
                  />
                </Card>
                <Card size="small">
                  <Statistic
                    title="Memory Usage"
                    value={realTimeStats[realTimeStats.length - 1]?.memoryUsage || 0}
                    precision={1}
                    suffix="%"
                    valueStyle={{ color: '#cf1322' }}
                  />
                </Card>
                <Card size="small">
                  <Statistic
                    title="GPU Usage"
                    value={realTimeStats[realTimeStats.length - 1]?.gpuUsage || 0}
                    precision={1}
                    suffix="%"
                    valueStyle={{ color: '#722ed1' }}
                  />
                </Card>
                <Card size="small">
                  <Statistic
                    title="Throughput"
                    value={realTimeStats[realTimeStats.length - 1]?.throughput || 0}
                    precision={2}
                    suffix="docs/s"
                    valueStyle={{ color: '#fa8c16' }}
                  />
                </Card>
              </Space>
            </Col>
          </Row>
          
          {/* Training Metrics */}
          {trainingMetrics && (
            <Row gutter={16} style={{ marginTop: 16 }}>
              <Col span={24}>
                <Card title="Training Metrics">
                  <Row gutter={16}>
                    <Col span={4}>
                      <Statistic
                        title="Documents Processed"
                        value={trainingMetrics.documentsProcessed}
                        prefix={<FileTextOutlined />}
                      />
                    </Col>
                    <Col span={4}>
                      <Statistic
                        title="Chunks Generated"
                        value={trainingMetrics.chunksGenerated}
                        prefix={<DatabaseOutlined />}
                      />
                    </Col>
                    <Col span={4}>
                      <Statistic
                        title="Embeddings Created"
                        value={trainingMetrics.embeddingsCreated}
                        prefix={<ThunderboltOutlined />}
                      />
                    </Col>
                    <Col span={4}>
                      <Statistic
                        title="Duplicates Removed"
                        value={trainingMetrics.duplicatesRemoved}
                        prefix={<DeleteOutlined />}
                      />
                    </Col>
                    <Col span={4}>
                      <Statistic
                        title="Processing Speed"
                        value={trainingMetrics.processingSpeed}
                        precision={2}
                        suffix="MB/s"
                        prefix={<RocketOutlined />}
                      />
                    </Col>
                    <Col span={4}>
                      <Statistic
                        title="Error Rate"
                        value={trainingMetrics.errorRate}
                        precision={2}
                        suffix="%"
                        prefix={<BugOutlined />}
                        valueStyle={{ color: trainingMetrics.errorRate > 5 ? '#cf1322' : '#3f8600' }}
                      />
                    </Col>
                  </Row>
                </Card>
              </Col>
            </Row>
          )}
        </TabPane>

        {/* Document Analysis Tab */}
        <TabPane tab={<span><FileTextOutlined />Document Analysis</span>} key="documents">
          <Card 
            title="Document Processing Analysis"
            extra={
              <Space>
                <Select
                  placeholder="Filter by status"
                  style={{ width: 120 }}
                  allowClear
                  onChange={(value) => {
                    // Filter documents by status
                  }}
                >
                  <Option value="pending">Pending</Option>
                  <Option value="processing">Processing</Option>
                  <Option value="completed">Completed</Option>
                  <Option value="error">Error</Option>
                </Select>
                <Button icon={<ReloadOutlined />} onClick={() => {
                  // Refresh document analysis
                }}>
                  Refresh
                </Button>
              </Space>
            }
          >
            <Table
              columns={documentColumns}
              dataSource={documentAnalysis}
              rowKey="id"
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} documents`
              }}
              rowSelection={{
                selectedRowKeys: selectedDocuments,
                onChange: setSelectedDocuments,
              }}
            />
          </Card>
        </TabPane>

        {/* Logs Tab */}
        <TabPane tab={<span><BugOutlined />Logs & Debug</span>} key="logs">
          <Card 
            title="Training Logs"
            extra={
              <Space>
                <Select
                  value={logFilter}
                  onChange={setLogFilter}
                  style={{ width: 120 }}
                >
                  <Option value="all">All Logs</Option>
                  <Option value="error">Errors</Option>
                  <Option value="warning">Warnings</Option>
                  <Option value="info">Info</Option>
                  <Option value="debug">Debug</Option>
                </Select>
                <Button icon={<DownloadOutlined />}>
                  Export Logs
                </Button>
              </Space>
            }
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
              {trainingProgress?.log && (
                <Timeline mode="left">
                  {trainingProgress.log.split('\n').map((line, index) => (
                    <Timeline.Item 
                      key={index}
                      color={
                        line.includes('ERROR') ? 'red' :
                        line.includes('WARNING') ? 'orange' :
                        line.includes('INFO') ? 'blue' : 'green'
                      }
                    >
                      <span style={{ fontSize: '11px' }}>{line}</span>
                    </Timeline.Item>
                  ))}
                </Timeline>
              )}
            </div>
          </Card>
        </TabPane>
      </Tabs>

      {/* Configuration Modal */}
      <Modal
        title="Advanced Training Configuration"
        open={configModalVisible}
        onCancel={() => setConfigModalVisible(false)}
        width={1200}
        footer={[
          <Button key="load" onClick={loadConfiguration}>
            Load Saved
          </Button>,
          <Button key="save" onClick={saveConfiguration}>
            Save Config
          </Button>,
          <Button key="export" onClick={exportConfiguration}>
            Export
          </Button>,
          <Button key="cancel" onClick={() => setConfigModalVisible(false)}>
            Cancel
          </Button>,
          <Button key="apply" type="primary" onClick={() => setConfigModalVisible(false)}>
            Apply Configuration
          </Button>
        ]}
      >
        {/* Configuration form content would go here */}
        <Tabs>
          <TabPane tab="Data Sources" key="data">
            <Form layout="vertical">
              <Form.Item label="Custom Directories">
                <Input.TextArea 
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
          </TabPane>
          
          <TabPane tab="Processing" key="processing">
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
                  <Form.Item label="Chunk Overlap">
                    <Slider
                      min={0}
                      max={500}
                      value={trainingConfig.processing.chunkOverlap}
                      onChange={(value) => setTrainingConfig(prev => ({
                        ...prev,
                        processing: { ...prev.processing, chunkOverlap: value }
                      }))}
                    />
                  </Form.Item>
                </Col>
              </Row>
              
              <Row gutter={16}>
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
                <Col span={12}>
                  <Form.Item label="Max Workers">
                    <InputNumber
                      min={1}
                      max={16}
                      value={trainingConfig.processing.maxWorkers}
                      onChange={(value) => setTrainingConfig(prev => ({
                        ...prev,
                        processing: { ...prev.processing, maxWorkers: value || 4 }
                      }))}
                    />
                  </Form.Item>
                </Col>
              </Row>
            </Form>
          </TabPane>
          
          <TabPane tab="Model" key="model">
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
              
              <Form.Item label="Model Precision">
                <Radio.Group
                  value={trainingConfig.model.modelPrecision}
                  onChange={(e) => setTrainingConfig(prev => ({
                    ...prev,
                    model: { ...prev.model, modelPrecision: e.target.value }
                  }))}
                >
                  <Radio value="fp32">FP32 (Highest Quality)</Radio>
                  <Radio value="fp16">FP16 (Balanced)</Radio>
                  <Radio value="int8">INT8 (Fastest)</Radio>
                </Radio.Group>
              </Form.Item>
            </Form>
          </TabPane>
        </Tabs>
      </Modal>

      {/* Analytics Modal */}
      <Modal
        title="Advanced Analytics Dashboard"
        open={analyticsModalVisible}
        onCancel={() => setAnalyticsModalVisible(false)}
        width={1400}
        footer={null}
      >
        <Tabs>
          <TabPane tab="Performance Analytics" key="performance">
            {/* Performance charts and analytics */}
          </TabPane>
          <TabPane tab="Quality Metrics" key="quality">
            {/* Quality analysis charts */}
          </TabPane>
          <TabPane tab="Resource Usage" key="resources">
            {/* Resource usage analytics */}
          </TabPane>
        </Tabs>
      </Modal>
    </div>
  );
};

export default AdvancedRAGTrainingPanel;