import React, { useState } from 'react';
import { Card, Button, message, Row, Col, Divider, Input, Modal } from 'antd';
import { apiService } from '../services/api';
import QuickToolsWidget from './QuickToolsWidget';
import ToolsSystemStats from './ToolsSystemStats';
import StatusPanel from './StatusPanel';
import ToolsCatalogWidget from './ToolsCatalogWidget';

const ControlPanel: React.FC = () => {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [modalContent, setModalContent] = useState<{ title: string; content: any } | null>(null);
  const [trainDir, setTrainDir] = useState('');
  const [queryText, setQueryText] = useState('');
  const [aiPrompt, setAiPrompt] = useState('');
  const [loading, setLoading] = useState<Record<string, boolean>>({});

  const showModal = (title: string, content: any) => {
    setModalContent({ title, content });
    setIsModalVisible(true);
  };

  const handleOk = () => {
    setIsModalVisible(false);
  };

  const handleCancel = () => {
    setIsModalVisible(false);
  };

  const handleAction = async (action: string, apiCall: () => Promise<any>, successMessage: string) => {
    try {
      setLoading(prev => ({ ...prev, [action]: true }));
      const result = await apiCall();
      
      // Handle AI asynchronous response format
      if (action === 'ai' && result.status === 'processing') {
        message.success(`AI request started (Task ID: ${result.task_id}). Please check back later for the result.`);
        showModal(`${action} Результат`, `AI request started (Task ID: ${result.task_id})\n${result.message}\n\nPlease wait while I process your request. I'll send you the response when it's ready.`);
      } else {
        message.success(successMessage);
        // Show result in modal for better visibility
        showModal(`${action} Результат`, JSON.stringify(result, null, 2));
      }
    } catch (error: any) {
      console.error(`Ошибка выполнения ${action}:`, error);
      message.error(`Не удалось выполнить ${action}: ${error.response?.data?.error || error.message}`);
    } finally {
      setLoading(prev => ({ ...prev, [action]: false }));
    }
  };

  const checkHealth = async () => {
    const health = await apiService.getHealth();
    message.info(`Состояние системы: ${health.status}`);
    showModal('Состояние системы', health);
  };

  const handleTrain = async () => {
    if (trainDir) {
      await handleAction('train', () => apiService.train({}), 'Обучение запущено');
    } else {
      await handleAction('train', () => apiService.train(), 'Обучение запущено');
    }
  };

  const handleQuery = async () => {
    if (!queryText.trim()) {
      message.warning('Введите текст запроса');
      return;
    }
    
    await handleAction('query', () => apiService.query({ query: queryText }), 'Запрос выполнен');
  };

  const handleAI = async () => {
    if (!aiPrompt.trim()) {
      message.warning('Введите промпт для AI');
      return;
    }
    
    await handleAction('ai', () => apiService.callAI({ prompt: aiPrompt }), 'AI вызван');
  };

  const handleDB = async () => {
    await handleAction('db', () => apiService.executeCypher({ cypher: 'MATCH (n) RETURN count(n) AS nodeCount' }), 'Запрос к БД выполнен');
  };

  const handleBot = async () => {
    await handleAction('bot', () => apiService.sendBotCommand({ cmd: 'status' }), 'Команда боту отправлена');
  };

  const handleQuickToolExecute = (toolName: string) => {
    message.info(`Quick tool executed: ${toolName}`);
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* Quick Tools Widget */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <QuickToolsWidget onToolExecute={handleQuickToolExecute} />
        </Col>
        <Col span={16}>
          <ToolsSystemStats />
        </Col>
      </Row>

      <Card title="Панель управления системой" bordered={false}>
        <Row gutter={[16, 16]}>
          <Col span={12}>
            <Card title="Основные команды" size="small">
              <div style={{ marginBottom: '10px' }}>
                <Input 
                  placeholder="Директория для обучения (опционально)" 
                  value={trainDir}
                  onChange={(e) => setTrainDir(e.target.value)}
                  style={{ marginBottom: '10px' }}
                />
                <Button 
                  type="primary" 
                  onClick={handleTrain}
                  loading={loading.train}
                  style={{ marginRight: 8, marginBottom: 8 }}
                >
                  /train
                </Button>
              </div>
              
              <div style={{ marginBottom: '10px' }}>
                <Input 
                  placeholder="Текст запроса" 
                  value={queryText}
                  onChange={(e) => setQueryText(e.target.value)}
                  style={{ marginBottom: '10px' }}
                />
                <Button 
                  onClick={handleQuery}
                  loading={loading.query}
                  style={{ marginRight: 8, marginBottom: 8 }}
                >
                  /query
                </Button>
              </div>
              
              <div style={{ marginBottom: '10px' }}>
                <Input 
                  placeholder="Промпт для AI" 
                  value={aiPrompt}
                  onChange={(e) => setAiPrompt(e.target.value)}
                  style={{ marginBottom: '10px' }}
                />
                <Button 
                  onClick={handleAI}
                  loading={loading.ai}
                  style={{ marginRight: 8, marginBottom: 8 }}
                >
                  /ai
                </Button>
              </div>
            </Card>
          </Col>
          
          <Col span={12}>
            <Card title="Инструменты" size="small">
              <Button 
                onClick={handleDB}
                loading={loading.db}
                style={{ marginRight: 8, marginBottom: 8 }}
              >
                /db
              </Button>
              <Button 
                onClick={handleBot}
                loading={loading.bot}
                style={{ marginRight: 8, marginBottom: 8 }}
              >
                /bot-send
              </Button>
              <Button 
                onClick={checkHealth}
                loading={loading.health}
                style={{ marginRight: 8, marginBottom: 8 }}
              >
                /health
              </Button>
            </Card>
          </Col>
        </Row>
        
        <Divider />
        
        <Card title="Статус системы" size="small">
          <p>Состояние компонентов системы:</p>
          <Button 
            type="dashed" 
            onClick={checkHealth}
            loading={loading.health}
          >
            Проверить состояние
          </Button>
        </Card>
      </Card>

      <ToolsCatalogWidget />
      
      <Modal
        title={modalContent?.title || 'Результат'}
        open={isModalVisible}
        onOk={handleOk}
        onCancel={handleCancel}
        width={800}
        bodyStyle={{ maxHeight: '600px', overflowY: 'auto' }}
      >
        <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
          {modalContent?.content || 'Нет данных'}
        </pre>
      </Modal>
    </div>
  );
};

export default ControlPanel;