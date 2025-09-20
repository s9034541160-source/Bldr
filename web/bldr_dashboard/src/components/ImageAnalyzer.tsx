/**
 * ImageAnalyzer - ПОЛНОЦЕННЫЙ анализатор изображений для TypeScript/Ant Design
 * ENTERPRISE READY компонент для анализа чертежей, планов и фотографий
 */

import React, { useState, useCallback } from 'react';
import { 
  Card, 
  Upload, 
  Button, 
  Select, 
  Slider, 
  Switch,
  Progress, 
  Result, 
  Descriptions, 
  Table, 
  Image,
  Tabs,
  Tag,
  message,
  Row,
  Col,
  Divider,
  Space,
  Tooltip,
  Badge
} from 'antd';
import { 
  PictureOutlined, 
  DeleteOutlined, 
  PlayCircleOutlined,
  DownloadOutlined,
  EyeOutlined,
  ZoomInOutlined,
  ScanOutlined,
  BgColorsOutlined
} from '@ant-design/icons';
import type { RcFile, UploadFile } from 'antd/es/upload/interface';

const { Option } = Select;
const { TabPane } = Tabs;

interface AnalysisParams {
  analysisType: string;
  detectObjects: boolean;
  extractDimensions: boolean;
  recognizeText: boolean;
  confidenceThreshold: number;
  enhanceQuality: boolean;
  imageQuality: string;
}

interface DetectedObject {
  type: string;
  confidence: number;
  bbox: [number, number, number, number];
  description: string;
}

interface ExtractedDimension {
  value: string;
  unit: string;
  description: string;
  confidence: number;
}

interface AnalysisResult {
  summary: {
    images: Array<{
      filename: string;
      objects_detected: DetectedObject[];
      dimensions_found: ExtractedDimension[];
      text_recognized: string;
      quality_score: number;
      resolution: string;
    }>;
  };
  technical_analysis: {
    description: string;
    recommendations: string[];
    detected_elements: string[];
    scale_detected: boolean;
    drawing_type: string;
  };
}

const ImageAnalyzer: React.FC = () => {
  const [images, setImages] = useState<UploadFile[]>([]);
  const [analysisParams, setAnalysisParams] = useState<AnalysisParams>({
    analysisType: 'comprehensive',
    detectObjects: true,
    extractDimensions: true, 
    recognizeText: true,
    confidenceThreshold: 0.7,
    enhanceQuality: true,
    imageQuality: 'high'
  });
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [previewVisible, setPreviewVisible] = useState(false);
  const [previewImage, setPreviewImage] = useState<string>('');

  // Обработка загрузки изображений
  const handleImageChange = useCallback((info: any) => {
    const { fileList } = info;
    
    // Фильтруем только поддерживаемые типы изображений
    const supportedImages = fileList.filter((file: UploadFile) => {
      const isSupported = [
        'image/jpeg',
        'image/jpg', 
        'image/png',
        'image/tiff',
        'image/bmp',
        'application/pdf'
      ].includes(file.type || '');
      
      if (!isSupported && file.status !== 'removed') {
        message.error(`Файл ${file.name} не поддерживается для анализа изображений`);
      }
      
      // Проверка размера файла (100MB лимит)
      if (file.size && file.size > 100 * 1024 * 1024) {
        message.error(`Изображение ${file.name} слишком большое (максимум 100MB)`);
        return false;
      }
      
      return isSupported;
    });
    
    setImages(supportedImages);
  }, []);

  // Кастомная функция загрузки
  const customRequest = ({ onSuccess }: any) => {
    setTimeout(() => {
      onSuccess({});
    }, 0);
  };

  // Предпросмотр изображения
  const handlePreview = async (file: UploadFile) => {
    if (!file.url && !file.preview) {
      file.preview = await getBase64(file.originFileObj as RcFile);
    }
    setPreviewImage(file.url || (file.preview as string));
    setPreviewVisible(true);
  };

  // Конвертация в base64 для предпросмотра
  const getBase64 = (file: RcFile): Promise<string> =>
    new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = (error) => reject(error);
    });

  // Запуск анализа изображений
  const startAnalysis = async () => {
    if (images.length === 0) {
      message.warning('Пожалуйста, загрузите изображения для анализа');
      return;
    }

    setIsAnalyzing(true);
    setAnalysisProgress(0);
    setAnalysisResult(null);
    setAnalysisError(null);

    try {
      const formData = new FormData();
      
      // Добавляем изображения
      images.forEach((image) => {
        if (image.originFileObj) {
          formData.append('images', image.originFileObj as RcFile);
        }
      });
      
      // Добавляем параметры
      formData.append('params', JSON.stringify(analysisParams));

      const response = await fetch('/api/tools/analyze/images', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`HTTP ошибка: ${response.status}`);
      }

      const result = await response.json();
      
      if (result.success) {
        setCurrentJobId(result.job_id);
        message.success('Анализ изображений запущен');
        
        // Отслеживаем прогресс
        const checkProgress = async () => {
          try {
            const statusResponse = await fetch(`/api/tools/jobs/${result.job_id}/status`);
            if (statusResponse.ok) {
              const statusData = await statusResponse.json();
              
              setAnalysisProgress(statusData.progress || 0);
              
              if (statusData.status === 'completed') {
                setAnalysisResult(statusData.result);
                setIsAnalyzing(false);
                message.success('Анализ изображений завершен!');
              } else if (statusData.status === 'failed') {
                setAnalysisError(statusData.error || 'Неизвестная ошибка');
                setIsAnalyzing(false);
                message.error('Ошибка анализа изображений');
              } else {
                setTimeout(checkProgress, 2000);
              }
            }
          } catch (error) {
            console.error('Ошибка проверки статуса:', error);
            setTimeout(checkProgress, 5000);
          }
        };
        
        checkProgress();
        
      } else {
        throw new Error(result.message || 'Неизвестная ошибка');
      }

    } catch (error) {
      console.error('Ошибка запуска анализа:', error);
      setAnalysisError(error instanceof Error ? error.message : 'Неизвестная ошибка');
      setIsAnalyzing(false);
      message.error('Ошибка при запуске анализа изображений');
    }
  };

  // Скачивание результата
  const downloadResult = async () => {
    if (!currentJobId) return;
    
    try {
      const response = await fetch(`/api/tools/jobs/${currentJobId}/download`);
      const blob = await response.blob();
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `image_analysis_result.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      message.success('Результат анализа загружен');
    } catch (error) {
      message.error('Ошибка при скачивании результата');
    }
  };

  // Колонки для таблицы объектов
  const objectColumns = [
    {
      title: 'Тип объекта',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => {
        const colors: Record<string, string> = {
          'wall': 'blue',
          'door': 'green', 
          'window': 'orange',
          'dimension': 'purple',
          'text': 'red'
        };
        return <Tag color={colors[type] || 'default'}>{type}</Tag>;
      }
    },
    {
      title: 'Уверенность',
      dataIndex: 'confidence',
      key: 'confidence',
      width: 120,
      render: (confidence: number) => (
        <Badge 
          status={confidence > 0.8 ? 'success' : confidence > 0.6 ? 'warning' : 'error'}
          text={`${Math.round(confidence * 100)}%`}
        />
      )
    },
    {
      title: 'Описание',
      dataIndex: 'description',
      key: 'description',
    }
  ];

  // Колонки для таблицы размеров
  const dimensionColumns = [
    {
      title: 'Значение',
      dataIndex: 'value',
      key: 'value',
      width: 100,
      render: (value: string) => <span style={{ fontWeight: 'bold' }}>{value}</span>
    },
    {
      title: 'Единица',
      dataIndex: 'unit',
      key: 'unit',
      width: 80
    },
    {
      title: 'Описание',
      dataIndex: 'description',
      key: 'description'
    },
    {
      title: 'Точность',
      dataIndex: 'confidence',
      key: 'confidence',
      width: 100,
      render: (confidence: number) => `${Math.round(confidence * 100)}%`
    }
  ];

  return (
    <div>
      <Row gutter={[24, 24]}>
        {/* Панель загрузки изображений */}
        <Col span={12}>
          <Card title="🖼️ Загрузка изображений" size="small">
            <Upload.Dragger
              multiple
              accept=".jpg,.jpeg,.png,.tiff,.bmp,.pdf"
              fileList={images}
              onChange={handleImageChange}
              customRequest={customRequest}
              onPreview={handlePreview}
              showUploadList={{
                showRemoveIcon: true,
                showPreviewIcon: true
              }}
            >
              <p className="ant-upload-drag-icon">
                <PictureOutlined style={{ fontSize: 48, color: '#1890ff' }} />
              </p>
              <p className="ant-upload-text">
                Нажмите или перетащите изображения для загрузки
              </p>
              <p className="ant-upload-hint">
                Поддерживаются: JPG, PNG, TIFF, BMP, PDF (до 100MB)
              </p>
            </Upload.Dragger>
            
            {/* Предпросмотр */}
            <Image
              width={200}
              style={{ display: 'none' }}
              src={previewImage}
              preview={{
                visible: previewVisible,
                src: previewImage,
                onVisibleChange: (value) => {
                  setPreviewVisible(value);
                }
              }}
            />
          </Card>
        </Col>

        {/* Панель настроек анализа */}
        <Col span={12}>
          <Card title="⚙️ Параметры анализа изображений" size="small">
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
                  <ScanOutlined /> Тип анализа:
                </label>
                <Select
                  style={{ width: '100%' }}
                  value={analysisParams.analysisType}
                  onChange={(value) => setAnalysisParams(prev => ({ ...prev, analysisType: value }))}
                >
                  <Option value="comprehensive">Комплексный анализ</Option>
                  <Option value="architectural">Архитектурный анализ</Option>
                  <Option value="technical">Технический анализ</Option>
                  <Option value="ocr_only">Только распознавание текста</Option>
                  <Option value="objects_only">Только объекты</Option>
                </Select>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
                  <BgColorsOutlined /> Качество обработки:
                </label>
                <Select
                  style={{ width: '100%' }}
                  value={analysisParams.imageQuality}
                  onChange={(value) => setAnalysisParams(prev => ({ ...prev, imageQuality: value }))}
                >
                  <Option value="high">Высокое качество (медленно)</Option>
                  <Option value="medium">Среднее качество (быстро)</Option>
                  <Option value="low">Низкое качество (очень быстро)</Option>
                </Select>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
                  Порог уверенности: {Math.round(analysisParams.confidenceThreshold * 100)}%
                </label>
                <Slider
                  min={0.3}
                  max={0.95}
                  step={0.05}
                  value={analysisParams.confidenceThreshold}
                  onChange={(value) => setAnalysisParams(prev => ({ ...prev, confidenceThreshold: value }))}
                  marks={{
                    0.3: '30%',
                    0.7: '70%', 
                    0.95: '95%'
                  }}
                />
              </div>

              <Divider />

              <Space direction="vertical" size="small">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>Распознавание объектов</span>
                  <Switch
                    checked={analysisParams.detectObjects}
                    onChange={(checked) => setAnalysisParams(prev => ({ ...prev, detectObjects: checked }))}
                  />
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>Извлечение размеров</span>
                  <Switch
                    checked={analysisParams.extractDimensions}
                    onChange={(checked) => setAnalysisParams(prev => ({ ...prev, extractDimensions: checked }))}
                  />
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>Распознавание текста (OCR)</span>
                  <Switch
                    checked={analysisParams.recognizeText}
                    onChange={(checked) => setAnalysisParams(prev => ({ ...prev, recognizeText: checked }))}
                  />
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>Улучшение качества</span>
                  <Switch
                    checked={analysisParams.enhanceQuality}
                    onChange={(checked) => setAnalysisParams(prev => ({ ...prev, enhanceQuality: checked }))}
                  />
                </div>
              </Space>
            </Space>
          </Card>
        </Col>
      </Row>

      {/* Кнопка запуска анализа */}
      <div style={{ textAlign: 'center', margin: '24px 0' }}>
        <Button
          type="primary"
          size="large"
          icon={<PlayCircleOutlined />}
          onClick={startAnalysis}
          disabled={images.length === 0 || isAnalyzing}
          loading={isAnalyzing}
        >
          {isAnalyzing ? 'Анализируем изображения...' : 'Начать анализ изображений'}
        </Button>
        {images.length > 0 && (
          <div style={{ marginTop: '8px', color: '#666' }}>
            Будет проанализировано {images.length} изображение(й)
          </div>
        )}
      </div>

      {/* Прогресс анализа */}
      {isAnalyzing && (
        <Card style={{ marginBottom: '24px' }}>
          <div style={{ textAlign: 'center' }}>
            <Progress
              type="circle"
              percent={analysisProgress}
              status="active"
              format={percent => `${percent}%`}
            />
            <p style={{ marginTop: '16px', color: '#666' }}>
              Обрабатываем {images.length} изображение(й)... AI модель анализирует объекты и текст
            </p>
          </div>
        </Card>
      )}

      {/* Результаты анализа */}
      {analysisResult && (
        <Card 
          title="✅ Результаты анализа изображений"
          extra={
            <Button 
              type="primary" 
              icon={<DownloadOutlined />}
              onClick={downloadResult}
            >
              Скачать отчет
            </Button>
          }
        >
          {/* Общая информация */}
          <Descriptions column={3} bordered style={{ marginBottom: '24px' }}>
            <Descriptions.Item label="Обработано изображений">
              {analysisResult.summary.images.length}
            </Descriptions.Item>
            <Descriptions.Item label="Тип чертежа">
              <Tag color="blue">{analysisResult.technical_analysis.drawing_type}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Масштаб обнаружен">
              <Badge 
                status={analysisResult.technical_analysis.scale_detected ? 'success' : 'warning'}
                text={analysisResult.technical_analysis.scale_detected ? 'Да' : 'Нет'}
              />
            </Descriptions.Item>
          </Descriptions>

          {/* Табы с результатами по изображениям */}
          <Tabs defaultActiveKey="0">
            {analysisResult.summary.images.map((imageResult, index) => (
              <TabPane 
                tab={`${imageResult.filename} (${imageResult.objects_detected.length} объектов)`} 
                key={index.toString()}
              >
                <Row gutter={[16, 16]}>
                  <Col span={12}>
                    {/* Информация об изображении */}
                    <Card title="📊 Общая информация" size="small" style={{ marginBottom: '16px' }}>
                      <Descriptions column={2} size="small">
                        <Descriptions.Item label="Качество">
                          <Badge 
                            status={imageResult.quality_score > 0.8 ? 'success' : 'warning'}
                            text={`${Math.round(imageResult.quality_score * 100)}%`}
                          />
                        </Descriptions.Item>
                        <Descriptions.Item label="Разрешение">
                          {imageResult.resolution}
                        </Descriptions.Item>
                      </Descriptions>
                      
                      {imageResult.text_recognized && (
                        <div>
                          <Divider orientation="left" orientationMargin="0">Распознанный текст</Divider>
                          <div style={{ 
                            background: '#f6f6f6', 
                            padding: '12px', 
                            borderRadius: '6px',
                            fontFamily: 'monospace',
                            fontSize: '13px'
                          }}>
                            {imageResult.text_recognized}
                          </div>
                        </div>
                      )}
                    </Card>
                    
                    {/* Рекомендации */}
                    <Card title="💡 Рекомендации" size="small">
                      <ul style={{ margin: 0, paddingLeft: '20px' }}>
                        {analysisResult.technical_analysis.recommendations.map((rec, i) => (
                          <li key={i} style={{ marginBottom: '4px' }}>{rec}</li>
                        ))}
                      </ul>
                    </Card>
                  </Col>
                  
                  <Col span={12}>
                    {/* Обнаруженные объекты */}
                    {imageResult.objects_detected.length > 0 && (
                      <Card title="🎯 Обнаруженные объекты" size="small" style={{ marginBottom: '16px' }}>
                        <Table
                          columns={objectColumns}
                          dataSource={imageResult.objects_detected}
                          size="small"
                          pagination={false}
                          scroll={{ y: 200 }}
                        />
                      </Card>
                    )}
                    
                    {/* Найденные размеры */}
                    {imageResult.dimensions_found.length > 0 && (
                      <Card title="📏 Извлеченные размеры" size="small">
                        <Table
                          columns={dimensionColumns}
                          dataSource={imageResult.dimensions_found}
                          size="small"
                          pagination={false}
                          scroll={{ y: 200 }}
                        />
                      </Card>
                    )}
                  </Col>
                </Row>
              </TabPane>
            ))}
          </Tabs>
          
          {/* Техническое описание */}
          <Card title="📋 Техническое заключение" style={{ marginTop: '16px' }}>
            <p>{analysisResult.technical_analysis.description}</p>
            
            <Divider orientation="left">Обнаруженные элементы</Divider>
            <Space wrap>
              {analysisResult.technical_analysis.detected_elements.map((element, index) => (
                <Tag key={index} color="processing">{element}</Tag>
              ))}
            </Space>
          </Card>
        </Card>
      )}

      {/* Ошибки */}
      {analysisError && (
        <Result
          status="error"
          title="Ошибка анализа изображений"
          subTitle={analysisError}
          extra={
            <Button type="primary" onClick={() => setAnalysisError(null)}>
              Попробовать снова
            </Button>
          }
        />
      )}
    </div>
  );
};

export default ImageAnalyzer;
