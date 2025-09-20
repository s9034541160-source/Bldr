/**
 * EstimateAnalyzer - анализатор смет для TypeScript/Ant Design
 */

import React, { useState, useCallback } from 'react';
import { 
  Card, 
  Upload, 
  Button, 
  Select, 
  Checkbox, 
  Progress, 
  Result, 
  Descriptions, 
  Table, 
  message,
  Row,
  Col,
  Divider
} from 'antd';
import { 
  UploadOutlined, 
  FileExcelOutlined, 
  DeleteOutlined, 
  PlayCircleOutlined,
  DownloadOutlined
} from '@ant-design/icons';
import type { RcFile, UploadFile } from 'antd/es/upload/interface';

const { Option } = Select;

interface AnalysisParams {
  analysisType: string;
  region: string;
  includeGESN: boolean;
  includeFER: boolean;
  includeRegionalCoeff: boolean;
}

interface AnalysisResult {
  summary: {
    total_cost: string;
    items_count: number;
    errors_count: number;
    warnings_count: number;
  };
  details: Array<{
    name: string;
    unit: string;
    quantity: number;
    price: number;
    total: number;
  }>;
  compliance_check: {
    gesn_compliance: string;
    regional_coefficients: string;
    price_year: string;
  };
}

const EstimateAnalyzer: React.FC = () => {
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [analysisParams, setAnalysisParams] = useState<AnalysisParams>({
    analysisType: 'full',
    region: 'moscow', 
    includeGESN: true,
    includeFER: false,
    includeRegionalCoeff: true
  });
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  // Обработка загрузки файлов
  const handleFileChange = useCallback((info: any) => {
    const { fileList } = info;
    
    // Фильтруем только поддерживаемые типы
    const supportedFiles = fileList.filter((file: UploadFile) => {
      const isSupported = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel',
        'application/pdf',
        'text/csv'
      ].includes(file.type || '');
      
      if (!isSupported && file.status !== 'removed') {
        message.error(`Файл ${file.name} не поддерживается`);
      }
      
      return isSupported;
    });
    
    setFiles(supportedFiles);
  }, []);

  // Кастомная функция загрузки (предотвращаем автоматическую загрузку)
  const customRequest = ({ onSuccess }: any) => {
    setTimeout(() => {
      onSuccess({});
    }, 0);
  };

  // Запуск анализа
  const startAnalysis = async () => {
    if (files.length === 0) {
      message.warning('Пожалуйста, загрузите файлы смет для анализа');
      return;
    }

    setIsAnalyzing(true);
    setAnalysisProgress(0);
    setAnalysisResult(null);
    setAnalysisError(null);

    try {
      const formData = new FormData();
      
      // Добавляем файлы
      files.forEach((file) => {
        if (file.originFileObj) {
          formData.append('files', file.originFileObj as RcFile);
        }
      });
      
      // Добавляем параметры
      formData.append('params', JSON.stringify(analysisParams));

      const response = await fetch('/api/tools/analyze/estimate', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`HTTP ошибка: ${response.status}`);
      }

      const result = await response.json();
      
      if (result.success) {
        setCurrentJobId(result.job_id);
        message.success('Анализ смет запущен');
        
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
                message.success('Анализ смет завершен!');
              } else if (statusData.status === 'failed') {
                setAnalysisError(statusData.error || 'Неизвестная ошибка');
                setIsAnalyzing(false);
                message.error('Ошибка анализа смет');
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
      message.error('Ошибка при запуске анализа смет');
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
      a.download = `estimate_analysis_result.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      message.success('Результат загружен');
    } catch (error) {
      message.error('Ошибка при скачивании результата');
    }
  };

  // Колонки для таблицы деталей
  const detailColumns = [
    {
      title: 'Наименование работ',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Ед. изм.',
      dataIndex: 'unit',
      key: 'unit',
      width: 100,
    },
    {
      title: 'Количество',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 120,
      render: (value: number) => value.toLocaleString('ru-RU'),
    },
    {
      title: 'Цена, руб',
      dataIndex: 'price',
      key: 'price',
      width: 150,
      render: (value: number) => value.toLocaleString('ru-RU'),
    },
    {
      title: 'Сумма, руб',
      dataIndex: 'total',
      key: 'total',
      width: 180,
      render: (value: number) => (
        <span style={{ fontWeight: 'bold' }}>
          {value.toLocaleString('ru-RU')}
        </span>
      ),
    },
  ];

  return (
    <div>
      <Row gutter={[24, 24]}>
        {/* Панель загрузки файлов */}
        <Col span={12}>
          <Card title="📁 Загрузка файлов смет" size="small">
            <Upload.Dragger
              multiple
              accept=".xlsx,.xls,.pdf,.csv"
              fileList={files}
              onChange={handleFileChange}
              customRequest={customRequest}
              showUploadList={{
                showRemoveIcon: true,
                showPreviewIcon: false,
              }}
            >
              <p className="ant-upload-drag-icon">
                <FileExcelOutlined style={{ fontSize: 48, color: '#52c41a' }} />
              </p>
              <p className="ant-upload-text">
                Нажмите или перетащите файлы смет для загрузки
              </p>
              <p className="ant-upload-hint">
                Поддерживаются: XLSX, XLS, PDF, CSV (до 50MB)
              </p>
            </Upload.Dragger>
          </Card>
        </Col>

        {/* Панель настроек */}
        <Col span={12}>
          <Card title="⚙️ Параметры анализа" size="small">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
                  Тип анализа:
                </label>
                <Select
                  style={{ width: '100%' }}
                  value={analysisParams.analysisType}
                  onChange={(value) => setAnalysisParams(prev => ({ ...prev, analysisType: value }))}
                >
                  <Option value="full">Полный анализ</Option>
                  <Option value="basic">Базовый анализ</Option>
                  <Option value="compliance">Проверка соответствия</Option>
                  <Option value="cost_only">Только стоимость</Option>
                </Select>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
                  Регион:
                </label>
                <Select
                  style={{ width: '100%' }}
                  value={analysisParams.region}
                  onChange={(value) => setAnalysisParams(prev => ({ ...prev, region: value }))}
                >
                  <Option value="moscow">Москва</Option>
                  <Option value="spb">Санкт-Петербург</Option>
                  <Option value="ekb">Екатеринбург</Option>
                  <Option value="nsk">Новосибирск</Option>
                  <Option value="kzn">Казань</Option>
                </Select>
              </div>

              <Divider />

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <Checkbox
                  checked={analysisParams.includeGESN}
                  onChange={(e) => setAnalysisParams(prev => ({ ...prev, includeGESN: e.target.checked }))}
                >
                  Включить расценки ГЭСН
                </Checkbox>
                
                <Checkbox
                  checked={analysisParams.includeFER}
                  onChange={(e) => setAnalysisParams(prev => ({ ...prev, includeFER: e.target.checked }))}
                >
                  Включить расценки ФЕР
                </Checkbox>
                
                <Checkbox
                  checked={analysisParams.includeRegionalCoeff}
                  onChange={(e) => setAnalysisParams(prev => ({ ...prev, includeRegionalCoeff: e.target.checked }))}
                >
                  Применить региональные коэффициенты
                </Checkbox>
              </div>
            </div>
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
          disabled={files.length === 0 || isAnalyzing}
          loading={isAnalyzing}
        >
          {isAnalyzing ? 'Выполняется анализ...' : 'Начать анализ смет'}
        </Button>
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
              Анализируем {files.length} файл(ов)...
            </p>
          </div>
        </Card>
      )}

      {/* Результаты анализа */}
      {analysisResult && (
        <Card 
          title="✅ Результаты анализа смет"
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
          {/* Сводная информация */}
          <Descriptions column={4} bordered>
            <Descriptions.Item label="Общая стоимость">
              <span style={{ fontSize: '18px', fontWeight: 'bold', color: '#52c41a' }}>
                {analysisResult.summary.total_cost}
              </span>
            </Descriptions.Item>
            <Descriptions.Item label="Количество позиций">
              {analysisResult.summary.items_count}
            </Descriptions.Item>
            <Descriptions.Item label="Ошибки">
              <span style={{ color: analysisResult.summary.errors_count > 0 ? '#ff4d4f' : '#52c41a' }}>
                {analysisResult.summary.errors_count}
              </span>
            </Descriptions.Item>
            <Descriptions.Item label="Предупреждения">
              <span style={{ color: analysisResult.summary.warnings_count > 0 ? '#faad14' : '#52c41a' }}>
                {analysisResult.summary.warnings_count}
              </span>
            </Descriptions.Item>
            <Descriptions.Item label="Соответствие ГЭСН" span={2}>
              {analysisResult.compliance_check.gesn_compliance}
            </Descriptions.Item>
            <Descriptions.Item label="Региональные коэффициенты" span={2}>
              {analysisResult.compliance_check.regional_coefficients}
            </Descriptions.Item>
          </Descriptions>

          {/* Детальная таблица */}
          <Divider orientation="left">Детализация по позициям</Divider>
          <Table
            columns={detailColumns}
            dataSource={analysisResult.details}
            rowKey="name"
            size="small"
            scroll={{ x: 800 }}
            pagination={{ 
              pageSize: 10, 
              showSizeChanger: true,
              showTotal: (total, range) => `${range[0]}-${range[1]} из ${total} позиций`
            }}
          />
        </Card>
      )}

      {/* Ошибки */}
      {analysisError && (
        <Result
          status="error"
          title="Ошибка анализа смет"
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

export default EstimateAnalyzer;