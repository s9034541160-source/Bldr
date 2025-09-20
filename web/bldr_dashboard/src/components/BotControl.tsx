import React, { useState } from 'react';
import { Card, Input, Button, List, message, Typography, Collapse, Tag } from 'antd';
import { apiService } from '../services/api';

const { TextArea } = Input;
const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;

const BotControl: React.FC = () => {
  const [command, setCommand] = useState('');
  const [history, setHistory] = useState<Array<{cmd: string, response: string, timestamp: string}>>([]);
  const [loading, setLoading] = useState(false);

  // Predefined bot commands with descriptions
  const botCommands = [
    {
      command: "status",
      description: "Проверить статус бота",
      example: "status"
    },
    {
      command: "help",
      description: "Получить список доступных команд",
      example: "help"
    },
    {
      command: "projects",
      description: "Получить список проектов",
      example: "projects"
    },
    {
      command: "query",
      description: "Выполнить запрос к базе знаний",
      example: "query Какие нормативные документы относятся к безопасности?"
    },
    {
      command: "analyze",
      description: "Проанализировать документ",
      example: "analyze [название документа]"
    },
    {
      command: "notify",
      description: "Отправить уведомление",
      example: "notify Важное обновление системы"
    }
  ];

  const sendCommand = async () => {
    if (!command.trim()) {
      message.warning('Пожалуйста, введите команду');
      return;
    }
    
    try {
      setLoading(true);
      
      const response = await apiService.sendBotCommand({ cmd: command });
      
      if (response) {
        const newEntry = {
          cmd: command,
          response: response.message || 'Нет ответа',
          timestamp: new Date().toLocaleTimeString()
        };
        
        setHistory(prev => [newEntry, ...prev]);
        setCommand('');
        message.success('Команда отправлена успешно');
      } else {
        message.error('Получен пустой ответ от сервера');
        
        const errorEntry = {
          cmd: command,
          response: 'Ошибка: Пустой ответ от сервера',
          timestamp: new Date().toLocaleTimeString()
        };
        
        setHistory(prev => [errorEntry, ...prev]);
      }
      
    } catch (error: any) {
      console.error('Ошибка отправки команды:', error);
      message.error(`Не удалось отправить команду боту: ${error.response?.data?.error || error.message}`);
      
      const errorEntry = {
        cmd: command,
        response: `Ошибка: ${error.response?.data?.error || error.message}`,
        timestamp: new Date().toLocaleTimeString()
      };
      
      setHistory(prev => [errorEntry, ...prev]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendCommand();
    }
  };

  const handlePredefinedCommand = (cmd: string) => {
    setCommand(cmd);
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card title="Управление ботом" bordered={false}>
        <Card title="О боте" size="small" style={{ marginBottom: 24 }}>
          <Paragraph>
            Telegram бот интегрирован с системой Bldr Empire и позволяет:
          </Paragraph>
          <ul>
            <li>Получать уведомления о событиях в системе</li>
            <li>Выполнять запросы к базе знаний в формате естественного языка</li>
            <li>Управлять проектами и документами</li>
            <li>Получать аналитическую информацию</li>
          </ul>
          <Text type="secondary">
            Для активации бота необходимо настроить TELEGRAM_BOT_TOKEN в файле .env
          </Text>
        </Card>
        
        <Card title="Доступные команды" size="small" style={{ marginBottom: 24 }}>
          <Collapse>
            <Panel header="Показать список команд" key="1">
              <List
                dataSource={botCommands}
                renderItem={item => (
                  <List.Item 
                    actions={[
                      <Button 
                        type="link" 
                        onClick={() => handlePredefinedCommand(item.example)}
                      >
                        Использовать
                      </Button>
                    ]}
                  >
                    <List.Item.Meta
                      title={<Text code>{item.command}</Text>}
                      description={
                        <div>
                          <div>{item.description}</div>
                          <Text type="secondary">Пример: {item.example}</Text>
                        </div>
                      }
                    />
                  </List.Item>
                )}
              />
            </Panel>
          </Collapse>
        </Card>
        
        <Card title="Отправка команды" size="small">
          <TextArea
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            onPressEnter={handleKeyPress}
            placeholder="Введите команду для отправки боту..."
            autoSize={{ minRows: 3, maxRows: 6 }}
            disabled={loading}
          />
          <Button 
            type="primary" 
            onClick={sendCommand} 
            loading={loading}
            style={{ marginTop: 16 }}
          >
            Отправить команду
          </Button>
        </Card>
        
        <Card title="История команд" size="small" style={{ marginTop: 24 }}>
          {history && history.length > 0 ? (
            <List
              dataSource={history}
              renderItem={(item) => (
                <List.Item>
                  <div style={{ width: '100%' }}>
                    <div>
                      <Tag color="blue">Команда</Tag> {item.cmd || 'Нет данных'}
                    </div>
                    <div style={{ marginTop: 8 }}>
                      <Tag color="green">Ответ</Tag> 
                      <div style={{ 
                        marginTop: 4, 
                        padding: 8, 
                        backgroundColor: '#f5f5f5', 
                        borderRadius: 4,
                        whiteSpace: 'pre-wrap'
                      }}>
                        {item.response || 'Нет данных'}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right', fontSize: '12px', color: '#888', marginTop: 8 }}>
                      {item.timestamp || 'Нет времени'}
                    </div>
                  </div>
                </List.Item>
              )}
            />
          ) : (
            <div>
              <p>История команд будет отображаться здесь</p>
              <Text type="secondary">
                Подсказка: Используйте предопределенные команды выше или введите свою собственную.
                Например: <Text code>status</Text> или <Text code>help</Text>
              </Text>
            </div>
          )}
        </Card>
      </Card>
    </div>
  );
};

export default BotControl;