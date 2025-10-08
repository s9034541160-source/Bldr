/**
 * Tool Page Component
 * Отдельная страница для выполнения инструмента
 */

import React, { useState, useEffect } from 'react';
import { Card, Button, Space, Spin, Alert, message, Breadcrumb } from 'antd';
import { ArrowLeftOutlined, ReloadOutlined, FullscreenOutlined } from '@ant-design/icons';
import DynamicToolForm from './DynamicToolForm';
import ToolResultDisplay from './ToolResultDisplay';
import { apiService } from '../services/api';

interface ToolPageProps {
  toolName: string;
  initialParams?: Record<string, any>;
  onBack?: () => void;
}

const ToolPage: React.FC<ToolPageProps> = ({ 
  toolName, 
  initialParams = {},
  onBack 
}) => {
  const [toolInfo, setToolInfo] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [params, setParams] = useState<Record<string, any>>(initialParams);

  // Загрузить информацию об инструменте
  useEffect(() => {
    const loadToolInfo = async () => {
      try {
        setLoading(true);
        const info = await apiService.getToolInfo(toolName);
        setToolInfo(info);
      } catch (err: any) {
        setError(`Ошибка загрузки инструмента: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    loadToolInfo();
  }, [toolName]);

  // Выполнить инструмент
  const executeTool = async (toolParams: Record<string, any>) => {
    try {
      setExecuting(true);
      setError(null);
      setResult(null);

      const response = await apiService.executeTool(toolName, toolParams);
      setResult(response);
      
      if (response.status === 'error') {
        setError(response.error);
        message.error(`Ошибка выполнения: ${response.error}`);
      } else {
        message.success('Инструмент выполнен успешно');
      }
    } catch (err: any) {
      setError(`Ошибка выполнения: ${err.message}`);
      message.error(`Ошибка выполнения: ${err.message}`);
    } finally {
      setExecuting(false);
    }
  };

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '50vh' 
      }}>
        <Spin size="large" />
      </div>
    );
  }

  if (error && !toolInfo) {
    return (
      <div style={{ padding: 24 }}>
        <Alert
          message="Ошибка"
          description={error}
          type="error"
          showIcon
          action={
            <Button size="small" onClick={() => window.location.reload()}>
              Перезагрузить
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div style={{ padding: 24 }}>
      {/* Заголовок */}
      <div style={{ marginBottom: 24 }}>
        <Breadcrumb style={{ marginBottom: 16 }}>
          <Breadcrumb.Item>
            <Button 
              type="link" 
              icon={<ArrowLeftOutlined />}
              onClick={onBack || (() => window.history.back())}
            >
              Назад
            </Button>
          </Breadcrumb.Item>
          <Breadcrumb.Item>Инструменты</Breadcrumb.Item>
          <Breadcrumb.Item>{toolName}</Breadcrumb.Item>
        </Breadcrumb>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 24 }}>
              {toolInfo?.title || toolName}
            </h1>
            <p style={{ margin: '8px 0 0 0', color: '#666' }}>
              {toolInfo?.description || 'Выполнение инструмента'}
            </p>
          </div>
          
          <Space>
            <Button 
              icon={<ReloadOutlined />}
              onClick={() => window.location.reload()}
            >
              Обновить
            </Button>
            <Button 
              icon={<FullscreenOutlined />}
              onClick={() => {
                if (document.documentElement.requestFullscreen) {
                  document.documentElement.requestFullscreen();
                }
              }}
            >
              Полный экран
            </Button>
          </Space>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        {/* Левая панель - Форма параметров */}
        <Card title="Параметры инструмента" size="small">
          <DynamicToolForm
            toolInfo={toolInfo}
            initialValues={params}
            onValuesChange={setParams}
            onSubmit={executeTool}
            submitButtonText="Выполнить"
            showSubmitButton={true}
            loading={executing}
          />
        </Card>

        {/* Правая панель - Результаты */}
        <Card title="Результаты" size="small">
          {executing && (
            <div style={{ textAlign: 'center', padding: 24 }}>
              <Spin size="large" />
              <p style={{ marginTop: 16 }}>Выполнение инструмента...</p>
            </div>
          )}

          {error && !executing && (
            <Alert
              message="Ошибка выполнения"
              description={error}
              type="error"
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}

          {result && !executing && (
            <ToolResultDisplay 
              result={result}
              toolName={toolName}
            />
          )}

          {!result && !error && !executing && (
            <div style={{ 
              textAlign: 'center', 
              padding: 24, 
              color: '#999' 
            }}>
              Заполните параметры и нажмите "Выполнить"
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

export default ToolPage;
