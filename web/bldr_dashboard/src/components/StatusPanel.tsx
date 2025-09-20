import React, { useEffect, useState } from 'react';
import { Card, Row, Col, Badge, Statistic, Space, Tag, Tooltip } from 'antd';
import { apiService } from '../services/api';
import { useSocket } from '../hooks/useSocket';

interface StatusData {
  status?: string;
  timestamp?: string;
  version?: string;
  components?: Record<string, any>;
}

const miniSparkline = (values: number[] = [], width = 120, height = 28, color = '#1890ff') => {
  if (!values.length) return null as any;
  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const range = Math.max(max - min, 1);
  const step = width / Math.max(values.length - 1, 1);
  const pts = values.map((v, i) => {
    const x = i * step;
    const y = height - ((v - min) / range) * height;
    return `${x},${y}`;
  }).join(' ');
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      <polyline points={pts} fill="none" stroke={color} strokeWidth="2" />
    </svg>
  );
};

const StatusPanel: React.FC = () => {
  const [status, setStatus] = useState<StatusData>({});
  const [activeJobs, setActiveJobs] = useState<number>(0);
  const [activeTrend, setActiveTrend] = useState<number[]>([]);
  const { connected } = useSocket();

  const load = async () => {
    try {
      const s = await apiService.getStatus();
      setStatus(s || {});
    } catch {
      setStatus({});
    }
    try {
      const byTool = await apiService.getActiveJobs();
      const total = Object.values(byTool || {}).reduce((sum: number, arr: any) => sum + (Array.isArray(arr) ? arr.length : 0), 0);
      setActiveJobs(total);
      setActiveTrend(prev => {
        const next = [...prev.slice(-19), total];
        return next;
      });
    } catch {
      setActiveJobs(0);
    }
  };

  useEffect(() => {
    load();
    const t = setInterval(load, 15000);
    return () => clearInterval(t);
  }, []);

  const components = status?.components || {};
  const db = components.db || 'unknown';
  const celery = components.celery || 'unknown';
  const endpoints = components.endpoints ?? components.api_endpoints ?? null;
  const version = status.version || components.version || '-';

  const pill = (label: string, state: string) => (
    <Badge
      status={
        state === 'connected' || state === 'running' || state === 'ok' || state === 'skipped'
          ? 'success'
          : state === 'disconnected' || state === 'stopped' || state === 'error'
          ? 'error'
          : 'default'
      }
      text={`${label}: ${state}`}
    />
  );

  return (
    <Card style={{ marginBottom: 24 }} title="Состояние системы">
      <Row gutter={[16, 16]}>
        <Col xs={24} md={12} lg={8}>
          <Card size="small">
            <Space direction="vertical">
              {pill('DB', String(db))}
              {pill('Celery', String(celery))}
              {pill('WS', connected ? 'connected' : 'disconnected')}
            </Space>
          </Card>
        </Col>
        <Col xs={12} md={6} lg={4}>
          <Card size="small">
            <Statistic title="Активных задач" value={activeJobs} />
            <div style={{ marginTop: 8 }}>{miniSparkline(activeTrend)}</div>
          </Card>
        </Col>
        <Col xs={12} md={6} lg={4}>
          <Card size="small">
            <Statistic title="Endpoints" value={endpoints ?? '-'} />
          </Card>
        </Col>
        <Col xs={24} md={12} lg={8}>
          <Card size="small">
            <Space>
              <Tag color="blue">Version</Tag>
              <span style={{ fontWeight: 500 }}>{String(version)}</span>
              {status.timestamp && (
                <Tooltip title={`Last updated: ${new Date(status.timestamp).toLocaleString()}`}>
                  <Tag>{new Date(status.timestamp).toLocaleTimeString()}</Tag>
                </Tooltip>
              )}
            </Space>
          </Card>
        </Col>
      </Row>
    </Card>
  );
};

export default StatusPanel;
