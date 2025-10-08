import React, { useState, useEffect } from 'react';
import { Card, Input, Button, Table, message, Row, Col, Statistic, Upload, Modal, Progress, Timeline, Typography, Collapse, Alert } from 'antd';
import { UploadOutlined, FolderOpenOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { apiService } from '../services/api';
import type { ColumnsType } from 'antd/es/table';

// Add type definitions for the Directory Picker API
declare global {
  interface Window {
    showDirectoryPicker?: () => Promise<any>;
  }
}

const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;

const FileManager: React.FC = () => {
  const [path, setPath] = useState('I:\\docs\\база');
  const [scanResults, setScanResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  // New states for folder selection and training
  const [folderList, setFolderList] = useState<any[]>([]);
  const [isTrainModalVisible, setIsTrainModalVisible] = useState(false);
  const [trainingProgress, setTrainingProgress] = useState(0);
  const [trainingStatus, setTrainingStatus] = useState('Подготовка...');
  const [trainingLogs, setTrainingLogs] = useState<string[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [wsStatus, setWsStatus] = useState('Disconnected');

  // WebSocket connection for training updates
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      const websocket = new WebSocket(`ws://localhost:8000/ws?token=${token}`);
      
      websocket.onopen = () => {
        setWsStatus('Connected');
        console.log('WebSocket connected for file manager');
      };
      
      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.stage && data.log) {
            // This is a training progress update
            setTrainingStatus(data.log);
            setTrainingLogs(prev => [...prev, data.log]);
            
            // Update progress if available
            if (data.progress !== undefined) {
              setTrainingProgress(data.progress);
            }
            
            // If training is complete, close the modal after a delay
            if (data.status === 'completed') {
              setTimeout(() => {
                setIsTrainModalVisible(false);
                message.success('Обучение завершено успешно!');
              }, 2000);
            } else if (data.status === 'error') {
              message.error(`Ошибка обучения: ${data.log}`);
            }
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

  const scanFiles = async () => {
    if (!path.trim()) {
      message.warning('Пожалуйста, введите путь для сканирования');
      return;
    }
    
    try {
      setLoading(true);
      const response = await apiService.scanFiles({ path });
      
      if (response) {
        setScanResults(response);
        message.success(`Сканирование завершено. Найдено: ${response.scanned}, скопировано: ${response.copied}`);
      } else {
        message.warning('Получен пустой ответ от сервера');
      }
      
    } catch (error: any) {
      console.error('Ошибка сканирования файлов:', error);
      message.error(`Не удалось выполнить сканирование файлов: ${error.response?.data?.error || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // New function to handle folder selection
  const handleFolderSelect = async (folderPath: string) => {
    setSelectedFolder(folderPath);
    try {
      // Scan the selected folder to show preview
      const response = await apiService.scanFiles({ path: folderPath });
      if (response) {
        setScanResults(response);
        message.success(`Папка выбрана. Найдено: ${response.scanned} файлов`);
      }
    } catch (error: any) {
      console.error('Ошибка сканирования папки:', error);
      message.error(`Не удалось просканировать выбранную папку: ${error.response?.data?.error || error.message}`);
    }
  };

  // New function to start training on selected folder
  const startTraining = async () => {
    // Use selected folder or default paths
    const trainingPath = selectedFolder || path || 'I:/docs/downloaded';
    
    if (!trainingPath) {
      message.warning('Пожалуйста, сначала укажите папку для обучения');
      return;
    }
    
    setIsTrainModalVisible(true);
    setTrainingProgress(0);
    setTrainingStatus('Начало обучения...');
    setTrainingLogs(['Начало процесса обучения...']);
    
    try {
      // Call the train endpoint with custom_dir parameter
      await apiService.train({ custom_dir: trainingPath });
      message.success('Обучение запущено в фоновом режиме');
      setTrainingStatus('Обучение запущено в фоновом режиме');
      setTrainingLogs(prev => [...prev, 'Обучение запущено в фоновом режиме. Следите за прогрессом...']);
    } catch (error: any) {
      console.error('Ошибка запуска обучения:', error);
      message.error(`Не удалось запустить обучение: ${error.response?.data?.error || error.message}`);
      setTrainingStatus('Ошибка запуска обучения');
      setTrainingLogs(prev => [...prev, `Ошибка: ${error.response?.data?.error || error.message}`]);
    }
  };

  // Function to handle manual folder selection
  const handleManualFolderSelect = () => {
    const folderPath = prompt('Введите путь к папке для обучения:');
    if (folderPath) {
      handleFolderSelect(folderPath);
    }
  };

  // Function to handle folder picker dialog using modern web API
  const handleFolderPicker = async () => {
    // Check if the browser supports showDirectoryPicker
    if (window.showDirectoryPicker) {
      try {
        // Use the modern directory picker API
        const dirHandle = await window.showDirectoryPicker();
        const folderPath = dirHandle.name;
        // For now, we'll just use the directory name as the path
        // In a real implementation, we might want to handle the directory handle differently
        handleFolderSelect(folderPath);
      } catch (error) {
        // User cancelled the dialog or there was an error
        console.log('Directory picker was cancelled or failed:', error);
        // Fall back to manual input
        handleManualFolderSelect();
      }
    } else {
      // Fall back to manual input for older browsers
      handleManualFolderSelect();
    }
  };

  // Function to handle folder picker for training
  const handleTrainingFolderPicker = async () => {
    // Check if the browser supports showDirectoryPicker
    if (window.showDirectoryPicker) {
      try {
        // Use the modern directory picker API
        const dirHandle = await window.showDirectoryPicker();
        const folderPath = dirHandle.name;
        // For now, we'll just use the directory name as the path
        // In a real implementation, we might want to handle the directory handle differently
        handleFolderSelect(folderPath);
      } catch (error) {
        // User cancelled the dialog or there was an error
        console.log('Directory picker was cancelled or failed:', error);
        // Fall back to manual input
        handleManualFolderSelect();
      }
    } else {
      // Fall back to manual input for older browsers
      handleManualFolderSelect();
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card title="Менеджер файлов" bordered={false}>
        <Alert
          message="О компоненте"
          description="Менеджер файлов позволяет сканировать документы для добавления в базу знаний системы и запускать обучение RAG на выбранных папках."
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />
        
        <Collapse defaultActiveKey={['1']} style={{ marginBottom: 24 }}>
          <Panel header="Как использовать Менеджер файлов" key="1">
            <Paragraph>
              <ul>
                <li><Text strong>Сканирование файлов</Text>: Укажите путь к папке с документами и нажмите "Сканировать файлы" для поиска и копирования документов в систему</li>
                <li><Text strong>Выбор папки для обучения</Text>: Выберите папку с документами, на которых нужно обучить систему RAG</li>
                <li><Text strong>Обучение RAG</Text>: Запустите процесс обучения на выбранной папке для индексации документов в векторной базе</li>
              </ul>
            </Paragraph>
          </Panel>
        </Collapse>
        
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <Card title="Сканирование файлов" size="small">
              <Text type="secondary">
                Сканирует указанную папку и копирует поддерживаемые файлы в систему для дальнейшей обработки.
              </Text>
              <Input
                value={path}
                onChange={(e) => setPath(e.target.value)}
                placeholder="Введите путь для сканирования..."
                disabled={loading}
                style={{ marginTop: 12, marginBottom: 16 }}
              />
              <Button 
                icon={<FolderOpenOutlined />}
                onClick={handleFolderPicker}
                style={{ marginRight: 12 }}
              >
                Выбрать папку
              </Button>
              <Button 
                type="primary" 
                onClick={scanFiles} 
                loading={loading}
              >
                Сканировать файлы
              </Button>
              
              {/* New folder selection UI */}
              <div style={{ marginTop: 24 }}>
                <Card title="Обучение RAG" size="small">
                  <Text type="secondary">
                    Выберите папку с документами для обучения системы RAG (Retrieval-Augmented Generation).
                  </Text>
                  
                  <div style={{ marginTop: 16 }}>
                    <Button 
                      icon={<FolderOpenOutlined />} 
                      onClick={handleTrainingFolderPicker}
                    >
                      Выбрать папку для обучения
                    </Button>
                    
                    {selectedFolder && (
                      <div style={{ marginTop: 16, padding: 12, backgroundColor: '#f0f2f5', borderRadius: 4 }}>
                        <Text strong>Выбранная папка:</Text>
                        <div style={{ marginTop: 4, padding: 8, backgroundColor: 'white', borderRadius: 4 }}>
                          {selectedFolder}
                        </div>
                        
                        <Button 
                          type="primary" 
                          onClick={startTraining}
                          style={{ marginTop: 12 }}
                        >
                          Обучить на выбранной папке
                        </Button>
                        
                        <div style={{ marginTop: 12 }}>
                          <Text type="secondary">
                            После запуска обучения вы можете отслеживать прогресс в модальном окне.
                            Обучение происходит в фоновом режиме.
                          </Text>
                        </div>
                      </div>
                    )}
                  </div>
                </Card>
              </div>
            </Card>
          </Col>
          
          {scanResults && (
            <Col span={24}>
              <Card title="Результаты сканирования" size="small">
                <Row gutter={16}>
                  <Col span={8}>
                    <Statistic title="Всего файлов" value={scanResults.scanned || 0} />
                  </Col>
                  <Col span={8}>
                    <Statistic title="Скопировано" value={scanResults.copied || 0} />
                  </Col>
                  <Col span={8}>
                    <Statistic title="Путь" value={scanResults.path || 'Не указан'} />
                  </Col>
                </Row>
                
                <div style={{ marginTop: 16 }}>
                  <Text type="secondary">
                    Поддерживаемые форматы файлов: PDF, DOCX, XLSX, JPG, PNG, TIFF, DWG
                  </Text>
                </div>
              </Card>
            </Col>
          )}
        </Row>
      </Card>
      
      {/* Training Progress Modal */}
      <Modal
        title="Прогресс обучения RAG"
        visible={isTrainModalVisible}
        onCancel={() => setIsTrainModalVisible(false)}
        footer={null}
        width={600}
      >
        <div>
          <Progress percent={trainingProgress} status="active" />
          <p style={{ marginTop: 16 }}><strong>Статус:</strong> {trainingStatus}</p>
          
          <div style={{ marginTop: 16 }}>
            <Text type="secondary">WebSocket Status: <span style={{ color: wsStatus === 'Connected' ? 'green' : 'red' }}>{wsStatus}</span></Text>
          </div>
          
          <div style={{ marginTop: 24 }}>
            <h4>Логи обучения:</h4>
            <div style={{ maxHeight: 200, overflowY: 'auto', padding: 8, backgroundColor: '#f5f5f5', borderRadius: 4 }}>
              {trainingLogs.map((log, index) => (
                <div key={index} style={{ marginBottom: 4 }}>
                  <Text type="secondary">[{new Date().toLocaleTimeString()}]</Text> {log}
                </div>
              ))}
            </div>
          </div>
          
          <div style={{ marginTop: 24, textAlign: 'right' }}>
            <Button onClick={() => setIsTrainModalVisible(false)}>Закрыть</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default FileManager;