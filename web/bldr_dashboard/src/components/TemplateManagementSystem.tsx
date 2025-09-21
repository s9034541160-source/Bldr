/**
 * Template Management System
 * Система управления шаблонами документов с поиском, адаптацией и аналитикой
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Tabs,
  Row,
  Col,
  Button,
  Table,
  Tag,
  Space,
  Input,
  Select,
  Modal,
  Form,
  Upload,
  Progress,
  Statistic,
  List,
  Avatar,
  Descriptions,
  Divider,
  Alert,
  Tooltip,
  Badge,
  message,
  notification,
  Spin,
  Empty,
  Drawer,
  Steps,
  Radio,
  Checkbox,
  DatePicker,
  InputNumber,
  Switch
} from 'antd';
import {
  SearchOutlined,
  FilterOutlined,
  DownloadOutlined,
  UploadOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  CopyOutlined,
  FileTextOutlined,
  FolderOutlined,
  TagOutlined,
  StarOutlined,
  ClockCircleOutlined,
  UserOutlined,
  SettingOutlined,
  PlusOutlined,
  ReloadOutlined,
  ExportOutlined,
  ImportOutlined,
  ShareAltOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  InfoCircleOutlined,
  ThunderboltOutlined,
  RocketOutlined,
  BulbOutlined,
  HeartOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import type { ColumnsType } from 'antd/es/table';
import { apiService, unwrap } from '../services/api';
import ErrorBoundary from './ErrorBoundary';

const { TabPane } = Tabs;
const { Option } = Select;
const { Search } = Input;
const { TextArea } = Input;
const { Dragger } = Upload;
const { Step } = Steps;

// Интерфейсы
interface Template {
  id: string;
  name: string;
  category: string;
  format: string;
  size: number;
  created_date: string;
  modified_date: string;
  author: string;
  organization: string;
  description: string;
  tags: string[];
  placeholders: Placeholder[];
  usage_count: number;
  quality_score: number;
  complexity: string;
  language: string;
  file_path: string;
  preview_url?: string;
}

interface Placeholder {
  name: string;
  type: string;
  required: boolean;
  description: string;
  default_value?: string;
}

interface SearchResult {
  title: string;
  url: string;
  source: string;
  relevance_score: number;
  document_type?: string;
  preview?: string;
  metadata: Record<string, any>;
}

interface CompanyInfo {
  name: string;
  full_name: string;
  address: string;
  city: string;
  phone: string;
  email: string;
  inn: string;
  kpp: string;
  director: string;
  director_position: string;
}

interface ProjectInfo {
  name: string;
  description: string;
  address: string;
  budget: number;
  currency: string;
  start_date: string;
  end_date: string;
  client: string;
  contract_number: string;
}

const TemplateManagementSystem: React.FC = () => {
  const [activeTab, setActiveTab] = useState('library');
  const [templates, setTemplates] = useState<Template[]>([]);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  
  // Состояние поиска и фильтров
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedFormat, setSelectedFormat] = useState<string>('');
  const [selectedComplexity, setSelectedComplexity] = useState<string>('');
  
  // Модальные окна
  const [templateModalVisible, setTemplateModalVisible] = useState(false);
  const [adaptationModalVisible, setAdaptationModalVisible] = useState(false);
  const [searchModalVisible, setSearchModalVisible] = useState(false);
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  
  // Выбранный шаблон
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  
  // Данные для адаптации
  const [companyInfo, setCompanyInfo] = useState<CompanyInfo>({
    name: '',
    full_name: '',
    address: '',
    city: '',
    phone: '',
    email: '',
    inn: '',
    kpp: '',
    director: '',
    director_position: 'Генеральный директор'
  });
  
  const [projectInfo, setProjectInfo] = useState<ProjectInfo>({
    name: '',
    description: '',
    address: '',
    budget: 0,
    currency: 'RUB',
    start_date: '',
    end_date: '',
    client: '',
    contract_number: ''
  });
  
  // Шаг адаптации
  const [adaptationStep, setAdaptationStep] = useState(0);
  
  useEffect(() => {
    loadTemplates();
  }, []);
  
  const loadTemplates = async () => {
    setLoading(true);
    try {
      // Здесь должен быть вызов API для загрузки шаблонов
      // Пока используем моковые данные
      const mockTemplates: Template[] = [
        {
          id: '1',
          name: 'Договор строительного подряда',
          category: 'contracts',
          format: 'docx',
          size: 45678,
          created_date: '2024-01-15T10:30:00Z',
          modified_date: '2024-01-20T14:45:00Z',
          author: 'Иванов И.И.',
          organization: 'ООО СтройИнвест',
          description: 'Стандартный договор на выполнение строительных работ',
          tags: ['строительство', 'подряд', 'договор'],
          placeholders: [
            { name: 'COMPANY_NAME', type: 'text', required: true, description: 'Название компании' },
            { name: 'PROJECT_ADDRESS', type: 'text', required: true, description: 'Адрес объекта' },
            { name: 'CONTRACT_AMOUNT', type: 'money', required: true, description: 'Сумма договора' }
          ],
          usage_count: 25,
          quality_score: 0.92,
          complexity: 'medium',
          language: 'ru',
          file_path: '/templates/contract_construction.docx'
        },
        {
          id: '2',
          name: 'Акт выполненных работ',
          category: 'acts',
          format: 'docx',
          size: 23456,
          created_date: '2024-01-10T09:15:00Z',
          modified_date: '2024-01-18T16:20:00Z',
          author: 'Петров П.П.',
          organization: 'ООО СтройИнвест',
          description: 'Акт приемки выполненных строительных работ',
          tags: ['акт', 'приемка', 'работы'],
          placeholders: [
            { name: 'WORK_DESCRIPTION', type: 'text', required: true, description: 'Описание работ' },
            { name: 'WORK_AMOUNT', type: 'money', required: true, description: 'Стоимость работ' },
            { name: 'COMPLETION_DATE', type: 'date', required: true, description: 'Дата завершения' }
          ],
          usage_count: 18,
          quality_score: 0.88,
          complexity: 'simple',
          language: 'ru',
          file_path: '/templates/act_completion.docx'
        }
      ];
      
      setTemplates(mockTemplates);
    } catch (error) {
      console.error('Error loading templates:', error);
      message.error('Ошибка загрузки шаблонов');
    } finally {
      setLoading(false);
    }
  };
  
  const searchInternetTemplates = async () => {
    if (!searchQuery.trim()) {
      message.warning('Введите поисковый запрос');
      return;
    }
    
    setSearchLoading(true);
    try {
      const result = await apiService.executeUnifiedTool('enhanced_search_internet_templates', {
        query: searchQuery,
        doc_type: selectedCategory || undefined,
        language: 'ru',
        max_results: 20
      });
      const { ok, data, error } = unwrap<any>(result);
      if (ok) {
        setSearchResults((data?.results) || []);
        const total = data?.total_found ?? (data?.results?.length || 0);
        message.success(`Найдено ${total} шаблонов`);
      } else {
        message.error(`Ошибка поиска: ${String(error)}`);
      }
    } catch (error) {
      console.error('Error searching templates:', error);
      message.error('Ошибка поиска шаблонов');
    } finally {
      setSearchLoading(false);
    }
  };
  
  const downloadTemplate = async (searchResult: SearchResult) => {
    try {
      const result = await apiService.executeUnifiedTool('download_and_adapt_template', {
        template_url: searchResult.url,
        template_name: searchResult.title
      });
      const { ok, error } = unwrap<any>(result);
      if (ok) {
        message.success('Шаблон успешно загружен');
        loadTemplates();
      } else {
        message.error(`Ошибка загрузки: ${String(error)}`);
      }
    } catch (error) {
      console.error('Error downloading template:', error);
      message.error('Ошибка загрузки шаблона');
    }
  };
  
  const adaptTemplate = async () => {
    if (!selectedTemplate) return;
    
    try {
      const result = await apiService.executeUnifiedTool('adapt_template_for_company', {
        template_path: selectedTemplate.file_path,
        company_info: companyInfo,
        project_info: projectInfo
      });
      const { ok, data, error } = unwrap<any>(result);
      if (ok) {
        message.success('Шаблон успешно адаптирован');
        notification.success({
          message: 'Адаптация завершена',
          description: `Файл сохранен: ${data?.adapted_file || 'см. результаты'}`,
          duration: 10
        });
        setAdaptationModalVisible(false);
      } else {
        message.error(`Ошибка адаптации: ${String(error)}`);
      }
    } catch (error) {
      console.error('Error adapting template:', error);
      message.error('Ошибка адаптации шаблона');
    }
  };
  
  // Колонки таблицы шаблонов
  const templateColumns: ColumnsType<Template> = [
    {
      title: 'Шаблон',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          <FileTextOutlined />
          <div>
            <div style={{ fontWeight: 'bold' }}>{text}</div>
            <div style={{ fontSize: '12px', color: '#666' }}>
              {record.description}
            </div>
          </div>
        </Space>
      )
    },
    {
      title: 'Категория',
      dataIndex: 'category',
      key: 'category',
      render: (category) => (
        <Tag color="blue">{category}</Tag>
      )
    },
    {
      title: 'Формат',
      dataIndex: 'format',
      key: 'format',
      render: (format) => (
        <Tag>{format.toUpperCase()}</Tag>
      )
    },
    {
      title: 'Качество',
      dataIndex: 'quality_score',
      key: 'quality_score',
      render: (score) => (
        <Progress 
          percent={score * 100} 
          size="small" 
          status={score > 0.8 ? 'success' : score > 0.6 ? 'normal' : 'exception'}
        />
      )
    },
    {
      title: 'Использований',
      dataIndex: 'usage_count',
      key: 'usage_count',
      render: (count) => (
        <Badge count={count} style={{ backgroundColor: '#52c41a' }} />
      )
    },
    {
      title: 'Действия',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Tooltip title="Просмотр">
            <Button 
              type="text" 
              icon={<EyeOutlined />}
              onClick={() => {
                setSelectedTemplate(record);
                setTemplateModalVisible(true);
              }}
            />
          </Tooltip>
          <Tooltip title="Адаптировать">
            <Button 
              type="text" 
              icon={<EditOutlined />}
              onClick={() => {
                setSelectedTemplate(record);
                setAdaptationModalVisible(true);
              }}
            />
          </Tooltip>
          <Tooltip title="Скачать">
            <Button 
              type="text" 
              icon={<DownloadOutlined />}
              onClick={() => {
                // Логика скачивания
              }}
            />
          </Tooltip>
        </Space>
      )
    }
  ];
  
  // Колонки таблицы результатов поиска
  const searchColumns: ColumnsType<SearchResult> = [
    {
      title: 'Название',
      dataIndex: 'title',
      key: 'title',
      render: (text, record) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{text}</div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            {record.preview}
          </div>
        </div>
      )
    },
    {
      title: 'Источник',
      dataIndex: 'source',
      key: 'source',
      render: (source) => (
        <Tag color="green">{source}</Tag>
      )
    },
    {
      title: 'Релевантность',
      dataIndex: 'relevance_score',
      key: 'relevance_score',
      render: (score) => (
        <Progress 
          percent={score * 10} 
          size="small" 
          format={() => `${score.toFixed(1)}`}
        />
      )
    },
    {
      title: 'Действия',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button 
            type="primary" 
            size="small"
            icon={<DownloadOutlined />}
            onClick={() => downloadTemplate(record)}
          >
            Загрузить
          </Button>
          <Button 
            type="text" 
            size="small"
            icon={<EyeOutlined />}
            onClick={() => window.open(record.url, '_blank')}
          >
            Открыть
          </Button>
        </Space>
      )
    }
  ];  
  return (
    <ErrorBoundary>
    <div style={{ padding: '24px' }}>
      {/* Заголовок */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Space>
            <FolderOutlined style={{ fontSize: '24px', color: '#1890ff' }} />
            <h1 style={{ margin: 0 }}>Управление шаблонами</h1>
          </Space>
        </Col>
        <Col>
          <Space>
            <Button 
              icon={<PlusOutlined />}
              onClick={() => setUploadModalVisible(true)}
            >
              Добавить шаблон
            </Button>
            <Button 
              icon={<SearchOutlined />}
              type="primary"
              onClick={() => setSearchModalVisible(true)}
            >
              Поиск в интернете
            </Button>
          </Space>
        </Col>
      </Row>

      {/* Основные вкладки */}
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        {/* Библиотека шаблонов */}
        <TabPane tab={<span><FolderOutlined />Библиотека</span>} key="library">
          <Card>
            {/* Фильтры */}
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={8}>
                <Search
                  placeholder="Поиск шаблонов..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onSearch={() => {
                    // Фильтрация локальных шаблонов
                  }}
                />
              </Col>
              <Col span={4}>
                <Select
                  placeholder="Категория"
                  value={selectedCategory}
                  onChange={setSelectedCategory}
                  allowClear
                  style={{ width: '100%' }}
                >
                  <Option value="contracts">Договоры</Option>
                  <Option value="acts">Акты</Option>
                  <Option value="reports">Отчеты</Option>
                  <Option value="letters">Письма</Option>
                  <Option value="estimates">Сметы</Option>
                </Select>
              </Col>
              <Col span={4}>
                <Select
                  placeholder="Формат"
                  value={selectedFormat}
                  onChange={setSelectedFormat}
                  allowClear
                  style={{ width: '100%' }}
                >
                  <Option value="docx">DOCX</Option>
                  <Option value="pdf">PDF</Option>
                  <Option value="txt">TXT</Option>
                  <Option value="html">HTML</Option>
                </Select>
              </Col>
              <Col span={4}>
                <Select
                  placeholder="Сложность"
                  value={selectedComplexity}
                  onChange={setSelectedComplexity}
                  allowClear
                  style={{ width: '100%' }}
                >
                  <Option value="simple">Простой</Option>
                  <Option value="medium">Средний</Option>
                  <Option value="complex">Сложный</Option>
                </Select>
              </Col>
              <Col span={4}>
                <Button 
                  icon={<ReloadOutlined />}
                  onClick={loadTemplates}
                >
                  Обновить
                </Button>
              </Col>
            </Row>

            {/* Таблица шаблонов */}
            <Table
              columns={templateColumns}
              dataSource={templates}
              rowKey="id"
              loading={loading}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) => `${range[0]}-${range[1]} из ${total} шаблонов`
              }}
            />
          </Card>
        </TabPane>

        {/* Поиск в интернете */}
        <TabPane tab={<span><SearchOutlined />Поиск в интернете</span>} key="search">
          <Card>
            {/* Форма поиска */}
            <Row gutter={16} style={{ marginBottom: 24 }}>
              <Col span={12}>
                <Search
                  placeholder="Введите запрос для поиска шаблонов..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onSearch={searchInternetTemplates}
                  enterButton="Найти"
                  size="large"
                />
              </Col>
              <Col span={6}>
                <Select
                  placeholder="Тип документа"
                  value={selectedCategory}
                  onChange={setSelectedCategory}
                  allowClear
                  style={{ width: '100%' }}
                  size="large"
                >
                  <Option value="contract">Договоры</Option>
                  <Option value="report">Отчеты</Option>
                  <Option value="application">Заявления</Option>
                  <Option value="letter">Письма</Option>
                  <Option value="act">Акты</Option>
                  <Option value="estimate">Сметы</Option>
                </Select>
              </Col>
              <Col span={6}>
                <Button 
                  type="primary"
                  size="large"
                  icon={<ThunderboltOutlined />}
                  onClick={searchInternetTemplates}
                  loading={searchLoading}
                  block
                >
                  Расширенный поиск
                </Button>
              </Col>
            </Row>

            {/* Результаты поиска */}
            {searchResults.length > 0 && (
              <Table
                columns={searchColumns}
                dataSource={searchResults}
                rowKey="url"
                loading={searchLoading}
                pagination={{
                  pageSize: 10,
                  showTotal: (total, range) => `${range[0]}-${range[1]} из ${total} результатов`
                }}
              />
            )}

            {searchResults.length === 0 && !searchLoading && (
              <Empty 
                description="Введите запрос для поиска шаблонов в интернете"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            )}
          </Card>
        </TabPane>

        {/* Аналитика */}
        <TabPane tab={<span><BarChartOutlined />Аналитика</span>} key="analytics">
          <Row gutter={16}>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Всего шаблонов"
                  value={templates.length}
                  prefix={<FileTextOutlined />}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Использований"
                  value={templates.reduce((sum, t) => sum + t.usage_count, 0)}
                  prefix={<RocketOutlined />}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Средняя оценка"
                  value={templates.reduce((sum, t) => sum + t.quality_score, 0) / templates.length}
                  precision={2}
                  prefix={<StarOutlined />}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Категорий"
                  value={new Set(templates.map(t => t.category)).size}
                  prefix={<TagOutlined />}
                />
              </Card>
            </Col>
          </Row>

          <Row gutter={16} style={{ marginTop: 16 }}>
            <Col span={12}>
              <Card title="Популярные шаблоны">
                <List
                  dataSource={templates.sort((a, b) => b.usage_count - a.usage_count).slice(0, 5)}
                  renderItem={(template) => (
                    <List.Item>
                      <List.Item.Meta
                        avatar={<Avatar icon={<FileTextOutlined />} />}
                        title={template.name}
                        description={`Использований: ${template.usage_count}`}
                      />
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
            <Col span={12}>
              <Card title="Последние добавленные">
                <List
                  dataSource={templates.sort((a, b) => 
                    new Date(b.created_date).getTime() - new Date(a.created_date).getTime()
                  ).slice(0, 5)}
                  renderItem={(template) => (
                    <List.Item>
                      <List.Item.Meta
                        avatar={<Avatar icon={<ClockCircleOutlined />} />}
                        title={template.name}
                        description={new Date(template.created_date).toLocaleDateString()}
                      />
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
          </Row>
        </TabPane>
      </Tabs>

      {/* Модальное окно просмотра шаблона */}
      <Modal
        title="Информация о шаблоне"
        open={templateModalVisible}
        onCancel={() => setTemplateModalVisible(false)}
        width={800}
        footer={[
          <Button key="close" onClick={() => setTemplateModalVisible(false)}>
            Закрыть
          </Button>,
          <Button 
            key="adapt" 
            type="primary"
            onClick={() => {
              setTemplateModalVisible(false);
              setAdaptationModalVisible(true);
            }}
          >
            Адаптировать
          </Button>
        ]}
      >
        {selectedTemplate && (
          <div>
            <Descriptions column={2} bordered>
              <Descriptions.Item label="Название">{selectedTemplate.name}</Descriptions.Item>
              <Descriptions.Item label="Категория">{selectedTemplate.category}</Descriptions.Item>
              <Descriptions.Item label="Формат">{selectedTemplate.format}</Descriptions.Item>
              <Descriptions.Item label="Размер">{(selectedTemplate.size / 1024).toFixed(1)} KB</Descriptions.Item>
              <Descriptions.Item label="Автор">{selectedTemplate.author}</Descriptions.Item>
              <Descriptions.Item label="Организация">{selectedTemplate.organization}</Descriptions.Item>
              <Descriptions.Item label="Создан">
                {new Date(selectedTemplate.created_date).toLocaleDateString()}
              </Descriptions.Item>
              <Descriptions.Item label="Изменен">
                {new Date(selectedTemplate.modified_date).toLocaleDateString()}
              </Descriptions.Item>
            </Descriptions>

            <Divider />

            <h4>Описание</h4>
            <p>{selectedTemplate.description}</p>

            <h4>Теги</h4>
            <Space wrap>
              {selectedTemplate.tags.map(tag => (
                <Tag key={tag} color="blue">{tag}</Tag>
              ))}
            </Space>

            <Divider />

            <h4>Плейсхолдеры ({selectedTemplate.placeholders.length})</h4>
            <List
              size="small"
              dataSource={selectedTemplate.placeholders}
              renderItem={(placeholder) => (
                <List.Item>
                  <List.Item.Meta
                    title={
                      <Space>
                        <span>{placeholder.name}</span>
                        <Tag color={placeholder.required ? 'red' : 'default'}>
                          {placeholder.required ? 'Обязательный' : 'Опциональный'}
                        </Tag>
                        <Tag>{placeholder.type}</Tag>
                      </Space>
                    }
                    description={placeholder.description}
                  />
                </List.Item>
              )}
            />
          </div>
        )}
      </Modal>  
    {/* Модальное окно адаптации шаблона */}
      <Modal
        title="Адаптация шаблона"
        open={adaptationModalVisible}
        onCancel={() => setAdaptationModalVisible(false)}
        width={1000}
        footer={null}
      >
        <Steps current={adaptationStep} style={{ marginBottom: 24 }}>
          <Step title="Данные компании" icon={<UserOutlined />} />
          <Step title="Данные проекта" icon={<RocketOutlined />} />
          <Step title="Проверка" icon={<CheckCircleOutlined />} />
        </Steps>

        {adaptationStep === 0 && (
          <Form layout="vertical">
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="Название компании" required>
                  <Input
                    value={companyInfo.name}
                    onChange={(e) => setCompanyInfo({...companyInfo, name: e.target.value})}
                    placeholder="ООО 'Название'"
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="Полное название">
                  <Input
                    value={companyInfo.full_name}
                    onChange={(e) => setCompanyInfo({...companyInfo, full_name: e.target.value})}
                    placeholder="Общество с ограниченной ответственностью..."
                  />
                </Form.Item>
              </Col>
            </Row>
            
            <Row gutter={16}>
              <Col span={16}>
                <Form.Item label="Адрес">
                  <Input
                    value={companyInfo.address}
                    onChange={(e) => setCompanyInfo({...companyInfo, address: e.target.value})}
                    placeholder="123456, г. Москва, ул. Примерная, д. 1"
                  />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item label="Город">
                  <Input
                    value={companyInfo.city}
                    onChange={(e) => setCompanyInfo({...companyInfo, city: e.target.value})}
                    placeholder="Москва"
                  />
                </Form.Item>
              </Col>
            </Row>
            
            <Row gutter={16}>
              <Col span={8}>
                <Form.Item label="Телефон">
                  <Input
                    value={companyInfo.phone}
                    onChange={(e) => setCompanyInfo({...companyInfo, phone: e.target.value})}
                    placeholder="+7 (495) 123-45-67"
                  />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item label="Email">
                  <Input
                    value={companyInfo.email}
                    onChange={(e) => setCompanyInfo({...companyInfo, email: e.target.value})}
                    placeholder="info@company.ru"
                  />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item label="ИНН">
                  <Input
                    value={companyInfo.inn}
                    onChange={(e) => setCompanyInfo({...companyInfo, inn: e.target.value})}
                    placeholder="1234567890"
                  />
                </Form.Item>
              </Col>
            </Row>
            
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="Директор">
                  <Input
                    value={companyInfo.director}
                    onChange={(e) => setCompanyInfo({...companyInfo, director: e.target.value})}
                    placeholder="Иванов Иван Иванович"
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="Должность директора">
                  <Input
                    value={companyInfo.director_position}
                    onChange={(e) => setCompanyInfo({...companyInfo, director_position: e.target.value})}
                    placeholder="Генеральный директор"
                  />
                </Form.Item>
              </Col>
            </Row>
          </Form>
        )}

        {adaptationStep === 1 && (
          <Form layout="vertical">
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="Название проекта">
                  <Input
                    value={projectInfo.name}
                    onChange={(e) => setProjectInfo({...projectInfo, name: e.target.value})}
                    placeholder="Строительство жилого дома"
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="Номер договора">
                  <Input
                    value={projectInfo.contract_number}
                    onChange={(e) => setProjectInfo({...projectInfo, contract_number: e.target.value})}
                    placeholder="СД-2024-001"
                  />
                </Form.Item>
              </Col>
            </Row>
            
            <Form.Item label="Описание проекта">
              <TextArea
                rows={3}
                value={projectInfo.description}
                onChange={(e) => setProjectInfo({...projectInfo, description: e.target.value})}
                placeholder="Подробное описание проекта..."
              />
            </Form.Item>
            
            <Form.Item label="Адрес объекта">
              <Input
                value={projectInfo.address}
                onChange={(e) => setProjectInfo({...projectInfo, address: e.target.value})}
                placeholder="г. Москва, ул. Строительная, участок 10"
              />
            </Form.Item>
            
            <Row gutter={16}>
              <Col span={8}>
                <Form.Item label="Бюджет">
                  <InputNumber
                    style={{ width: '100%' }}
                    value={projectInfo.budget}
                    onChange={(value) => setProjectInfo({...projectInfo, budget: value || 0})}
                    placeholder="5000000"
                    formatter={value => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
                  />
                </Form.Item>
              </Col>
              <Col span={4}>
                <Form.Item label="Валюта">
                  <Select
                    value={projectInfo.currency}
                    onChange={(value) => setProjectInfo({...projectInfo, currency: value})}
                  >
                    <Option value="RUB">RUB</Option>
                    <Option value="USD">USD</Option>
                    <Option value="EUR">EUR</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="Клиент">
                  <Input
                    value={projectInfo.client}
                    onChange={(e) => setProjectInfo({...projectInfo, client: e.target.value})}
                    placeholder="ИП Петров П.П."
                  />
                </Form.Item>
              </Col>
            </Row>
            
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="Дата начала">
                  <DatePicker
                    style={{ width: '100%' }}
                    value={projectInfo.start_date ? dayjs(projectInfo.start_date) : null}
                    onChange={(date) => setProjectInfo({
                      ...projectInfo, 
                      start_date: date ? date.format('YYYY-MM-DD') : ''
                    })}
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="Дата окончания">
                  <DatePicker
                    style={{ width: '100%' }}
                    value={projectInfo.end_date ? dayjs(projectInfo.end_date) : null}
                    onChange={(date) => setProjectInfo({
                      ...projectInfo, 
                      end_date: date ? date.format('YYYY-MM-DD') : ''
                    })}
                  />
                </Form.Item>
              </Col>
            </Row>
          </Form>
        )}

        {adaptationStep === 2 && (
          <div>
            <Alert
              message="Проверьте данные перед адаптацией"
              description="Убедитесь, что все данные введены корректно. После адаптации будет создан новый документ."
              type="info"
              style={{ marginBottom: 16 }}
            />
            
            <Row gutter={16}>
              <Col span={12}>
                <Card title="Данные компании" size="small">
                  <Descriptions column={1} size="small">
                    <Descriptions.Item label="Название">{companyInfo.name}</Descriptions.Item>
                    <Descriptions.Item label="Адрес">{companyInfo.address}</Descriptions.Item>
                    <Descriptions.Item label="Телефон">{companyInfo.phone}</Descriptions.Item>
                    <Descriptions.Item label="Email">{companyInfo.email}</Descriptions.Item>
                    <Descriptions.Item label="Директор">{companyInfo.director}</Descriptions.Item>
                  </Descriptions>
                </Card>
              </Col>
              <Col span={12}>
                <Card title="Данные проекта" size="small">
                  <Descriptions column={1} size="small">
                    <Descriptions.Item label="Название">{projectInfo.name}</Descriptions.Item>
                    <Descriptions.Item label="Адрес">{projectInfo.address}</Descriptions.Item>
                    <Descriptions.Item label="Бюджет">
                      {projectInfo.budget.toLocaleString()} {projectInfo.currency}
                    </Descriptions.Item>
                    <Descriptions.Item label="Клиент">{projectInfo.client}</Descriptions.Item>
                    <Descriptions.Item label="Договор">{projectInfo.contract_number}</Descriptions.Item>
                  </Descriptions>
                </Card>
              </Col>
            </Row>
          </div>
        )}

        <div style={{ marginTop: 24, textAlign: 'right' }}>
          <Space>
            {adaptationStep > 0 && (
              <Button onClick={() => setAdaptationStep(adaptationStep - 1)}>
                Назад
              </Button>
            )}
            {adaptationStep < 2 ? (
              <Button 
                type="primary" 
                onClick={() => setAdaptationStep(adaptationStep + 1)}
              >
                Далее
              </Button>
            ) : (
              <Button 
                type="primary" 
                icon={<RocketOutlined />}
                onClick={adaptTemplate}
              >
                Адаптировать шаблон
              </Button>
            )}
          </Space>
        </div>
      </Modal>

      {/* Модальное окно поиска */}
      <Modal
        title="Поиск шаблонов в интернете"
        open={searchModalVisible}
        onCancel={() => setSearchModalVisible(false)}
        width={800}
        footer={null}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Search
            placeholder="Введите запрос для поиска..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onSearch={searchInternetTemplates}
            enterButton="Найти"
            size="large"
          />
          
          <Row gutter={16}>
            <Col span={12}>
              <Select
                placeholder="Тип документа"
                value={selectedCategory}
                onChange={setSelectedCategory}
                allowClear
                style={{ width: '100%' }}
              >
                <Option value="contract">Договоры</Option>
                <Option value="report">Отчеты</Option>
                <Option value="application">Заявления</Option>
                <Option value="letter">Письма</Option>
                <Option value="act">Акты</Option>
                <Option value="estimate">Сметы</Option>
              </Select>
            </Col>
            <Col span={12}>
              <Select
                placeholder="Тип компании"
                allowClear
                style={{ width: '100%' }}
              >
                <Option value="construction">Строительство</Option>
                <Option value="government">Государственные</Option>
                <Option value="business">Бизнес</Option>
              </Select>
            </Col>
          </Row>
        </Space>
      </Modal>

      {/* Модальное окно загрузки */}
      <Modal
        title="Загрузка шаблона"
        open={uploadModalVisible}
        onCancel={() => setUploadModalVisible(false)}
        width={600}
        footer={null}
      >
        <Dragger
          name="template"
          multiple={false}
          accept=".docx,.pdf,.txt,.html"
          beforeUpload={() => false} // Предотвращаем автоматическую загрузку
        >
          <p className="ant-upload-drag-icon">
            <UploadOutlined />
          </p>
          <p className="ant-upload-text">Нажмите или перетащите файл для загрузки</p>
          <p className="ant-upload-hint">
            Поддерживаются форматы: DOCX, PDF, TXT, HTML
          </p>
        </Dragger>
        
        <Form layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item label="Название шаблона">
            <Input placeholder="Введите название шаблона" />
          </Form.Item>
          <Form.Item label="Категория">
            <Select placeholder="Выберите категорию">
              <Option value="contracts">Договоры</Option>
              <Option value="acts">Акты</Option>
              <Option value="reports">Отчеты</Option>
              <Option value="letters">Письма</Option>
              <Option value="estimates">Сметы</Option>
            </Select>
          </Form.Item>
          <Form.Item label="Описание">
            <TextArea rows={3} placeholder="Описание шаблона" />
          </Form.Item>
        </Form>
        
        <div style={{ textAlign: 'right', marginTop: 16 }}>
          <Space>
            <Button onClick={() => setUploadModalVisible(false)}>
              Отмена
            </Button>
            <Button type="primary">
              Загрузить
            </Button>
          </Space>
        </div>
      </Modal>
    </div>
    </ErrorBoundary>
  );
};

export default TemplateManagementSystem;