import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Button, Input, Tabs, Progress, Spin } from 'antd';
import { 
  FileTextOutlined, 
  DatabaseOutlined, 
  BarChartOutlined, 
  PlayCircleOutlined,
  SearchOutlined,
  DownloadOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { apiService } from '../services/api';

const { TabPane } = Tabs;
const { Search } = Input;

// Types for our data
interface QueryResult {
  chunk: string;
  meta: {
    conf: number;
    entities: Record<string, string[]>;
    category?: string;
    [key: string]: any;
  };
  score: number;
  tezis: string;
  viol: number;
}

interface MetricsData {
  total_chunks: number;
  avg_ndcg: number;
  coverage: number;
  conf: number;
  viol: number;
  entities?: Record<string, number>;
}

interface NormDoc {
  id: string;
  name: string;
  category: string;
  type: string;
  status: string;
  issue_date: string;
  check_date: string;
  source: string;
  link: string;
  description: string;
  violations_count: number;
}

interface NormsSummary {
  total: number;
  actual: number;
  outdated: number;
  pending: number;
}

interface TrainingProgress {
  stage: string;
  log: string;
  progress: number;
}

const RAGModule: React.FC = () => {
  // State for different sections
  const [activeTab, setActiveTab] = useState('dashboard');
  const [messages, setMessages] = useState<Array<{type: string, content: string}>>([]);
  const [input, setInput] = useState('');
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [status, setStatus] = useState('Disconnected');
  
  // State for dashboard data
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [normsSummary, setNormsSummary] = useState<NormsSummary | null>(null);
  const [loadingMetrics, setLoadingMetrics] = useState(false);
  const [loadingSummary, setLoadingSummary] = useState(false);
  
  // State for trained documents
  const [trainedDocs, setTrainedDocs] = useState<NormDoc[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [docsPagination, setDocsPagination] = useState({
    page: 1,
    limit: 10,
    total: 0
  });
  
  // State for training
  const [trainingProgress, setTrainingProgress] = useState<TrainingProgress | null>(null);
  const [isTraining, setIsTraining] = useState(false);
  
  // State for query
  const [queryResults, setQueryResults] = useState<QueryResult[]>([]);
  const [queryLoading, setQueryLoading] = useState(false);

  // WebSocket connection
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      const websocket = new WebSocket(`ws://localhost:8000/ws?token=${token}`);

      websocket.onopen = () => {
        setStatus('Connected');
        console.log('WebSocket connected');
      };

      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.stage && data.log) {
            // This is a training progress update
            setTrainingProgress({
              stage: data.stage,
              log: data.log,
              progress: data.progress || 0
            });
            // If training is complete, reset the training state
            if (data.stage === 'complete') {
              setIsTraining(false);
            }
          } else {
            // This is a chat message
            setMessages(prev => [...prev, { type: 'bot', content: data.message || data }]);
          }
        } catch (e) {
          console.error('Error parsing WebSocket message:', e);
        }
      };

      websocket.onclose = () => {
        setStatus('Disconnected');
        console.log('WebSocket disconnected');
      };

      websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        setStatus('Error');
      };

      setWs(websocket);
    }

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, []);

  // Fetch initial data
  useEffect(() => {
    fetchMetrics();
    fetchNormsSummary();
    fetchTrainedDocuments();
  }, []);

  // Fetch metrics data
  const fetchMetrics = async () => {
    setLoadingMetrics(true);
    try {
      const data = await apiService.getMetrics();
      setMetrics(data);
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
    } finally {
      setLoadingMetrics(false);
    }
  };

  // Fetch norms summary
  const fetchNormsSummary = async () => {
    setLoadingSummary(true);
    try {
      const data = await apiService.getNormsSummary();
      setNormsSummary(data);
    } catch (error) {
      console.error('Failed to fetch norms summary:', error);
    } finally {
      setLoadingSummary(false);
    }
  };

  // Fetch trained documents
  const fetchTrainedDocuments = async (page = 1, limit = 10) => {
    setLoadingDocs(true);
    try {
      const response = await apiService.getNormsList({
        page,
        limit
      });
      setTrainedDocs(response.data);
      setDocsPagination({
        page: response.pagination.page,
        limit: response.pagination.limit,
        total: response.pagination.total
      });
    } catch (error) {
      console.error('Failed to fetch trained documents:', error);
    } finally {
      setLoadingDocs(false);
    }
  };

  // Handle pagination for trained documents
  const handleDocsPagination = (page: number, limit: number) => {
    fetchTrainedDocuments(page, limit);
  };

  // Send message/query
  const sendMessage = () => {
    if (input.trim() && ws) {
      ws.send(JSON.stringify({ message: input }));
      setMessages(prev => [...prev, { type: 'user', content: input }]);
      setInput('');
    }
  };

  // Start training
  const startTraining = async () => {
    try {
      setIsTraining(true);
      setTrainingProgress(null);
      await apiService.train();
    } catch (error) {
      console.error('Failed to start training:', error);
      setIsTraining(false);
    }
  };

  // Handle query submission
  const handleQuery = async (value: string) => {
    if (!value.trim()) return;
    
    setQueryLoading(true);
    try {
      const response = await apiService.query({ query: value });
      setQueryResults(response.results);
    } catch (error) {
      console.error('Failed to execute query:', error);
    } finally {
      setQueryLoading(false);
    }
  };

  // Columns for trained documents table
  const docColumns: ColumnsType<NormDoc> = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => <strong>{text}</strong>
    },
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
      render: (category: string) => (
        <Tag color={
          category === 'construction' ? 'blue' :
          category === 'finance' ? 'green' :
          category === 'safety' ? 'red' :
          'default'
        }>
          {category}
        </Tag>
      )
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type'
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={
          status === 'actual' ? 'green' :
          status === 'outdated' ? 'orange' :
          status === 'pending' ? 'blue' :
          'default'
        }>
          {status}
        </Tag>
      )
    },
    {
      title: 'Issue Date',
      dataIndex: 'issue_date',
      key: 'issue_date'
    },
    {
      title: 'Source',
      dataIndex: 'source',
      key: 'source'
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Button 
          type="link" 
          icon={<DownloadOutlined />}
          onClick={() => window.open(record.link, '_blank')}
        >
          View
        </Button>
      )
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      <h2>RAG Module</h2>
      
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        {/* Dashboard Tab */}
        <TabPane tab={<span><BarChartOutlined />Dashboard</span>} key="dashboard">
          <Row gutter={16} style={{ marginBottom: '24px' }}>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Total Chunks"
                  value={metrics?.total_chunks || 0}
                  precision={0}
                  valueStyle={{ color: '#3f8600' }}
                  prefix={<DatabaseOutlined />}
                  loading={loadingMetrics}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Avg NDCG"
                  value={metrics?.avg_ndcg || 0}
                  precision={2}
                  valueStyle={{ color: '#cf1322' }}
                  loading={loadingMetrics}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Coverage"
                  value={metrics ? (metrics.coverage * 100) : 0}
                  precision={1}
                  suffix="%"
                  loading={loadingMetrics}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Violations"
                  value={metrics?.viol || 0}
                  precision={0}
                  valueStyle={{ color: '#fa8c16' }}
                  loading={loadingMetrics}
                />
              </Card>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={12}>
              <Card title="NTD Database Summary" extra={<Button onClick={fetchNormsSummary}>Refresh</Button>}>
                {loadingSummary ? (
                  <Spin />
                ) : normsSummary ? (
                  <div>
                    <p>Total Documents: <strong>{normsSummary.total}</strong></p>
                    <p>Actual: <Tag color="green">{normsSummary.actual}</Tag></p>
                    <p>Outdated: <Tag color="orange">{normsSummary.outdated}</Tag></p>
                    <p>Pending: <Tag color="blue">{normsSummary.pending}</Tag></p>
                  </div>
                ) : (
                  <p>No data available</p>
                )}
              </Card>
            </Col>
            
            <Col span={12}>
              <Card title="Training Status">
                {trainingProgress ? (
                  <div>
                    <p><strong>Stage:</strong> {trainingProgress.stage}</p>
                    <p><strong>Log:</strong> {trainingProgress.log}</p>
                    <Progress percent={trainingProgress.progress} />
                  </div>
                ) : isTraining ? (
                  <div>
                    <Spin tip="Training in progress..." />
                  </div>
                ) : (
                  <div>
                    <p>No training in progress</p>
                    <Button 
                      type="primary" 
                      icon={<PlayCircleOutlined />}
                      onClick={startTraining}
                    >
                      Start Training
                    </Button>
                  </div>
                )}
              </Card>
            </Col>
          </Row>
        </TabPane>
        
        {/* Trained Documents Tab */}
        <TabPane tab={<span><FileTextOutlined />Trained Documents</span>} key="documents">
          <Card 
            title="Trained NTD Documents" 
            extra={
              <Button onClick={() => fetchTrainedDocuments()}>
                Refresh
              </Button>
            }
          >
            <Table
              columns={docColumns}
              dataSource={trainedDocs}
              loading={loadingDocs}
              pagination={{
                current: docsPagination.page,
                pageSize: docsPagination.limit,
                total: docsPagination.total,
                onChange: (page, pageSize) => handleDocsPagination(page, pageSize || 10)
              }}
              rowKey="id"
            />
          </Card>
        </TabPane>
        
        {/* Query Interface Tab */}
        <TabPane tab={<span><SearchOutlined />Query</span>} key="query">
          <Card title="RAG Query Interface">
            <Search
              placeholder="Enter your query..."
              enterButton="Search"
              size="large"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onSearch={handleQuery}
              loading={queryLoading}
              style={{ marginBottom: '24px' }}
            />
            
            {queryResults.length > 0 && (
              <div>
                <h3>Results:</h3>
                {queryResults.map((result, index) => (
                  <Card 
                    key={index} 
                    size="small" 
                    style={{ marginBottom: '12px' }}
                    title={`Score: ${(result.score * 100).toFixed(1)}%`}
                  >
                    <p>{result.chunk}</p>
                    <p><strong>Tezis:</strong> {result.tezis}</p>
                    <p><strong>Violations:</strong> {result.viol}%</p>
                  </Card>
                ))}
              </div>
            )}
            
            {queryLoading && <Spin tip="Searching..." />}
          </Card>
        </TabPane>
        
        {/* Chat Interface Tab */}
        <TabPane tab="Chat" key="chat">
          <Card title="RAG Chat Interface">
            <p>WebSocket Status: <span style={{ color: status === 'Connected' ? 'green' : 'red' }}>{status}</span></p>
            <div style={{ height: '300px', overflowY: 'scroll', border: '1px solid #ccc', padding: '10px', marginBottom: '12px' }}>
              {messages.map((msg, idx) => (
                <div key={idx} style={{ marginBottom: '5px' }}>
                  <strong>{msg.type}:</strong> {msg.content}
                </div>
              ))}
            </div>
            <Input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Enter your message..."
              onPressEnter={sendMessage}
              style={{ width: '70%', marginRight: '10px' }}
            />
            <Button onClick={sendMessage}>Send</Button>
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default RAGModule;