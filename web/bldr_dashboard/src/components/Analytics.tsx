import React, { useState, useEffect, useRef } from 'react';
import { Card, Row, Col, Statistic, message } from 'antd';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';
import io from 'socket.io-client';
import { apiService, type MetricsData } from '../services/api';

// Цвета для диаграммы сущностей
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

// Цвета для этапов пайплайна
const stageColors: Record<string, string> = {
  '7': '#ff6b6b',
  '4': '#4ecdc4',
  '5': '#45b7d1',
  '6': '#96ceb4',
  '8': '#feca57',
  '9': '#ff9ff3',
  '10': '#54a0ff',
  '11': '#5f27cd',
  '12': '#00d2d3',
  '13': '#ff9f43',
  '14': '#10ac84',
};

const Analytics: React.FC = () => {
  const [metricsData, setMetricsData] = useState<MetricsData | null>(null);
  const [stageLogs, setStageLogs] = useState<Array<{stage: string, log: string, progress: number}>>([]);
  const [isClient, setIsClient] = useState(false);
  const socketRef = useRef<any>(null);

  // Загрузка метрик
  const fetchMetrics = async () => {
    try {
      const data = await apiService.getMetrics();
      setMetricsData(data);
    } catch (error) {
      console.error('Ошибка загрузки метрик:', error);
      message.error('Не удалось загрузить метрики');
    }
  };

  // Подключение к WebSocket для получения логов этапов
  useEffect(() => {
    // Set client-side flag
    setIsClient(true);
    
    // Загружаем начальные метрики
    fetchMetrics();
    
    // Подключаемся к WebSocket
    if (!socketRef.current) {
      // Use correct URL for WebSocket connection
      const wsUrl = `http://localhost:8001`;
      socketRef.current = io(wsUrl, {
        transports: ['websocket'],
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
        path: '/ws/'
      });
      
      socketRef.current.on('connect', () => {
        console.log('WebSocket connected');
      });
      
      socketRef.current.on('disconnect', () => {
        console.log('WebSocket disconnected');
      });
      
      socketRef.current.on('stage_update', (data: any) => {
        setStageLogs(prev => [...prev, data]);
        
        // Если это завершение обучения, обновляем метрики
        if (data.stage === 'complete') {
          setTimeout(fetchMetrics, 2000);
        }
      });
      
      socketRef.current.on('connect_error', (error: any) => {
        console.error('WebSocket connection error:', error);
        message.error('Ошибка подключения к серверу WebSocket');
      });
    }
    
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, []);

  // Подготовка данных для диаграмм
  const getEntityData = () => {
    if (!metricsData?.entities) return [];
    return Object.entries(metricsData.entities).map(([name, value]) => ({
      name,
      value,
    }));
  };

  const getMetricsChartData = () => {
    if (!metricsData) return [];
    return [
      { name: 'NDCG', value: metricsData.avg_ndcg },
      { name: 'Coverage', value: metricsData.coverage },
      { name: 'Confidence', value: metricsData.conf },
      { name: 'Violations', value: metricsData.viol / 100 },
    ];
  };

  const getStagesProgressData = () => {
    // Используем реальные данные из логов этапов, если есть
    if (stageLogs.length > 0) {
      return stageLogs
        .filter(log => log.progress > 0)
        .map(log => ({
          stage: `Этап ${log.stage}`,
          progress: log.progress
        }));
    }
    
    // В противном случае используем симуляцию
    return [
      { stage: 'Этап 4', progress: 95 },
      { stage: 'Этап 5', progress: 85 },
      { stage: 'Этап 6', progress: 90 },
      { stage: 'Этап 7', progress: 99 },
      { stage: 'Этап 8', progress: 80 },
      { stage: 'Этап 9', progress: 75 },
      { stage: 'Этап 10', progress: 88 },
    ];
  };

  // Render nothing on server-side
  if (!isClient) {
    return null;
  }

  return (
    <div style={{ padding: '24px' }}>
      <Row gutter={16}>
        <Col span={24}>
          <Card title="Основные метрики" bordered={false}>
            <Row gutter={16}>
              <Col span={6}>
                <Statistic title="Всего чанков" value={metricsData?.total_chunks || 0} />
              </Col>
              <Col span={6}>
                <Statistic title="NDCG" value={metricsData?.avg_ndcg.toFixed(2) || '0.00'} />
              </Col>
              <Col span={6}>
                <Statistic title="Coverage" value={metricsData?.coverage.toFixed(2) || '0.00'} />
              </Col>
              <Col span={6}>
                <Statistic title="Violations %" value={metricsData?.viol || 0} />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
      
      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={8}>
          <Card title="Сущности" size="small">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={getEntityData()}
                  cx="50%"
                  cy="50%"
                  labelLine={true}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {getEntityData().map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        
        <Col span={8}>
          <Card title="Метрики" size="small">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={getMetricsChartData()}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="value" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        
        <Col span={8}>
          <Card title="Прогресс этапов" size="small">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={getStagesProgressData()}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="stage" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="progress" 
                  stroke="#82ca9d" 
                  activeDot={{ r: 8 }} 
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>
      
      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title="Логи этапов" size="small">
            <div style={{ maxHeight: 300, overflow: 'auto' }}>
              {stageLogs.length > 0 ? (
                stageLogs.map((log, index) => (
                  <div 
                    key={index} 
                    style={{ 
                      color: stageColors[log.stage.split('/')[0] || ''] || '#000',
                      marginBottom: '8px',
                      padding: '4px',
                      borderBottom: '1px solid #eee'
                    }}
                  >
                    [{log.stage}] {log.log} ({log.progress}%)
                  </div>
                ))
              ) : (
                <p>Логи этапов будут отображаться здесь в реальном времени</p>
              )}
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Analytics;