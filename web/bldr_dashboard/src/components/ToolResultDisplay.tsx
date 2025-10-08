import React from 'react';
import { 
  Alert, 
  Card, 
  Table, 
  Image, 
  Button, 
  Space, 
  Typography, 
  Divider,
  Tag,
  Tooltip,
  Collapse
} from 'antd';
import { 
  DownloadOutlined, 
  EyeOutlined, 
  FileTextOutlined,
  BarChartOutlined,
  TableOutlined,
  PictureOutlined
} from '@ant-design/icons';

const { Text, Paragraph } = Typography;
const { Panel } = Collapse;

interface ToolResult {
  status: 'success' | 'error' | 'warning';
  data?: any;
  files?: string[];
  metadata?: any;
  error?: string;
  execution_time?: number;
  // Standardized result fields
  result_type?: 'text' | 'json' | 'file' | 'image' | 'table' | 'chart';
  result_title?: string;
  result_content?: string;
  result_url?: string;
  result_table?: Array<Record<string, any>>;
  result_chart_config?: any;
}

interface ToolResultDisplayProps {
  result: ToolResult;
  toolName: string;
  compact?: boolean;
}

const ToolResultDisplay: React.FC<ToolResultDisplayProps> = ({ 
  result, 
  toolName, 
  compact = false 
}) => {
  // Debug: log the result to see what we're getting
  console.log('ToolResultDisplay received:', { result, toolName });
  console.log('ToolResultDisplay result_type:', result.result_type);
  console.log('ToolResultDisplay result_table:', result.result_table);
  console.log('ToolResultDisplay result_table length:', result.result_table?.length || 0);

  // УНИВЕРСАЛЬНАЯ ЛОГИКА: Автоматическое определение типа результата
  const detectResultType = (): string => {
    // Если явно указан тип - используем его
    if (result.result_type) {
      return result.result_type;
    }

    // Автоматическое определение по содержимому
    if (result.result_table && result.result_table.length > 0) {
      return 'table';
    }
    if (result.result_content) {
      return 'text';
    }
    if (result.result_url) {
      if (result.result_url.match(/\.(jpg|jpeg|png|gif|webp)$/i)) {
        return 'image';
      }
      return 'file';
    }
    if (result.data && typeof result.data === 'object') {
      return 'json';
    }
    
    return 'json'; // По умолчанию
  };

  // УНИВЕРСАЛЬНАЯ ЛОГИКА: Нормализация результата для любого tool
  const normalizeResult = () => {
    const normalized = { ...result };
    
    // Если tool вернул данные в data.results, перемещаем в result_table
    if (result.data?.results && !result.result_table) {
      normalized.result_table = result.data.results;
      normalized.result_type = 'table';
    }
    
    // Если tool вернул текст в data.content, перемещаем в result_content
    if (result.data?.content && !result.result_content) {
      normalized.result_content = result.data.content;
      normalized.result_type = 'text';
    }
    
    // Если tool вернул данные в data напрямую (массив), перемещаем в result_table
    if (result.data && Array.isArray(result.data) && !result.result_table) {
      normalized.result_table = result.data;
      normalized.result_type = 'table';
    }
    
    return normalized;
  };

  const normalizedResult = normalizeResult();

  const detectedType = detectResultType();
  const renderTextResult = () => {
    // УНИВЕРСАЛЬНАЯ ПОДДЕРЖКА: Ищем текст в разных местах
    let textContent = normalizedResult.result_content;
    
    // Если нет result_content, ищем в data
    if (!textContent && result.data) {
      if (typeof result.data === 'string') {
        textContent = result.data;
      } else if (result.data.content) {
        textContent = result.data.content;
      } else if (result.data.text) {
        textContent = result.data.text;
      }
    }
    
    if (!textContent) return null;
    
    return (
      <Card size="small" title="Результат" style={{ marginTop: 8 }}>
        <Paragraph style={{ 
          whiteSpace: 'pre-wrap', 
          margin: 0, 
          color: '#000',
          backgroundColor: '#fff',
          padding: 12,
          borderRadius: 4,
          border: '1px solid #d9d9d9'
        }}>
          {textContent}
        </Paragraph>
      </Card>
    );
  };

  const renderTableResult = () => {
    // УНИВЕРСАЛЬНАЯ ПОДДЕРЖКА: Используем нормализованные данные
    let tableData = normalizedResult.result_table;
    
    if (!tableData || tableData.length === 0) return null;
    
    const columns = Object.keys(tableData[0]).map(key => ({
      title: key,
      dataIndex: key,
      key: key,
      render: (text: any) => {
        if (typeof text === 'object') {
          return <Text code>{JSON.stringify(text)}</Text>;
        }
        return text;
      }
    }));

    return (
      <Card size="small" title="Таблица результатов" style={{ marginTop: 8 }}>
        <Table 
          dataSource={tableData} 
          columns={columns} 
          pagination={{ pageSize: 10 }}
          size="small"
        />
      </Card>
    );
  };

  const renderFileResult = () => {
    if (!result.result_url && (!result.files || result.files.length === 0)) return null;
    
    const files = result.files || [result.result_url].filter(Boolean);
    
    const handleDownload = (file: string) => {
      // Создаем ссылку для скачивания
      const link = document.createElement('a');
      link.href = file;
      link.download = file.split('/').pop() || 'download';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    };

    const handlePreview = (file: string) => {
      // Открываем файл в новой вкладке для просмотра
      window.open(file, '_blank');
    };
    
    return (
      <Card 
        size="small" 
        title="📁 Файлы результатов" 
        style={{ 
          marginTop: 8,
          background: 'linear-gradient(135deg, #f6ffed 0%, #f0f9ff 100%)',
          border: '1px solid #52c41a'
        }}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          {files.map((file, index) => (
            <div key={index} style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              padding: '12px 16px',
              background: 'rgba(82, 196, 26, 0.05)',
              border: '1px solid rgba(82, 196, 26, 0.2)',
              borderRadius: '8px',
              transition: 'all 0.2s ease'
            }}>
              <Space>
                <FileTextOutlined style={{ color: '#52c41a', fontSize: '16px' }} />
                <Text style={{ fontWeight: '500' }}>{file}</Text>
              </Space>
              <Space>
                <Tooltip title="Просмотр файла">
                  <Button 
                    size="small" 
                    icon={<EyeOutlined />}
                    onClick={() => handlePreview(file)}
                    style={{
                      background: 'rgba(24, 144, 255, 0.1)',
                      border: '1px solid rgba(24, 144, 255, 0.3)',
                      color: '#1890ff'
                    }}
                  />
                </Tooltip>
                <Tooltip title="Скачать файл">
                  <Button 
                    size="small" 
                    icon={<DownloadOutlined />}
                    onClick={() => handleDownload(file)}
                    style={{
                      background: 'rgba(82, 196, 26, 0.1)',
                      border: '1px solid rgba(82, 196, 26, 0.3)',
                      color: '#52c41a'
                    }}
                  />
                </Tooltip>
              </Space>
            </div>
          ))}
        </Space>
      </Card>
    );
  };

  const renderImageResult = () => {
    if (!result.result_url) return null;
    
    return (
      <Card size="small" title="Изображение" style={{ marginTop: 8 }}>
        <Image
          src={result.result_url}
          alt={result.result_title || 'Result image'}
          style={{ maxWidth: '100%', maxHeight: 400 }}
        />
      </Card>
    );
  };

  const renderJsonResult = () => {
    if (!result.data) return null;
    
    return (
      <Card size="small" title="Данные" style={{ marginTop: 8 }}>
        <pre style={{ 
          background: '#f5f5f5', 
          padding: 12, 
          borderRadius: 4, 
          maxHeight: 300, 
          overflow: 'auto',
          fontSize: '12px',
          margin: 0,
          color: '#000',
          border: '1px solid #d9d9d9'
        }}>
          {JSON.stringify(result.data, null, 2)}
        </pre>
      </Card>
    );
  };

  const renderChartResult = () => {
    if (!result.result_chart_config) return null;
    
    return (
      <Card size="small" title="График" style={{ marginTop: 8 }}>
        <div style={{ 
          height: 300, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          background: '#fafafa',
          border: '1px dashed #d9d9d9'
        }}>
          <Space direction="vertical" align="center">
            <BarChartOutlined style={{ fontSize: 48, color: '#1890ff' }} />
            <Text type="secondary">График будет отображен здесь</Text>
            <Text code>{JSON.stringify(result.result_chart_config)}</Text>
          </Space>
        </div>
      </Card>
    );
  };

  const getResultIcon = () => {
    switch (result.result_type) {
      case 'text': return <FileTextOutlined />;
      case 'table': return <TableOutlined />;
      case 'image': return <PictureOutlined />;
      case 'chart': return <BarChartOutlined />;
      case 'file': return <DownloadOutlined />;
      default: return <FileTextOutlined />;
    }
  };

  const getResultTypeTitle = () => {
    switch (result.result_type) {
      case 'text': return 'Текстовый результат';
      case 'table': return 'Таблица';
      case 'image': return 'Изображение';
      case 'chart': return 'График';
      case 'file': return 'Файлы';
      case 'json': return 'JSON данные';
      default: return 'Результат';
    }
  };

  if (compact) {
    return (
      <Alert
        message={result.status === 'success' ? 'Success' : 'Error'}
        description={
          result.error || 
          `Executed successfully in ${result.execution_time?.toFixed(3)}s`
        }
        type={result.status === 'success' ? 'success' : 'error'}
        showIcon
      />
    );
  }

  return (
    <div>
      {/* Status Alert */}
      <Alert
        message={result.status === 'success' ? 'Success' : 'Error'}
        description={
          result.error || 
          `Executed successfully in ${result.execution_time?.toFixed(3)}s`
        }
        type={result.status === 'success' ? 'success' : 'error'}
        showIcon
        style={{ marginBottom: 16 }}
      />

      {/* Execution Metadata */}
      {result.metadata && (
        <Card size="small" style={{ marginBottom: 16 }}>
          <Space wrap>
            {result.execution_time && (
              <Tag color="blue">⏱️ {result.execution_time.toFixed(3)}s</Tag>
            )}
            {result.metadata.processing_time && (
              <Tag color="green">🔄 {result.metadata.processing_time}ms</Tag>
            )}
            {result.metadata.error_category && (
              <Tag color="red">❌ {result.metadata.error_category}</Tag>
            )}
            {result.metadata.suggestions && (
              <Tag color="orange">💡 {result.metadata.suggestions}</Tag>
            )}
          </Space>
        </Card>
      )}

      {/* Result Content */}
      {result.status === 'success' && (
        <Collapse defaultActiveKey={['result']}>
          <Panel 
            header={
              <Space>
                {getResultIcon()}
                <span>{result.result_title || getResultTypeTitle()}</span>
              </Space>
            } 
            key="result"
          >
            {/* УНИВЕРСАЛЬНОЕ ОТОБРАЖЕНИЕ: Автоматическое определение типа */}
            {detectedType === 'text' && renderTextResult()}
            {(detectedType === 'table' || detectedType === 'advanced_table') && renderTableResult()}
            {detectedType === 'file' && renderFileResult()}
            {detectedType === 'image' && renderImageResult()}
            {detectedType === 'chart' && renderChartResult()}
            {detectedType === 'json' && renderJsonResult()}
            
            {/* Fallback: if no specific result type but we have data, show it */}
            {!result.result_type && result.data && (
              <div style={{ marginTop: 16 }}>
                <h5>Raw Data:</h5>
                <pre style={{ 
                  background: '#f5f5f5', 
                  padding: 12, 
                  borderRadius: 4, 
                  maxHeight: 300, 
                  overflow: 'auto',
                  fontSize: '12px',
                  margin: 0,
                  color: '#000',
                  border: '1px solid #d9d9d9'
                }}>
                  {JSON.stringify(result.data, null, 2)}
                </pre>
              </div>
            )}
          </Panel>
        </Collapse>
      )}
    </div>
  );
};

export default ToolResultDisplay;