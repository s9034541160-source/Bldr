import React, { useState, useRef, useEffect } from 'react';
import { apiService } from '../services/api';
import { Button, Input, message, Select, Card, Typography, Switch, Upload, Modal } from 'antd';
import { UploadOutlined, DownloadOutlined, ClearOutlined } from '@ant-design/icons';
import { useStore } from '../store';

const { Title, Text } = Typography;

const AIShell: React.FC = () => {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedRole, setSelectedRole] = useState('coordinator'); // Default to coordinator
  const [thinkingMode, setThinkingMode] = useState(true); // Thinking mode enabled by default
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [selectedFileId, setSelectedFileId] = useState('');
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [wsStatus, setWsStatus] = useState('Disconnected');
  const { theme, chatHistory, setChatHistory, addChatMessage, clearChatHistory } = useStore(); // Get chat history from store

  // Role options with descriptions
  const roleOptions = [
    {
      value: 'coordinator',
      label: 'Координатор (Qwen2.5-VL-7B)',
      description: 'Главный координатор системы Bldr2. Оркестрирует роли, анализирует запросы, планирует шаги, делегирует задачи по JSON-плану. Максимум 4 итерации, 1 час выполнения.'
    },
    {
      value: 'chief_engineer',
      label: 'Главный инженер (Qwen2.5-VL-7B)',
      description: 'Отвечает за технический дизайн, инновации, безопасность, нормативные требования. Может анализировать фото/планы.'
    },
    {
      value: 'structural_geotech_engineer',
      label: 'Инженер по конструкциям (Mistral-Nemo-Instruct-2407)',
      description: 'Специализируется на расчетах конструкций, геотехническом анализе, моделировании МКЭ.'
    },
    {
      value: 'analyst',
      label: 'Аналитик (Mistral-Nemo-Instruct-2407)',
      description: 'Работает с оценками, бюджетами, стоимостью, прогнозированием, тендерами ФЗ-44.'
    },
    {
      value: 'project_manager',
      label: 'Менеджер проекта (DeepSeek-R1-0528-Qwen3-8B)',
      description: 'Управляет планированием проекта, сроками, распределением ресурсов, анализом рисков.'
    }
  ];

  // WebSocket connection
  useEffect(() => {
    // Get token from localStorage with correct key
    const token = localStorage.getItem('auth-token');
    
    if (token) {
      const websocket = new WebSocket(`ws://localhost:3001/ws?token=${token}`);

      websocket.onopen = () => {
        setWsStatus('Connected');
        console.log('WebSocket connected');
      };

      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.stage && data.log) {
            // This is a training progress update or AI task update
            if (data.status === 'completed') {
              const aiResponse = { type: 'ai' as const, content: data.data || data.log };
              addChatMessage(aiResponse);
              setLoading(false);
            } else if (data.status === 'error' || data.status === 'timeout') {
              const errorMessage = { type: 'error' as const, content: data.data || data.log };
              addChatMessage(errorMessage);
              setLoading(false);
            } else {
              // Processing update
              const processingMessage = { type: 'system' as const, content: data.log };
              addChatMessage(processingMessage);
            }
          } else {
            // This is a chat message
            const aiResponse = { type: 'ai' as const, content: data.message || data };
            addChatMessage(aiResponse);
          }
        } catch (e) {
          console.error('Error parsing WebSocket message:', e);
        }
      };

      websocket.onclose = () => {
        setWsStatus('Disconnected');
        console.log('WebSocket disconnected');
      };

      websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        setWsStatus('Error');
      };

      setWs(websocket);
    }

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, []);

  const sendToAI = async () => {
    if (!input.trim()) return;

    const userMessage = { type: 'user' as const, content: input };
    addChatMessage(userMessage); // Add to store
    setLoading(true);
    setError(null);
    setInput('');

    try {
      // For coordinator role, use the multi-agent system
      if (selectedRole === 'coordinator') {
        // Async flow: enqueue and wait via WS/polling
        const resp = await apiService.submitQueryAsync(input);
        const taskId = resp?.task_id;
        if (taskId) {
          const processingMessage = { type: 'system' as const, content: `Запрос поставлен в очередь (Task ID: ${taskId}). Идёт обработка...` };
          addChatMessage(processingMessage);
          // Poll as fallback in case WS isn’t available
          const start = Date.now();
          const poll = async () => {
            try {
              const r = await apiService.getAsyncResult(taskId);
              if (r?.status === 'completed' && r?.result) {
                const final = r.result;
                const text = final.final_response || JSON.stringify(final, null, 2);
                addChatMessage({ type: 'ai', content: text });
                setLoading(false);
                return true;
              }
              if (r?.status === 'error') {
                addChatMessage({ type: 'error', content: r?.error || 'Ошибка выполнения задачи' });
                setLoading(false);
                return true;
              }
              if (Date.now() - start > 15 * 60 * 1000) { // 15 min timeout
                addChatMessage({ type: 'error', content: 'Таймаут ожидания результата' });
                setLoading(false);
                return true;
              }
            } catch (e) {}
            return false;
          };
          const interval = setInterval(async () => {
            const done = await poll();
            if (done) clearInterval(interval);
          }, 3000);
        } else {
          addChatMessage({ type: 'error', content: 'Не удалось поставить задачу в очередь' });
          setLoading(false);
        }
      } else {
        // For other roles, use the direct AI endpoint with proper role context
        const selectedRoleInfo = roleOptions.find(role => role.value === selectedRole);
        const roleContext = selectedRoleInfo ? `Выступая в роли ${selectedRoleInfo.label}: ` : '';
        const enhancedPrompt = `${roleContext}${input}`;
        
        // Add thinking mode instruction if disabled
        const finalPrompt = thinkingMode 
          ? enhancedPrompt 
          : `${enhancedPrompt}\n\nОтветь сразу, без промежуточных рассуждений. Не показывай цепочку размышлений.`;
        
        const response = await apiService.callAI({ 
          prompt: finalPrompt,
          model: selectedRole === 'coordinator' || selectedRole === 'project_manager' ? 
            'deepseek/deepseek-r1-0528-qwen3-8b' : 
            selectedRole === 'chief_engineer' || selectedRole === 'construction_safety' ? 
            'qwen/qwen2.5-vl-7b' : 
            'mistralai/mistral-nemo-instruct-2407'
        });
        
        // Handle the new asynchronous response format
        if (response.status === 'processing') {
          const processingMessage = { 
            type: 'system' as const, 
            content: `AI request started (Task ID: ${response.task_id}). Please wait while I process your request.` 
          };
          addChatMessage(processingMessage); // Add to store
          
          // The actual response will come via WebSocket, so we don't add anything here
          // Just keep the loading state until we get the WebSocket update
        } else {
          // Handle direct response (for backward compatibility)
          const aiResponse = { type: 'ai' as const, content: response.response || '' };
          addChatMessage(aiResponse); // Add to store
          setLoading(false);
        }
      }
    } catch (err: any) {
      console.error('AI error:', err);
      setError(err.response?.data?.error || 'Не удалось получить ответ от AI');
      // Add error to history for visibility
      const errorMessage = { type: 'error' as const, content: err.response?.data?.error || 'Не удалось получить ответ от AI' };
      addChatMessage(errorMessage); // Add to store
      setLoading(false);
    }
  };

  const handleFileUpload = async (file: File) => {
    try {
      // Pass the file directly to the API service method
      const response = await apiService.uploadFile(file);
      
      // Add file info to history
      const fileMessage = { 
        type: 'user' as const, 
        content: `Загружен файл: ${file.name}`, 
        fileId: response.filename 
      };
      addChatMessage(fileMessage); // Add to store
      
      message.success('Файл успешно загружен');
    } catch (err: any) {
      console.error('File upload error:', err);
      setError(err.response?.data?.error || 'Не удалось загрузить файл');
      message.error('Ошибка загрузки файла');
    }
  };

  const handleFileDownload = async (fileId: string) => {
    try {
      // In a real implementation, we would download the file
      // For now, we'll just show a message
      message.info(`Файл ${fileId} будет скачан`);
      
      // Add download info to history
      const downloadMessage = { 
        type: 'system' as const, 
        content: `Скачивание файла: ${fileId}` 
      };
      addChatMessage(downloadMessage); // Add to store
    } catch (err: any) {
      console.error('File download error:', err);
      setError(err.response?.data?.error || 'Не удалось скачать файл');
      message.error('Ошибка скачивания файла');
    }
  };

  const showModal = (fileId: string) => {
    setSelectedFileId(fileId);
    setIsModalVisible(true);
  };

  const handleModalOk = () => {
    handleFileDownload(selectedFileId);
    setIsModalVisible(false);
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
  };

  return (
    <div>
      <Title level={2}>AI Shell</Title>
      <Text>Система Bldr Empire v2 с многоагентной архитектурой. Выберите роль для взаимодействия:</Text>
      
      <Card style={{ 
        marginBottom: '20px', 
        backgroundColor: theme === 'dark' ? '#1f1f1f' : '#f5f5f5',
        borderColor: theme === 'dark' ? '#444' : '#ddd'
      }} size="small">
        <div style={{ marginBottom: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Text strong>Выберите роль:</Text>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <Text style={{ marginRight: '10px' }}>Режим размышлений:</Text>
            <Switch 
              checked={thinkingMode} 
              onChange={setThinkingMode} 
              checkedChildren="ВКЛ" 
              unCheckedChildren="ВЫКЛ" 
            />
          </div>
        </div>
        <Select
          value={selectedRole}
          onChange={setSelectedRole}
          style={{ width: '100%', marginBottom: '10px' }}
          options={roleOptions.map(role => ({ value: role.value, label: role.label }))}
        />
        <Text type="secondary">
          {roleOptions.find(role => role.value === selectedRole)?.description}
        </Text>
        <div style={{ marginTop: '10px' }}>
          <Text type="secondary">WebSocket Status: <span style={{ color: wsStatus === 'Connected' ? 'green' : 'red' }}>{wsStatus}</span></Text>
        </div>
      </Card>
      
      {error && <div style={{ color: 'red' }}>Ошибка: {error}</div>}
      <div style={{ 
        height: '400px', 
        overflowY: 'scroll', 
        border: '1px solid #ccc', 
        padding: '10px', 
        marginBottom: '10px', 
        backgroundColor: theme === 'dark' ? '#1f1f1f' : '#f5f5f5',
        color: theme === 'dark' ? '#ffffff' : '#000000'
      }}>
        {chatHistory.map((msg, idx) => (
          <div key={idx} style={{ 
            marginBottom: '10px', 
            padding: '5px', 
            borderRadius: '4px', 
            backgroundColor: msg.type === 'user' ? 
              (theme === 'dark' ? '#177ddc' : '#e6f7ff') : 
              msg.type === 'error' ? 
                (theme === 'dark' ? '#a61d24' : '#fff2f0') : 
                msg.type === 'system' ?
                  (theme === 'dark' ? '#d8bd14' : '#fffbe6') :
                  (theme === 'dark' ? '#3f6600' : '#f6ffed'),
            color: theme === 'dark' ? '#ffffff' : '#000000'
          }}>
            <strong>
              {msg.type === 'user' ? 'Вы:' : 
               msg.type === 'error' ? 'Ошибка:' : 
               msg.type === 'system' ? 'Система:' : 'AI:'}
            </strong> {msg.content}
            {msg.fileId && (
              <Button 
                type="link" 
                icon={<DownloadOutlined />} 
                onClick={() => showModal(msg.fileId || '')}
                style={{ padding: '0 5px' }}
              >
                Скачать
              </Button>
            )}
          </div>
        ))}
        {loading && <div>AI думает...</div>}
      </div>
      
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '10px' }}>
        <Input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Введите промпт для AI..."
          onKeyPress={(e) => e.key === 'Enter' && sendToAI()}
          disabled={loading}
          style={{ flex: 1, marginRight: '10px' }}
        />
        <Upload 
          beforeUpload={(file) => {
            handleFileUpload(file);
            return false; // Prevent default upload behavior
          }}
          showUploadList={false}
        >
          <Button icon={<UploadOutlined />}>Загрузить файл</Button>
        </Upload>
        <Button 
          onClick={sendToAI} 
          disabled={loading || !input.trim()}
          style={{ marginLeft: '10px' }}
        >
          {loading ? 'Отправка...' : 'Отправить'}
        </Button>
        <Button 
          onClick={() => {
            clearChatHistory();
            setError(null);
          }} 
          icon={<ClearOutlined />}
          style={{ marginLeft: '10px' }}
        >
          Очистить
        </Button>
      </div>

      <Modal
        title="Скачать файл"
        visible={isModalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
        okText="Скачать"
        cancelText="Отмена"
      >
        <p>Вы уверены, что хотите скачать файл {selectedFileId}?</p>
      </Modal>
    </div>
  );
};

export default AIShell;