/**
 * ToolsInterface - главный интерфейс для работы с инструментами анализа файлов
 * Интегрирован с существующей архитектурой Bldr Dashboard
 */

import React, { useState, useEffect } from 'react';
import { Tabs, Badge, Card, Alert, Button, Row, Col } from 'antd';
import { 
  FileTextOutlined, 
  PictureOutlined, 
  FolderOutlined, 
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined 
} from '@ant-design/icons';
import EstimateAnalyzer from './EstimateAnalyzer';
import ImageAnalyzer from './ImageAnalyzer';
import DocumentAnalyzer from './DocumentAnalyzer';
import TenderAnalyzer from './TenderAnalyzer';
import { useSocket } from '../hooks/useSocket';
import { apiService } from '../services/api';

const { TabPane } = Tabs;

interface ActiveJob {
  job_id: string;
  tool_type: string;
  status: string;
  progress: number;
  message: string;
  created_at: string;
}

const ToolsInterface: React.FC = () => {
  const [activeTab, setActiveTab] = useState('estimate');
  const [activeJobs, setActiveJobs] = useState<ActiveJob[]>([]);
  const [notifications, setNotifications] = useState<any[]>([]);
  const [wsConnected, setWsConnected] = useState(false);
  const { socket, connected } = useSocket();

  // Subscribe to normalized task_update events
  useEffect(() => {
    setWsConnected(connected);
    if (!socket) return;
    const handle = (data: any) => {
      setActiveJobs(prev => {
        const updated = prev.map(job => job.job_id === (data.id || data.job_id) ? { ...job, status: data.status, progress: data.progress, message: data.message } : job);
        if (!updated.find(job => job.job_id === (data.id || data.job_id))) {
          updated.push({
            job_id: data.id || data.job_id,
            tool_type: data.type || 'unknown',
            status: data.status || 'running',
            progress: data.progress ?? 0,
            message: data.message || 'Обновление задачи',
            created_at: new Date().toISOString()
          });
        }
        return updated;
      });
    };
    socket.on('task_update', handle);
    return () => socket.off('task_update', handle);
  }, [socket, connected]);

  // Загружаем активные задачи при монтировании (через apiService)
  useEffect(() => {
    const fetchActiveJobs = async () => {
      try {
        const byTool = await apiService.getActiveJobs();
        const jobs: ActiveJob[] = [];
        Object.entries(byTool).forEach(([toolType, toolJobs]: [string, any]) => {
          (toolJobs as any[]).forEach((job: any) => {
            jobs.push({
              job_id: job.job_id,
              tool_type: toolType,
              status: job.status,
              progress: job.progress,
              message: job.message,
              created_at: job.created_at
            });
          });
        });
        setActiveJobs(jobs);
      } catch (error) {
        console.error('Ошибка загрузки активных задач:', error);
      }
    };

    fetchActiveJobs();
    const interval = setInterval(fetchActiveJobs, 10000);
    return () => clearInterval(interval);
  }, []);

  // Очищаем старые уведомления
  useEffect(() => {
    const timer = setInterval(() => {
      setNotifications(prev => 
        prev.filter(notif => 
          Date.now() - new Date(notif.timestamp).getTime() < 30000 // Убираем через 30 сек
        )
      );
    }, 5000);

    return () => clearInterval(timer);
  }, []);

  const getTabBadgeCount = (toolType: string) => {
    return activeJobs.filter(job => 
      job.tool_type === toolType && job.status === 'running'
    ).length;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'processing';
      case 'completed': return 'success';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* Заголовок с статусом подключения */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col span={18}>
          <h2 style={{ margin: 0, color: '#1f2937' }}>
            🔧 Инструменты анализа файлов
          </h2>
          <p style={{ color: '#6b7280', margin: 0 }}>
            Загружайте и анализируйте сметы, изображения и документы
          </p>
        </Col>
        <Col span={6} style={{ textAlign: 'right' }}>
          <Badge 
            status={wsConnected ? 'processing' : 'error'} 
            text={wsConnected ? 'Подключено' : 'Отключено'} 
          />
        </Col>
      </Row>

      {/* Уведомления */}
      {notifications.length > 0 && (
        <div style={{ marginBottom: '16px' }}>
          {notifications.slice(-3).map(notif => (
            <Alert
              key={notif.id}
              type={notif.type}
              message={notif.message}
              style={{ marginBottom: '8px' }}
              closable
              onClose={() => setNotifications(prev => 
                prev.filter(n => n.id !== notif.id)
              )}
            />
          ))}
        </div>
      )}

      {/* Активные задачи */}
      {activeJobs.length > 0 && (
        <Card 
          title={
            <span>
              <ClockCircleOutlined style={{ marginRight: '8px' }} />
              Активные задачи ({activeJobs.length})
            </span>
          }
          style={{ marginBottom: '24px' }}
        >
          <Row gutter={[16, 8]}>
            {activeJobs.map(job => (
              <Col key={job.job_id} span={24}>
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  padding: '8px', 
                  backgroundColor: '#f9fafb',
                  borderRadius: '6px',
                  marginBottom: '8px'
                }}>
                  <div style={{ marginRight: '12px' }}>
                    {job.status === 'running' && <ClockCircleOutlined style={{ color: '#1890ff' }} />}
                    {job.status === 'completed' && <CheckCircleOutlined style={{ color: '#52c41a' }} />}
                    {job.status === 'failed' && <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 'bold' }}>{job.tool_type}</div>
                    <div style={{ fontSize: '12px', color: '#666' }}>{job.message}</div>
                  </div>
                  <div style={{ minWidth: '80px', textAlign: 'right' }}>
                    <Badge 
                      status={getStatusColor(job.status)} 
                      text={`${job.progress}%`} 
                    />
                  </div>
                </div>
              </Col>
            ))}
          </Row>
        </Card>
      )}

      {/* Табы с инструментами */}
      <Card>
        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab}
          type="card"
          size="large"
        >
          <TabPane 
            tab={
              <span>
                <FileTextOutlined />
                Анализ смет
                {getTabBadgeCount('estimate_analyzer') > 0 && (
                  <Badge 
                    count={getTabBadgeCount('estimate_analyzer')} 
                    style={{ marginLeft: '8px' }} 
                  />
                )}
              </span>
            } 
            key="estimate"
          >
            <EstimateAnalyzer />
          </TabPane>
          
          <TabPane 
            tab={
              <span>
                <PictureOutlined />
                Анализ изображений
                {getTabBadgeCount('image_analyzer') > 0 && (
                  <Badge 
                    count={getTabBadgeCount('image_analyzer')} 
                    style={{ marginLeft: '8px' }} 
                  />
                )}
              </span>
            } 
            key="images"
          >
            <ImageAnalyzer />
          </TabPane>
          
          <TabPane 
            tab={
              <span>
                <FolderOutlined />
                Анализ документов
                {getTabBadgeCount('document_analyzer') > 0 && (
                  <Badge 
                    count={getTabBadgeCount('document_analyzer')} 
                    style={{ marginLeft: '8px' }} 
                  />
                )}
              </span>
            } 
            key="documents"
          >
            <DocumentAnalyzer />
          </TabPane>
          
          <TabPane 
            tab={
              <span>
                🏆
                Комплексный анализ тендера
                {getTabBadgeCount('tender_analyzer') > 0 && (
                  <Badge 
                    count={getTabBadgeCount('tender_analyzer')} 
                    style={{ marginLeft: '8px' }} 
                  />
                )}
              </span>
            } 
            key="tender"
          >
            <TenderAnalyzer />
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default ToolsInterface;