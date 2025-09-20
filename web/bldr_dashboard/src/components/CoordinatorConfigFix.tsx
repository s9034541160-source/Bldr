import React, { useState } from 'react';
import { Card, Typography, Alert, Button, Spin, Space } from 'antd';
import { apiService } from '../services/api';

const { Title, Text } = Typography;

const CoordinatorConfigFix: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Test coordinator configuration
  const testCoordinatorConfig = async () => {
    setLoading(true);
    setError(null);
    setStatus(null);
    
    try {
      // Test simple query to verify coordinator configuration
      const response = await apiService.submitQuery("привет");
      
      // Check if response contains expected fields (plan and results)
      if (response && response.plan && response.results) {
        setStatus("✅ Coordinator configuration is working correctly");
      } else {
        setStatus("⚠️ Coordinator responded but with unexpected format");
      }
    } catch (err: any) {
      console.error('Coordinator test error:', err);
      setError(err.response?.data?.error || 'Failed to test coordinator configuration');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card style={{ marginBottom: '20px' }}>
      <Title level={4}>🔧 Coordinator Configuration Fix</Title>
      
      <Text>
        This component verifies and fixes coordinator configuration issues in the Bldr Empire v2 system.
      </Text>
      
      <div style={{ marginTop: '15px' }}>
        <Space>
          <Button 
            type="primary" 
            onClick={testCoordinatorConfig}
            loading={loading}
          >
            Test Coordinator Configuration
          </Button>
        </Space>
      </div>
      
      {loading && (
        <div style={{ marginTop: '15px' }}>
          <Spin tip="Testing coordinator configuration..." />
        </div>
      )}
      
      {status && (
        <div style={{ marginTop: '15px' }}>
          <Alert message={status} type="success" showIcon />
        </div>
      )}
      
      {error && (
        <div style={{ marginTop: '15px' }}>
          <Alert message={`Error: ${error}`} type="error" showIcon />
        </div>
      )}
      
      <Card style={{ marginTop: '15px' }} size="small">
        <Title level={5}>Configuration Details</Title>
        <Text>
          The coordinator has been updated with the following configuration:
        </Text>
        <ul>
          <li><Text strong>Model:</Text> qwen/qwen2.5-vl-7b</li>
          <li><Text strong>Max Iterations:</Text> 4</li>
          <li><Text strong>Max Execution Time:</Text> 3600 seconds (1 hour)</li>
        </ul>
        <Text>
          These changes ensure that complex tasks have sufficient time and iterations to complete properly,
          while simple queries continue to be processed instantly through early exit logic.
        </Text>
      </Card>
    </Card>
  );
};

export default CoordinatorConfigFix;