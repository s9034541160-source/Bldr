/**
 * Tool Result Display Component
 * Shows standardized tool execution results with proper formatting
 */

import React from 'react';
import { 
  Card, 
  Alert, 
  Descriptions, 
  Tag, 
  Typography, 
  Space, 
  Button, 
  Collapse,
  List,
  Divider
} from 'antd';
import { 
  CheckCircleOutlined, 
  CloseCircleOutlined, 
  WarningOutlined,
  DownloadOutlined,
  InfoCircleOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';

const { Text, Paragraph } = Typography;
const { Panel } = Collapse;

interface StandardResponse {
  status: 'success' | 'error' | 'warning';
  data?: any;
  files?: string[];
  metadata?: {
    processing_time?: number;
    parameters_used?: Record<string, any>;
    error_category?: string;
    suggestions?: string;
  };
  error?: string;
  execution_time?: number;
  tool_name: string;
  timestamp: string;
}

interface ToolResultDisplayProps {
  result: StandardResponse;
  onDownloadFile?: (filePath: string) => void;
  className?: string;
}

const ToolResultDisplay: React.FC<ToolResultDisplayProps> = ({ 
  result, 
  onDownloadFile,
  className = '' 
}) => {
  const getStatusIcon = () => {
    switch (result.status) {
      case 'success':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'error':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'warning':
        return <WarningOutlined style={{ color: '#faad14' }} />;
      default:
        return <InfoCircleOutlined />;
    }
  };

  const getStatusColor = () => {
    switch (result.status) {
      case 'success':
        return 'success';
      case 'error':
        return 'error';
      case 'warning':
        return 'warning';
      default:
        return 'info';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return timestamp;
    }
  };

  const renderData = (data: any) => {
    if (!data) return null;

    if (typeof data === 'string') {
      return <Paragraph copyable>{data}</Paragraph>;
    }

    if (typeof data === 'object') {
      return (
        <Collapse size="small">
          <Panel header="View Data" key="data">
            <pre style={{ 
              background: '#f5f5f5', 
              padding: '12px', 
              borderRadius: '4px',
              fontSize: '12px',
              maxHeight: '300px',
              overflow: 'auto'
            }}>
              {JSON.stringify(data, null, 2)}
            </pre>
          </Panel>
        </Collapse>
      );
    }

    return <Text>{String(data)}</Text>;
  };

  return (
    <Card 
      className={className}
      title={
        <Space>
          {getStatusIcon()}
          <span>Tool Result: {result.tool_name}</span>
          <Tag color={getStatusColor()}>{result.status.toUpperCase()}</Tag>
        </Space>
      }
      size="small"
    >
      {/* Status Alert */}
      <Alert
        message={
          result.status === 'success' 
            ? 'Tool executed successfully' 
            : result.status === 'error'
            ? 'Tool execution failed'
            : 'Tool executed with warnings'
        }
        description={result.error}
        type={getStatusColor() as any}
        showIcon
        style={{ marginBottom: 16 }}
      />

      {/* Basic Information */}
      <Descriptions size="small" column={2} style={{ marginBottom: 16 }}>
        <Descriptions.Item label="Tool">
          <Text code>{result.tool_name}</Text>
        </Descriptions.Item>
        <Descriptions.Item label="Status">
          <Tag color={getStatusColor()}>{result.status}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Execution Time">
          <Space>
            <ClockCircleOutlined />
            {result.execution_time ? `${result.execution_time.toFixed(3)}s` : 'N/A'}
          </Space>
        </Descriptions.Item>
        <Descriptions.Item label="Timestamp">
          {formatTimestamp(result.timestamp)}
        </Descriptions.Item>
      </Descriptions>

      {/* Files */}
      {result.files && result.files.length > 0 && (
        <>
          <Divider orientation="left" orientationMargin="0">
            Generated Files ({result.files.length})
          </Divider>
          <List
            size="small"
            dataSource={result.files}
            renderItem={(file) => (
              <List.Item
                actions={[
                  onDownloadFile && (
                    <Button
                      type="link"
                      size="small"
                      icon={<DownloadOutlined />}
                      onClick={() => onDownloadFile(file)}
                    >
                      Download
                    </Button>
                  )
                ].filter(Boolean)}
              >
                <Text code>{file}</Text>
              </List.Item>
            )}
          />
        </>
      )}

      {/* Data */}
      {result.data && (
        <>
          <Divider orientation="left" orientationMargin="0">
            Result Data
          </Divider>
          {renderData(result.data)}
        </>
      )}

      {/* Metadata */}
      {result.metadata && (
        <>
          <Divider orientation="left" orientationMargin="0">
            Execution Metadata
          </Divider>
          <Descriptions size="small" column={1}>
            {result.metadata.processing_time && (
              <Descriptions.Item label="Processing Time">
                {result.metadata.processing_time.toFixed(3)}s
              </Descriptions.Item>
            )}
            {result.metadata.error_category && (
              <Descriptions.Item label="Error Category">
                <Tag color="red">{result.metadata.error_category}</Tag>
              </Descriptions.Item>
            )}
            {result.metadata.suggestions && (
              <Descriptions.Item label="Suggestions">
                <Alert
                  message={result.metadata.suggestions}
                  type="info"
                  showIcon
                  size="small"
                />
              </Descriptions.Item>
            )}
            {result.metadata.parameters_used && (
              <Descriptions.Item label="Parameters Used">
                <Collapse size="small">
                  <Panel header="View Parameters" key="params">
                    <pre style={{ 
                      background: '#f5f5f5', 
                      padding: '8px', 
                      borderRadius: '4px',
                      fontSize: '12px'
                    }}>
                      {JSON.stringify(result.metadata.parameters_used, null, 2)}
                    </pre>
                  </Panel>
                </Collapse>
              </Descriptions.Item>
            )}
          </Descriptions>
        </>
      )}
    </Card>
  );
};

export default ToolResultDisplay;