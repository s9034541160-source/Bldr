/**
 * Diagnostic Panel
 * Диагностическая панель для отладки проблем фронтенда
 */

import React, { useState, useEffect } from 'react';
import { Card, Alert, Button, Space, Descriptions, Tag } from 'antd';
import { apiService } from '../services/api';

const DiagnosticPanel: React.FC = () => {
  const [apiStatus, setApiStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [apiError, setApiError] = useState<string>('');
  const [systemInfo, setSystemInfo] = useState<any>(null);

  useEffect(() => {
    checkAPI();
  }, []);

  const checkAPI = async () => {
    try {
      setApiStatus('loading');
      const health = await apiService.getHealth();
      setSystemInfo(health);
      setApiStatus('success');
    } catch (error: any) {
      setApiError(error.message || 'Unknown error');
      setApiStatus('error');
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card title="🔧 Frontend Diagnostic Panel" style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Alert
            message="Frontend Status"
            description="Frontend is loading and rendering correctly"
            type="success"
            showIcon
          />
          
          <Descriptions title="System Information" bordered>
            <Descriptions.Item label="React Version">
              {React.version}
            </Descriptions.Item>
            <Descriptions.Item label="Environment">
              {process.env.NODE_ENV || 'development'}
            </Descriptions.Item>
            <Descriptions.Item label="API Base URL">
              {import.meta.env.VITE_API_URL || 'http://localhost:8000'}
            </Descriptions.Item>
            <Descriptions.Item label="Current Time">
              {new Date().toLocaleString()}
            </Descriptions.Item>
          </Descriptions>

          <Card title="API Connection Status" size="small">
            {apiStatus === 'loading' && (
              <Alert message="Checking API connection..." type="info" />
            )}
            
            {apiStatus === 'success' && (
              <div>
                <Alert message="API connection successful" type="success" showIcon />
                {systemInfo && (
                  <Descriptions size="small" style={{ marginTop: 16 }}>
                    <Descriptions.Item label="Status">
                      <Tag color="green">{systemInfo.status}</Tag>
                    </Descriptions.Item>
                    <Descriptions.Item label="Database">
                      <Tag color={systemInfo.components?.db ? 'green' : 'red'}>
                        {systemInfo.components?.db ? 'Connected' : 'Disconnected'}
                      </Tag>
                    </Descriptions.Item>
                    <Descriptions.Item label="Celery">
                      <Tag color={systemInfo.components?.celery ? 'green' : 'red'}>
                        {systemInfo.components?.celery ? 'Running' : 'Stopped'}
                      </Tag>
                    </Descriptions.Item>
                  </Descriptions>
                )}
              </div>
            )}
            
            {apiStatus === 'error' && (
              <div>
                <Alert 
                  message="API connection failed" 
                  description={apiError}
                  type="error" 
                  showIcon 
                />
                <div style={{ marginTop: 16 }}>
                  <Alert
                    message="Troubleshooting Steps"
                    description={
                      <ul>
                        <li>Make sure the backend server is running on port 8000</li>
                        <li>Check if Neo4j is running on port 7474</li>
                        <li>Verify Redis is running on port 6379</li>
                        <li>Check the browser console for additional errors</li>
                      </ul>
                    }
                    type="warning"
                  />
                </div>
              </div>
            )}
            
            <Button 
              onClick={checkAPI} 
              style={{ marginTop: 16 }}
              loading={apiStatus === 'loading'}
            >
              Retry API Connection
            </Button>
          </Card>

          <Card title="Browser Information" size="small">
            <Descriptions size="small">
              <Descriptions.Item label="User Agent">
                {navigator.userAgent}
              </Descriptions.Item>
              <Descriptions.Item label="Language">
                {navigator.language}
              </Descriptions.Item>
              <Descriptions.Item label="Platform">
                {navigator.platform}
              </Descriptions.Item>
              <Descriptions.Item label="Cookies Enabled">
                {navigator.cookieEnabled ? 'Yes' : 'No'}
              </Descriptions.Item>
            </Descriptions>
          </Card>

          <Alert
            message="If you see this panel, the frontend is working correctly"
            description="The white screen issue might be related to API connectivity or component loading errors. Check the browser console (F12) for JavaScript errors."
            type="info"
            showIcon
          />
        </Space>
      </Card>
    </div>
  );
};

export default DiagnosticPanel;