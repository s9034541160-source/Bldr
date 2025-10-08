/**
 * RAG Analytics Dashboard
 * Comprehensive analytics and insights for RAG training process
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Tag,
  Progress,
  Tabs,
  Select,
  DatePicker,
  Button,
  Space,
  Tooltip,
  Alert,
  List,
  Avatar,
  Timeline,
  Descriptions,
  Badge,
  Divider,
  Typography,
  Collapse,
  Tree,
  Input,
  Slider,
  Switch
} from 'antd';
import {
  LineChartOutlined,
  BarChartOutlined,
  PieChartOutlined,
  TrophyOutlined,
  BugOutlined,
  FireOutlined,
  ThunderboltOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  ClockCircleOutlined,
  CloudOutlined,
  SearchOutlined,
  FilterOutlined,
  DownloadOutlined,
  EyeOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  InfoCircleOutlined,
  RocketOutlined,
  RadarChartOutlined,
  DotChartOutlined
} from '@ant-design/icons';
import { Line, Bar, Pie, Gauge, Heatmap, Scatter, Area, Column } from '@ant-design/plots';
import type { ColumnsType } from 'antd/es/table';

const { TabPane } = Tabs;
const { RangePicker } = DatePicker;
const { Text, Title } = Typography;
const { Panel } = Collapse;
const { Search } = Input;

// Analytics interfaces
interface QualityMetrics {
  overallScore: number;
  embeddingQuality: number;
  chunkCoherence: number;
  languageDetectionAccuracy: number;
  duplicateDetectionRate: number;
  processingAccuracy: number;
  semanticSimilarity: number;
  contextPreservation: number;
}

interface PerformanceMetrics {
  processingSpeed: number;
  memoryEfficiency: number;
  cpuUtilization: number;
  gpuUtilization: number;
  diskIORate: number;
  networkIORate: number;
  throughputTrend: Array<{ time: string; value: number }>;
  bottlenecks: string[];
}

interface DocumentInsights {
  totalDocuments: number;
  processedDocuments: number;
  failedDocuments: number;
  averageProcessingTime: number;
  documentTypes: Record<string, number>;
  languageDistribution: Record<string, number>;
  sizeDistribution: Record<string, number>;
  qualityDistribution: Record<string, number>;
}

interface EmbeddingAnalytics {
  totalEmbeddings: number;
  embeddingDimensions: number;
  averageEmbeddingTime: number;
  embeddingQualityScore: number;
  clusterAnalysis: Array<{ cluster: number; size: number; quality: number }>;
  similarityMatrix: number[][];
  outliers: Array<{ id: string; score: number; reason: string }>;
}

interface ErrorAnalysis {
  totalErrors: number;
  errorsByType: Record<string, number>;
  errorsByStage: Record<string, number>;
  criticalErrors: Array<{
    id: string;
    type: string;
    message: string;
    timestamp: string;
    document?: string;
    stage: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
  }>;
  errorTrends: Array<{ time: string; count: number; type: string }>;
}

interface OptimizationSuggestions {
  performance: Array<{
    category: string;
    suggestion: string;
    impact: 'low' | 'medium' | 'high';
    effort: 'low' | 'medium' | 'high';
    estimatedImprovement: string;
  }>;
  quality: Array<{
    category: string;
    suggestion: string;
    impact: 'low' | 'medium' | 'high';
    effort: 'low' | 'medium' | 'high';
    estimatedImprovement: string;
  }>;
  resources: Array<{
    category: string;
    suggestion: string;
    impact: 'low' | 'medium' | 'high';
    effort: 'low' | 'medium' | 'high';
    estimatedImprovement: string;
  }>;
}

const RAGAnalyticsDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [timeRange, setTimeRange] = useState<[string, string] | null>(null);
  const [refreshInterval, setRefreshInterval] = useState(30);
  const [autoRefresh, setAutoRefresh] = useState(true);
  
  // Analytics data state
  const [qualityMetrics, setQualityMetrics] = useState<QualityMetrics | null>(null);
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetrics | null>(null);
  const [documentInsights, setDocumentInsights] = useState<DocumentInsights | null>(null);
  const [embeddingAnalytics, setEmbeddingAnalytics] = useState<EmbeddingAnalytics | null>(null);
  const [errorAnalysis, setErrorAnalysis] = useState<ErrorAnalysis | null>(null);
  const [optimizationSuggestions, setOptimizationSuggestions] = useState<OptimizationSuggestions | null>(null);
  
  const [loading, setLoading] = useState(false);

  // Fetch analytics data
  useEffect(() => {
    fetchAnalyticsData();
    
    if (autoRefresh) {
      const interval = setInterval(fetchAnalyticsData, refreshInterval * 1000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, timeRange]);

  const fetchAnalyticsData = async () => {
    setLoading(true);
    try {
      // Fetch all analytics data
      const [quality, performance, documents, embeddings, errors, suggestions] = await Promise.all([
        fetchQualityMetrics(),
        fetchPerformanceMetrics(),
        fetchDocumentInsights(),
        fetchEmbeddingAnalytics(),
        fetchErrorAnalysis(),
        fetchOptimizationSuggestions()
      ]);
      
      setQualityMetrics(quality);
      setPerformanceMetrics(performance);
      setDocumentInsights(documents);
      setEmbeddingAnalytics(embeddings);
      setErrorAnalysis(errors);
      setOptimizationSuggestions(suggestions);
    } catch (error) {
      console.error('Error fetching analytics data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchQualityMetrics = async (): Promise<QualityMetrics> => {
    // Mock data - replace with actual API call
    return {
      overallScore: 0.87,
      embeddingQuality: 0.92,
      chunkCoherence: 0.85,
      languageDetectionAccuracy: 0.96,
      duplicateDetectionRate: 0.89,
      processingAccuracy: 0.94,
      semanticSimilarity: 0.88,
      contextPreservation: 0.83
    };
  };

  const fetchPerformanceMetrics = async (): Promise<PerformanceMetrics> => {
    // Mock data - replace with actual API call
    return {
      processingSpeed: 45.2,
      memoryEfficiency: 0.78,
      cpuUtilization: 0.65,
      gpuUtilization: 0.82,
      diskIORate: 125.5,
      networkIORate: 89.3,
      throughputTrend: Array.from({ length: 24 }, (_, i) => ({
        time: `${i}:00`,
        value: Math.random() * 100 + 50
      })),
      bottlenecks: ['Memory allocation', 'Disk I/O', 'GPU memory']
    };
  };

  const fetchDocumentInsights = async (): Promise<DocumentInsights> => {
    // Mock data - replace with actual API call
    return {
      totalDocuments: 15420,
      processedDocuments: 14890,
      failedDocuments: 530,
      averageProcessingTime: 2.3,
      documentTypes: {
        'PDF': 8500,
        'DOCX': 4200,
        'TXT': 1800,
        'MD': 920
      },
      languageDistribution: {
        'Russian': 12500,
        'English': 2400,
        'Mixed': 520
      },
      sizeDistribution: {
        'Small (<1MB)': 6800,
        'Medium (1-10MB)': 7200,
        'Large (>10MB)': 1420
      },
      qualityDistribution: {
        'High (>0.8)': 11200,
        'Medium (0.6-0.8)': 3400,
        'Low (<0.6)': 820
      }
    };
  };

  const fetchEmbeddingAnalytics = async (): Promise<EmbeddingAnalytics> => {
    // Mock data - replace with actual API call
    return {
      totalEmbeddings: 245680,
      embeddingDimensions: 768,
      averageEmbeddingTime: 0.045,
      embeddingQualityScore: 0.91,
      clusterAnalysis: [
        { cluster: 1, size: 45000, quality: 0.92 },
        { cluster: 2, size: 38000, quality: 0.89 },
        { cluster: 3, size: 52000, quality: 0.94 },
        { cluster: 4, size: 31000, quality: 0.87 },
        { cluster: 5, size: 79680, quality: 0.91 }
      ],
      similarityMatrix: [], // Would contain actual similarity matrix
      outliers: [
        { id: 'doc_1234', score: 0.23, reason: 'Low semantic coherence' },
        { id: 'doc_5678', score: 0.31, reason: 'Language detection failed' },
        { id: 'doc_9012', score: 0.28, reason: 'Corrupted text extraction' }
      ]
    };
  };

  const fetchErrorAnalysis = async (): Promise<ErrorAnalysis> => {
    // Mock data - replace with actual API call
    return {
      totalErrors: 127,
      errorsByType: {
        'Processing Error': 45,
        'Memory Error': 23,
        'Format Error': 31,
        'Network Error': 12,
        'GPU Error': 16
      },
      errorsByStage: {
        'Document Loading': 34,
        'Text Extraction': 28,
        'Chunking': 19,
        'Embedding': 25,
        'Storage': 21
      },
      criticalErrors: [
        {
          id: 'err_001',
          type: 'Memory Error',
          message: 'Out of memory during batch processing',
          timestamp: '2024-01-15T14:30:00Z',
          document: 'large_document.pdf',
          stage: 'Embedding',
          severity: 'critical'
        },
        {
          id: 'err_002',
          type: 'GPU Error',
          message: 'CUDA out of memory',
          timestamp: '2024-01-15T15:45:00Z',
          stage: 'Embedding',
          severity: 'high'
        }
      ],
      errorTrends: Array.from({ length: 24 }, (_, i) => ({
        time: `${i}:00`,
        count: Math.floor(Math.random() * 10),
        type: ['Processing', 'Memory', 'Format'][Math.floor(Math.random() * 3)]
      }))
    };
  };

  const fetchOptimizationSuggestions = async (): Promise<OptimizationSuggestions> => {
    // Mock data - replace with actual API call
    return {
      performance: [
        {
          category: 'Memory Management',
          suggestion: 'Increase batch size to 64 for better GPU utilization',
          impact: 'high',
          effort: 'low',
          estimatedImprovement: '25% faster processing'
        },
        {
          category: 'Parallel Processing',
          suggestion: 'Enable multi-GPU processing for large documents',
          impact: 'high',
          effort: 'medium',
          estimatedImprovement: '40% faster embedding generation'
        }
      ],
      quality: [
        {
          category: 'Text Processing',
          suggestion: 'Implement advanced text cleaning for better chunk quality',
          impact: 'medium',
          effort: 'medium',
          estimatedImprovement: '15% better semantic coherence'
        }
      ],
      resources: [
        {
          category: 'Storage',
          suggestion: 'Use SSD storage for faster I/O operations',
          impact: 'medium',
          effort: 'high',
          estimatedImprovement: '30% faster document loading'
        }
      ]
    };
  };

  // Chart configurations
  const qualityGaugeConfig = {
    percent: qualityMetrics?.overallScore || 0,
    range: {
      color: ['#F4664A', '#FAAD14', '#30BF78'],
    },
    indicator: {
      pointer: {
        style: {
          stroke: '#D0D0D0',
        },
      },
      pin: {
        style: {
          stroke: '#D0D0D0',
        },
      },
    },
    statistic: {
      content: {
        style: {
          fontSize: '36px',
          lineHeight: '36px',
        },
      },
    },
  };

  const performanceTrendConfig = {
    data: performanceMetrics?.throughputTrend || [],
    padding: 'auto',
    xField: 'time',
    yField: 'value',
    smooth: true,
    areaStyle: {
      fill: 'l(270) 0:#ffffff 0.5:#7ec2f3 1:#1890ff',
    },
  };

  const documentTypesConfig = {
    data: documentInsights ? Object.entries(documentInsights.documentTypes).map(([type, count]) => ({
      type,
      count
    })) : [],
    angleField: 'count',
    colorField: 'type',
    radius: 0.8,
    label: {
      type: 'outer',
      content: '{name} {percentage}',
    },
    interactions: [
      {
        type: 'element-selected',
      },
      {
        type: 'element-active',
      },
    ],
  };

  const errorTrendConfig = {
    data: errorAnalysis?.errorTrends || [],
    xField: 'time',
    yField: 'count',
    seriesField: 'type',
    color: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'],
  };

  // Render optimization suggestions
  const renderOptimizationSuggestions = (suggestions: OptimizationSuggestions['performance']) => (
    <List
      dataSource={suggestions}
      renderItem={(item) => (
        <List.Item>
          <List.Item.Meta
            avatar={
              <Avatar 
                icon={<RocketOutlined />} 
                style={{ 
                  backgroundColor: item.impact === 'high' ? '#52c41a' : 
                                   item.impact === 'medium' ? '#faad14' : '#d9d9d9' 
                }}
              />
            }
            title={
              <Space>
                <span>{item.category}</span>
                <Tag color={item.impact === 'high' ? 'green' : item.impact === 'medium' ? 'orange' : 'default'}>
                  {item.impact.toUpperCase()} IMPACT
                </Tag>
                <Tag color={item.effort === 'low' ? 'green' : item.effort === 'medium' ? 'orange' : 'red'}>
                  {item.effort.toUpperCase()} EFFORT
                </Tag>
              </Space>
            }
            description={
              <div>
                <p>{item.suggestion}</p>
                <Text type="success">Expected: {item.estimatedImprovement}</Text>
              </div>
            }
          />
        </List.Item>
      )}
    />
  );

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Space>
            <RadarChartOutlined style={{ fontSize: '24px', color: '#1890ff' }} />
            <Title level={2} style={{ margin: 0 }}>RAG Analytics Dashboard</Title>
          </Space>
        </Col>
        <Col>
          <Space>
            <Switch 
              checked={autoRefresh}
              onChange={setAutoRefresh}
              checkedChildren="Auto"
              unCheckedChildren="Manual"
            />
            <Select
              value={refreshInterval}
              onChange={setRefreshInterval}
              style={{ width: 100 }}
              options={[
                { value: 10, label: '10s' },
                { value: 30, label: '30s' },
                { value: 60, label: '1m' },
                { value: 300, label: '5m' }
              ]}
            />
            <RangePicker 
              onChange={(dates) => setTimeRange(dates ? [dates[0]!.toISOString(), dates[1]!.toISOString()] : null)}
            />
            <Button 
              icon={<DownloadOutlined />}
              onClick={() => {
                // Export analytics report
              }}
            >
              Export Report
            </Button>
          </Space>
        </Col>
      </Row>

      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        {/* Overview Tab */}
        <TabPane tab={<span><DotChartOutlined />Overview</span>} key="overview">
          <Row gutter={16}>
            {/* Quality Score */}
            <Col span={8}>
              <Card title="Overall Quality Score" style={{ textAlign: 'center' }}>
                <Gauge {...qualityGaugeConfig} height={200} />
                <div style={{ marginTop: 16 }}>
                  <Row gutter={8}>
                    <Col span={12}>
                      <Statistic
                        title="Embedding Quality"
                        value={qualityMetrics?.embeddingQuality || 0}
                        precision={2}
                        valueStyle={{ fontSize: '16px' }}
                      />
                    </Col>
                    <Col span={12}>
                      <Statistic
                        title="Chunk Coherence"
                        value={qualityMetrics?.chunkCoherence || 0}
                        precision={2}
                        valueStyle={{ fontSize: '16px' }}
                      />
                    </Col>
                  </Row>
                </div>
              </Card>
            </Col>

            {/* Performance Metrics */}
            <Col span={16}>
              <Card title="Performance Trends">
                <Area {...performanceTrendConfig} height={200} />
                <Row gutter={16} style={{ marginTop: 16 }}>
                  <Col span={6}>
                    <Statistic
                      title="Processing Speed"
                      value={performanceMetrics?.processingSpeed || 0}
                      precision={1}
                      suffix="docs/min"
                      prefix={<ThunderboltOutlined />}
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="Memory Efficiency"
                      value={(performanceMetrics?.memoryEfficiency || 0) * 100}
                      precision={1}
                      suffix="%"
                      prefix={<CloudOutlined />}
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="CPU Usage"
                      value={(performanceMetrics?.cpuUtilization || 0) * 100}
                      precision={1}
                      suffix="%"
                      // ProcessorOutlined is removed, so this line is commented out
                      // prefix={<ProcessorOutlined />} 
                    />
                  </Col>
                  <Col span={6}>
                    <Statistic
                      title="GPU Usage"
                      value={(performanceMetrics?.gpuUtilization || 0) * 100}
                      precision={1}
                      suffix="%"
                      prefix={<CloudOutlined />}
                    />
                  </Col>
                </Row>
              </Card>
            </Col>
          </Row>

          {/* Document Insights */}
          <Row gutter={16} style={{ marginTop: 16 }}>
            <Col span={12}>
              <Card title="Document Distribution">
                <Pie {...documentTypesConfig} height={300} />
              </Card>
            </Col>
            <Col span={12}>
              <Card title="Processing Summary">
                <Row gutter={16}>
                  <Col span={8}>
                    <Statistic
                      title="Total Documents"
                      value={documentInsights?.totalDocuments || 0}
                      prefix={<FileTextOutlined />}
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title="Processed"
                      value={documentInsights?.processedDocuments || 0}
                      prefix={<CheckCircleOutlined />}
                      valueStyle={{ color: '#3f8600' }}
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title="Failed"
                      value={documentInsights?.failedDocuments || 0}
                      prefix={<WarningOutlined />}
                      valueStyle={{ color: '#cf1322' }}
                    />
                  </Col>
                </Row>
                
                <Divider />
                
                <div>
                  <Text strong>Processing Rate</Text>
                  <Progress 
                    percent={documentInsights ? 
                      (documentInsights.processedDocuments / documentInsights.totalDocuments) * 100 : 0
                    }
                    status="active"
                    strokeColor={{
                      '0%': '#108ee9',
                      '100%': '#87d068',
                    }}
                  />
                </div>
                
                <div style={{ marginTop: 16 }}>
                  <Text strong>Average Processing Time: </Text>
                  <Text>{documentInsights?.averageProcessingTime || 0}s per document</Text>
                </div>
              </Card>
            </Col>
          </Row>
        </TabPane>

        {/* Quality Analysis Tab */}
        <TabPane tab={<span><TrophyOutlined />Quality Analysis</span>} key="quality">
          <Row gutter={16}>
            <Col span={16}>
              <Card title="Quality Metrics Breakdown">
                <Row gutter={16}>
                  {qualityMetrics && Object.entries(qualityMetrics).map(([key, value]) => (
                    <Col span={6} key={key}>
                      <Card size="small">
                        <Statistic
                          title={key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                          value={value}
                          precision={2}
                          valueStyle={{ 
                            color: value > 0.8 ? '#3f8600' : value > 0.6 ? '#faad14' : '#cf1322',
                            fontSize: '20px'
                          }}
                        />
                        <Progress 
                          percent={value * 100} 
                          size="small" 
                          showInfo={false}
                          strokeColor={value > 0.8 ? '#52c41a' : value > 0.6 ? '#faad14' : '#ff4d4f'}
                        />
                      </Card>
                    </Col>
                  ))}
                </Row>
              </Card>
            </Col>
            
            <Col span={8}>
              <Card title="Quality Issues">
                {embeddingAnalytics?.outliers && (
                  <List
                    size="small"
                    dataSource={embeddingAnalytics.outliers}
                    renderItem={(item) => (
                      <List.Item>
                        <List.Item.Meta
                          avatar={<Avatar icon={<BugOutlined />} style={{ backgroundColor: '#ff4d4f' }} />}
                          title={item.id}
                          description={
                            <div>
                              <Text type="danger">Score: {item.score}</Text>
                              <br />
                              <Text type="secondary">{item.reason}</Text>
                            </div>
                          }
                        />
                      </List.Item>
                    )}
                  />
                )}
              </Card>
            </Col>
          </Row>
        </TabPane>

        {/* Performance Analysis Tab */}
        <TabPane tab={<span><RocketOutlined />Performance</span>} key="performance">
          <Row gutter={16}>
            <Col span={18}>
              <Card title="Resource Utilization Over Time">
                <Line 
                  data={performanceMetrics?.throughputTrend || []}
                  xField="time"
                  yField="value"
                  height={300}
                />
              </Card>
            </Col>
            
            <Col span={6}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Card title="Bottlenecks" size="small">
                  {performanceMetrics?.bottlenecks.map((bottleneck, index) => (
                    <Tag key={index} color="red" style={{ marginBottom: 8 }}>
                      {bottleneck}
                    </Tag>
                  ))}
                </Card>
                
                <Card title="I/O Rates" size="small">
                  <Statistic
                    title="Disk I/O"
                    value={performanceMetrics?.diskIORate || 0}
                    precision={1}
                    suffix="MB/s"
                  />
                  <Statistic
                    title="Network I/O"
                    value={performanceMetrics?.networkIORate || 0}
                    precision={1}
                    suffix="MB/s"
                  />
                </Card>
              </Space>
            </Col>
          </Row>
        </TabPane>

        {/* Error Analysis Tab */}
        <TabPane tab={<span><BugOutlined />Error Analysis</span>} key="errors">
          <Row gutter={16}>
            <Col span={12}>
              <Card title="Error Trends">
                <Line {...errorTrendConfig} height={300} />
              </Card>
            </Col>
            
            <Col span={12}>
              <Card title="Error Distribution">
                <Row gutter={16}>
                  <Col span={12}>
                    <Title level={5}>By Type</Title>
                    {errorAnalysis?.errorsByType && Object.entries(errorAnalysis.errorsByType).map(([type, count]) => (
                      <div key={type} style={{ marginBottom: 8 }}>
                        <Text>{type}: {count}</Text>
                        <Progress 
                          percent={(count / errorAnalysis.totalErrors) * 100} 
                          size="small" 
                          showInfo={false}
                        />
                      </div>
                    ))}
                  </Col>
                  
                  <Col span={12}>
                    <Title level={5}>By Stage</Title>
                    {errorAnalysis?.errorsByStage && Object.entries(errorAnalysis.errorsByStage).map(([stage, count]) => (
                      <div key={stage} style={{ marginBottom: 8 }}>
                        <Text>{stage}: {count}</Text>
                        <Progress 
                          percent={(count / errorAnalysis.totalErrors) * 100} 
                          size="small" 
                          showInfo={false}
                        />
                      </div>
                    ))}
                  </Col>
                </Row>
              </Card>
            </Col>
          </Row>
          
          <Row gutter={16} style={{ marginTop: 16 }}>
            <Col span={24}>
              <Card title="Critical Errors">
                <List
                  dataSource={errorAnalysis?.criticalErrors || []}
                  renderItem={(error) => (
                    <List.Item>
                      <List.Item.Meta
                        avatar={
                          <Avatar 
                            icon={<BugOutlined />} 
                            style={{ 
                              backgroundColor: error.severity === 'critical' ? '#ff4d4f' : 
                                               error.severity === 'high' ? '#fa8c16' : '#faad14'
                            }}
                          />
                        }
                        title={
                          <Space>
                            <Text strong>{error.type}</Text>
                            <Tag color={error.severity === 'critical' ? 'red' : 
                                       error.severity === 'high' ? 'orange' : 'yellow'}>
                              {error.severity.toUpperCase()}
                            </Tag>
                            <Text type="secondary">{error.stage}</Text>
                          </Space>
                        }
                        description={
                          <div>
                            <Text>{error.message}</Text>
                            <br />
                            <Text type="secondary">
                              {error.document && `Document: ${error.document} | `}
                              Time: {new Date(error.timestamp).toLocaleString()}
                            </Text>
                          </div>
                        }
                      />
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
          </Row>
        </TabPane>

        {/* Optimization Tab */}
        <TabPane tab={<span><RocketOutlined />Optimization</span>} key="optimization">
          <Row gutter={16}>
            <Col span={8}>
              <Card title="Performance Optimizations">
                {optimizationSuggestions?.performance && 
                  renderOptimizationSuggestions(optimizationSuggestions.performance)}
              </Card>
            </Col>
            
            <Col span={8}>
              <Card title="Quality Improvements">
                {optimizationSuggestions?.quality && 
                  renderOptimizationSuggestions(optimizationSuggestions.quality)}
              </Card>
            </Col>
            
            <Col span={8}>
              <Card title="Resource Optimizations">
                {optimizationSuggestions?.resources && 
                  renderOptimizationSuggestions(optimizationSuggestions.resources)}
              </Card>
            </Col>
          </Row>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default RAGAnalyticsDashboard;