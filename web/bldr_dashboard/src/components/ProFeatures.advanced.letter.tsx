import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Form, 
  Input, 
  Button, 
  Tabs, 
  message, 
  Spin, 
  Select, 
  Row, 
  Col,
  Divider,
  Space,
  Slider,
  Table,
  Tag,
  InputNumber
} from 'antd';
import { 
  FilePdfOutlined, 
  DownloadOutlined,
  SearchOutlined,
  SyncOutlined
} from '@ant-design/icons';
import { apiService, Template } from '../services/api';
import { useStore } from '../store';

const { TabPane } = Tabs;
const { Option } = Select;

const AdvancedLetterGeneration: React.FC = () => {
  const [activeTab, setActiveTab] = useState('letters');
  const [loading, setLoading] = useState(false);
  const [letterForm] = Form.useForm();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [templatesLoading, setTemplatesLoading] = useState(false);
  const [letterText, setLetterText] = useState('');
  const [letterTokens, setLetterTokens] = useState(0);
  const [tone, setTone] = useState(0);
  const [dryness, setDryness] = useState(0.5);
  const [humanity, setHumanity] = useState(0.7);
  const [length, setLength] = useState('medium');
  const [formality, setFormality] = useState('formal');
  const [improveLoading, setImproveLoading] = useState(false);
  
  // Norms management state
  const [normsData, setNormsData] = useState<any[]>([]);
  const [normsLoading, setNormsLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  const [totalCount, setTotalCount] = useState(0);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [actualCount, setActualCount] = useState(0);
  const [outdatedCount, setOutdatedCount] = useState(0);
  const [updating, setUpdating] = useState(false);
  
  const { projects, fetchProjects } = useStore();
  const [selectedProject, setSelectedProject] = useState<string | null>(null);

  // Load projects and templates on component mount
  useEffect(() => {
    fetchProjects();
    loadTemplates();
  }, [fetchProjects]);

  // Load templates for letter generation
  const loadTemplates = async () => {
    try {
      setTemplatesLoading(true);
      const templates = await apiService.getTemplates();
      setTemplates(templates);
    } catch (error) {
      console.error('Failed to load templates:', error);
      message.error('Не удалось загрузить шаблоны писем');
    } finally {
      setTemplatesLoading(false);
    }
  };

  // Handle project selection
  const handleProjectSelect = async (projectId: string) => {
    setSelectedProject(projectId);
    
    if (projectId) {
      try {
        // Fetch project data from the backend
        const project = await apiService.getProject(projectId);
        if (project) {
          // Auto-fill form with project data
          const projectData = {
            recipient: project.name || '',
            subject: `Письмо по проекту ${project.name}`
          };
          
          letterForm.setFieldsValue(projectData);
          message.info(`Данные проекта ${project.name} загружены`);
        }
      } catch (error) {
        console.error('Error loading project data:', error);
        message.error('Не удалось загрузить данные проекта');
      }
    }
  };

  // Handle template loading
  const loadTemplate = (templateId: string) => {
    const template = templates.find(t => t.id === templateId);
    if (template) {
      letterForm.setFieldsValue({
        description: template.preview,
        subject: template.name
      });
      message.info(`Загружен шаблон: ${template.name}`);
    }
  };

  // Handle advanced letter generation
  const handleGenerateAdvancedLetter = async (values: any) => {
    try {
      setLoading(true);
      
      // Check if we're improving a draft or generating a new letter
      if (values.draft && values.draft.trim() !== '') {
        // Improve existing draft
        await handleImprove(values);
        return;
      }
      
      // Generate new letter with default values for optional fields
      const letterData = {
        description: values.description || '',
        template_id: values.template_id || '',
        project_id: values.project_id || '',
        tone: tone,
        dryness: dryness,
        humanity: humanity,
        length: length,
        formality: formality,
        recipient: values.recipient || '',
        sender: values.sender || 'АО БЛДР',
        subject: values.subject || ''
      };

      const response = await apiService.generateAdvancedLetter(letterData);

      if (response.status === 'success') {
        message.success('Письмо успешно сгенерировано!');
        setLetterText(response.letter || '');
        setLetterTokens(response.tokens || 0);
      } else {
        throw new Error(response.error || 'Не удалось сгенерировать письмо');
      }
    } catch (error: any) {
      console.error('Ошибка генерации письма:', error);
      message.error(error.message || 'Не удалось сгенерировать письмо');
    } finally {
      setLoading(false);
    }
  };

  // Handle letter improvement
  const handleImprove = async (values: any) => {
    try {
      setImproveLoading(true);
      
      const improveData = {
        draft: values.draft || '',
        description: values.description || '',
        template_id: values.template_id || '',
        project_id: values.project_id || '',
        tone: tone,
        dryness: dryness,
        humanity: humanity,
        length: length,
        formality: formality
      };

      const response = await apiService.improveLetter(improveData);

      if (response.status === 'success') {
        message.success('Письмо успешно улучшено!');
        setLetterText(response.letter || '');
        setLetterTokens(response.tokens || 0);
      } else {
        throw new Error(response.error || 'Не удалось улучшить письмо');
      }
    } catch (error: any) {
      console.error('Ошибка улучшения письма:', error);
      message.error(error.message || 'Не удалось улучшить письмо');
    } finally {
      setImproveLoading(false);
    }
  };

  // Handle letter download
  const downloadLetter = async (format: string) => {
    try {
      if (!letterText) {
        message.warning('Нет текста письма для скачивания');
        return;
      }
      
      // For now, we'll create a simple text file download
      // In a real implementation, this would call the backend to generate and download the file
      const blob = new Blob([letterText], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      
      // Create a temporary link and trigger download
      const a = document.createElement('a');
      a.href = url;
      a.download = `letter_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.${format}`;
      document.body.appendChild(a);
      a.click();
      
      // Clean up
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      message.success(`Письмо скачано как ${format.toUpperCase()}`);
    } catch (error) {
      console.error('Ошибка скачивания письма:', error);
      message.error('Не удалось скачать письмо');
    }
  };

  // Load norms list
  const loadNormsList = async () => {
    try {
      setNormsLoading(true);
      
      // Build query parameters
      const params: any = {};
      if (categoryFilter) params.category = categoryFilter;
      if (statusFilter) params.status = statusFilter;
      if (typeFilter) params.type = typeFilter;
      if (search) params.search = search;
      params.page = page;
      params.limit = limit;
      
      // Call the actual API endpoint
      const response = await apiService.getNormsList(params);
      
      setNormsData(response.data);
      setTotalCount(response.pagination.total);
      
      // Load summary counts
      const summaryResponse = await apiService.getNormsSummary();
      setActualCount(summaryResponse.actual);
      setOutdatedCount(summaryResponse.outdated);
    } catch (error) {
      console.error('Failed to load norms list:', error);
      message.error('Не удалось загрузить перечень НТД');
    } finally {
      setNormsLoading(false);
    }
  };

  // Handle search with debounce
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      setPage(1);
      loadNormsList();
    }, 500);
    
    return () => clearTimeout(timeoutId);
  }, [search, categoryFilter, typeFilter, statusFilter]);

  // Load norms list when page changes
  useEffect(() => {
    if (activeTab === 'norms') {
      loadNormsList();
    }
  }, [page, activeTab]);

  // Handle manual norms update
  const updateNormsNow = async () => {
    try {
      setUpdating(true);
      // Call the actual API endpoint
      const response = await apiService.updateNorms({
        categories: categoryFilter ? [categoryFilter] : undefined,
        force: false
      });
      
      message.success(response.message || 'Нормы успешно обновлены!');
      loadNormsList(); // Refresh the list
    } catch (error: any) {
      console.error('Ошибка обновления норм:', error);
      message.error(error.message || 'Не удалось обновить нормы');
    } finally {
      setUpdating(false);
    }
  };

  // Handle export
  const exportNorms = async (format: string) => {
    try {
      message.loading('Экспортируем перечень НТД...');
      
      // Call the actual API endpoint
      const response = await apiService.exportNorms({
        format: format,
        category: categoryFilter || undefined,
        status: statusFilter || undefined,
        type: typeFilter || undefined,
        search: search || undefined
      });
      
      // Create a blob URL and trigger download
      const url = window.URL.createObjectURL(new Blob([response]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `ntd_list_${format}_${new Date().toISOString().split('T')[0]}.${format === 'csv' ? 'csv' : 'xlsx'}`);
      document.body.appendChild(link);
      link.click();
      
      // Clean up
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      message.success('Экспортировано успешно!');
    } catch (error) {
      console.error('Ошибка экспорта норм:', error);
      message.error('Не удалось экспортировать перечень НТД');
    }
  };

  // Handle attaching letter to project
  const attachToProject = async (projectId: string, letterText: string) => {
    if (!projectId) {
      message.warning('Выберите проект для сохранения');
      return;
    }
    
    if (!letterText) {
      message.warning('Нет текста письма для сохранения');
      return;
    }
    
    try {
      // Save the letter as a project result
      await apiService.saveProjectResult(projectId, 'letter', {
        content: letterText,
        generated_at: new Date().toISOString(),
        tone: tone,
        dryness: dryness,
        humanity: humanity,
        length: length,
        formality: formality
      });
      message.success('Письмо сохранено в проект');
    } catch (error) {
      console.error('Ошибка сохранения письма в проект:', error);
      message.error('Не удалось сохранить письмо в проект');
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card title="Pro Tools для Строительных Проектов" bordered={false}>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          {/* Official Letters Tab */}
          <TabPane tab="Официальные Письма" key="letters">
            <Card title="Генератор Официальных Писем (LM Studio)" size="small" data-cy="letter-gen">
              <Form layout="vertical" onFinish={handleGenerateAdvancedLetter} form={letterForm}>
                <Form.Item name="project_id" label="Проект (авто-данные)">
                  <Select 
                    showSearch 
                    onChange={handleProjectSelect} 
                    placeholder="Выберите для нарушений/деталей" 
                    data-cy="letter-project"
                  >
                    {projects.map(p => (
                      <Option key={p.id} value={p.id}>
                        {p.name} ({p.files_count} файлов)
                      </Option>
                    ))}
                  </Select>
                </Form.Item>

                <Form.Item 
                  name="template_id" 
                  label="Шаблон" 
                  rules={[{ required: true }]}
                >
                  <Select 
                    onChange={loadTemplate} 
                    placeholder="Выберите шаблон" 
                    data-cy="letter-template"
                    loading={templatesLoading}
                  >
                    {templates.map(t => (
                      <Option key={t.id} value={t.id}>
                        {t.name} ({t.category})
                      </Option>
                    ))}
                  </Select>
                </Form.Item>

                <Form.Item name="description" label="Краткое Описание Проблемы">
                  <Input.TextArea 
                    rows={4} 
                    placeholder="e.g., Нарушение cl.5.2 СП31 в бетоне, задержка тендера FZ-44" 
                    data-cy="letter-desc" 
                  />
                </Form.Item>

                <Form.Item name="draft" label="Черновик для Улучшения (опционально)">
                  <Input.TextArea 
                    rows={6} 
                    placeholder="Ваш текст письма для редактирования/дополнения" 
                    data-cy="letter-draft" 
                  />
                </Form.Item>

                <Divider>Настройки Стиля</Divider>
                <Row gutter={16}>
                  <Col span={6}>
                    <Form.Item label="Тон (Жесткий - Лояльный)">
                      <Slider 
                        min={-1} 
                        max={1} 
                        step={0.1} 
                        defaultValue={0} 
                        onChange={setTone} 
                        tooltip={{ open: true, formatter: v => v !== undefined && v < 0 ? `Жесткий ${v}` : v !== undefined && v > 0 ? `Лояльный ${v}` : 'Нейтральный' }} 
                        data-cy="tone-slider" 
                      />
                    </Form.Item>
                  </Col>
                  <Col span={6}>
                    <Form.Item label="Сухость (Живой - Сухой)">
                      <Slider 
                        min={0} 
                        max={1} 
                        step={0.1} 
                        defaultValue={0.5} 
                        onChange={setDryness} 
                        tooltip={{ formatter: v => v !== undefined ? `Сухость ${v.toFixed(1)}` : '' }} 
                        data-cy="dryness-slider" 
                      />
                    </Form.Item>
                  </Col>
                  <Col span={6}>
                    <Form.Item label="Человечность (Робот - Natural)">
                      <Slider 
                        min={0} 
                        max={1} 
                        step={0.1} 
                        defaultValue={0.7} 
                        onChange={setHumanity} 
                        tooltip={{ formatter: v => v !== undefined ? `Человечность ${v.toFixed(1)}` : '' }} 
                        data-cy="humanity-slider" 
                      />
                    </Form.Item>
                  </Col>
                  <Col span={6}>
                    <Form.Item label="Длина">
                      <Select 
                        defaultValue="medium" 
                        onChange={setLength} 
                        data-cy="length-select"
                      >
                        <Option value="short">Короткое (&lt;300 слов)</Option>
                        <Option value="medium">Среднее (500 слов)</Option>
                        <Option value="long">Длинное (&gt;800 слов)</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                </Row>

                <Form.Item name="formality" label="Формальность">
                  <Select 
                    defaultValue="formal" 
                    onChange={setFormality} 
                    data-cy="formality-select"
                  >
                    <Option value="formal">Формальный</Option>
                    <Option value="informal">Неформальный</Option>
                  </Select>
                </Form.Item>

                <Form.Item 
                  name="recipient" 
                  label="Получатель" 
                >
                  <Input placeholder="e.g., ООО СтройПроект" data-cy="recipient" />
                </Form.Item>

                <Form.Item name="sender" label="Отправитель">
                  <Input defaultValue="АО БЛДР" data-cy="sender" />
                </Form.Item>

                <Form.Item name="subject" label="Тема">
                  <Input placeholder="e.g., Соответствие СП31" data-cy="subject" />
                </Form.Item>

                <Space>
                  <Button 
                    type="primary" 
                    htmlType="submit" 
                    loading={loading} 
                    data-cy="generate-letter"
                  >
                    Сгенерировать Письмо
                  </Button>
                  <Button onClick={loadTemplates}>Обновить Шаблоны</Button>
                </Space>
              </Form>

              {templates.length === 0 && <Spin tip="Загрузка шаблонов..." />}

              {letterText && (
                <div style={{ marginTop: 20 }}>
                  <Divider>Сгенерированное Письмо</Divider>
                  <Input.TextArea 
                    value={letterText} 
                    rows={10} 
                    readOnly 
                    placeholder="Здесь текст письма" 
                    data-cy="letter-output" 
                  />
                  <p data-cy="tokens-info">Токены: {letterTokens}</p>
                  <Space>
                    <Button 
                      type="primary" 
                      onClick={() => downloadLetter('docx')} 
                      icon={<FilePdfOutlined />} 
                      data-cy="download-docx"
                    >
                      Скачать DOCX
                    </Button>
                    <Button 
                      onClick={() => downloadLetter('pdf')} 
                      icon={<DownloadOutlined />} 
                      data-cy="download-pdf"
                    >
                      PDF
                    </Button>
                    <Button 
                      onClick={() => {
                        const projectId = letterForm.getFieldValue('project_id');
                        attachToProject(projectId, letterText);
                      }} 
                      data-cy="save-project"
                    >
                      Сохранить в Проект
                    </Button>
                    <Button 
                      onClick={() => letterForm.setFieldsValue({ draft: letterText })}
                    >
                      Редактировать
                    </Button>
                  </Space>
                </div>
              )}
            </Card>
          </TabPane>

          {/* Norms Management Tab */}
          <TabPane tab="Управление Нормами" key="norms">
            <Card title="Перечень НТД" size="small" data-cy="norms-list-card">
              <Row gutter={16} style={{ marginBottom: 16 }}>
                <Col span={6}>
                  <Input.Search 
                    placeholder="Поиск по ID/названию" 
                    onSearch={(value) => setSearch(value)} 
                    data-cy="norms-search" 
                  />
                </Col>
                <Col span={6}>
                  <Select 
                    value={categoryFilter} 
                    onChange={(value) => setCategoryFilter(value)} 
                    placeholder="Категория" 
                    style={{ width: '100%' }} 
                    data-cy="category-filter"
                  >
                    <Option value="">Все</Option>
                    <Option value="construction">Строительство</Option>
                    <Option value="finance">Финансы</Option>
                    <Option value="safety">Безопасность</Option>
                    <Option value="ecology">Экология</Option>
                    <Option value="hr">Кадры</Option>
                    <Option value="other">Другое</Option>
                  </Select>
                </Col>
                <Col span={6}>
                  <Select 
                    value={typeFilter} 
                    onChange={(value) => setTypeFilter(value)} 
                    placeholder="Тип" 
                    style={{ width: '100%' }} 
                    data-cy="type-filter"
                  >
                    <Option value="">Все</Option>
                    <Option value="mandatory">Обязательная</Option>
                    <Option value="recommended">Рекомендуемая</Option>
                    <Option value="methodical">Методическая</Option>
                    <Option value="textbook">Учебник</Option>
                  </Select>
                </Col>
                <Col span={6}>
                  <Select 
                    value={statusFilter} 
                    onChange={(value) => setStatusFilter(value)} 
                    placeholder="Статус" 
                    style={{ width: '100%' }} 
                    data-cy="status-filter"
                  >
                    <Option value="">Все</Option>
                    <Option value="actual">Актуальная</Option>
                    <Option value="outdated">Устаревшая</Option>
                    <Option value="pending">На проверке</Option>
                  </Select>
                </Col>
              </Row>
              
              <Table 
                dataSource={normsData} 
                columns={[
                  { title: 'ID Док', dataIndex: 'id', key: 'id', sorter: true },
                  { title: 'Название', dataIndex: 'name', key: 'name', ellipsis: true },
                  { 
                    title: 'Категория', 
                    dataIndex: 'category', 
                    key: 'category', 
                    render: (cat: string) => (
                      <Tag color={cat === 'construction' ? 'blue' : 'green'}>
                        {cat}
                      </Tag>
                    )
                  },
                  { 
                    title: 'Тип', 
                    dataIndex: 'type', 
                    key: 'type', 
                    render: (type: string) => (
                      <Tag color={type === 'mandatory' ? 'red' : 'orange'}>
                        {type === 'mandatory' ? 'Обязательная' : 
                         type === 'recommended' ? 'Рекомендуемая' : 
                         type === 'methodical' ? 'Методическая' : 'Учебник'}
                      </Tag>
                    )
                  },
                  { 
                    title: 'Статус', 
                    dataIndex: 'status', 
                    key: 'status', 
                    render: (s: string) => (
                      <Tag color={s === 'actual' ? 'green' : s === 'outdated' ? 'red' : 'yellow'}>
                        {s === 'actual' ? 'Актуальная' : 
                         s === 'outdated' ? 'Устаревшая' : 'На проверке'}
                      </Tag>
                    )
                  },
                  { 
                    title: 'Дата Выхода', 
                    dataIndex: 'issue_date', 
                    key: 'issue_date', 
                    render: (date: string) => new Date(date).toLocaleDateString('ru') 
                  },
                  { 
                    title: 'Дата Проверки', 
                    dataIndex: 'check_date', 
                    key: 'check_date', 
                    render: (date: string) => new Date(date).toLocaleDateString('ru') 
                  },
                  { title: 'Источник', dataIndex: 'source', key: 'source' },
                  { 
                    title: 'Ссылка', 
                    dataIndex: 'link', 
                    key: 'link', 
                    render: (link: string) => (
                      <a href={link} target="_blank" rel="noopener noreferrer">Скачать</a>
                    )
                  },
                  { title: 'Описание', dataIndex: 'description', key: 'description', ellipsis: true },
                  { 
                    title: 'Нарушений (RAG)', 
                    dataIndex: 'violations_count', 
                    key: 'violations_count', 
                    sorter: true 
                  }
                ]} 
                pagination={{
                  pageSize: 20, 
                  total: totalCount, 
                  current: page,
                  onChange: (newPage) => setPage(newPage)
                }} 
                loading={normsLoading} 
                size="small" 
                data-cy="norms-table" 
                scroll={{ x: 1200 }} 
              />
              
              <Row style={{ marginTop: 16 }}>
                <Col>
                  <Button 
                    onClick={updateNormsNow} 
                    loading={updating} 
                    data-cy="update-norms"
                  >
                    Обновить Перечень
                  </Button>
                  <Button 
                    onClick={() => exportNorms('csv')} 
                    icon={<DownloadOutlined />} 
                    data-cy="export-csv"
                  >
                    CSV
                  </Button>
                  <Button 
                    onClick={() => exportNorms('excel')} 
                    data-cy="export-excel"
                  >
                    Excel
                  </Button>
                </Col>
                <Col span={12} offset={6} style={{ textAlign: 'right' }}>
                  <p data-cy="summary">
                    Всего: {totalCount}, Актуальных: {actualCount}, Устаревших: {outdatedCount}
                  </p>
                </Col>
              </Row>
            </Card>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default AdvancedLetterGeneration;