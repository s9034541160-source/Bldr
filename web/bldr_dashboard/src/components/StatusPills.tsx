import React, { useEffect, useState } from 'react';
import { Badge, Space, Tooltip } from 'antd';
import { apiService } from '../services/api';
import { useSocket } from '../hooks/useSocket';

interface StatusData {
  status?: string;
  timestamp?: string;
  components?: {
    db?: string;
    celery?: string;
    websocket_connections?: number;
    endpoints?: number;
    [key: string]: any;
  };
}

const StatusPills: React.FC = () => {
  const [data, setData] = useState<StatusData>({});
  const { connected } = useSocket();

  const load = async () => {
    try {
      const res = await apiService.getStatus();
      setData(res);
    } catch {
      setData({});
    }
  };

  useEffect(() => {
    load();
    const t = setInterval(load, 15000);
    return () => clearInterval(t);
  }, []);

  const db = data?.components?.db || 'unknown';
  const celery = data?.components?.celery || 'unknown';
  const ws = connected ? 'connected' : 'disconnected';

  const pill = (label: string, state: string) => (
    <Tooltip title={`${label}: ${state}`}>
      <Badge
        status={
          state === 'connected' || state === 'running' || state === 'skipped'
            ? 'success'
            : state === 'disconnected' || state === 'stopped'
            ? 'error'
            : 'default'
        }
        text={label}
      />
    </Tooltip>
  );

  return (
    <Space size={12} style={{ marginLeft: 16 }}>
      {pill('DB', db)}
      {pill('Celery', celery)}
      {pill('WS', ws)}
    </Space>
  );
};

export default StatusPills;
