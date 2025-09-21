import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Form, 
  Input, 
  Button, 
  Upload, 
  Tabs, 
  Table, 
  message, 
  Spin, 
  Select, 
  Row, 
  Col,
  Divider,
  Descriptions,
  Tag,
  UploadProps,
  Modal,
  Progress,
  Statistic,
  List,
  Typography,
  Switch,
  DatePicker,
  Slider,
  Collapse,
  Checkbox,
  InputNumber,
  Space,
  Alert
} from 'antd';
import { 
  UploadOutlined, 
  FilePdfOutlined, 
  FileExcelOutlined, 
  DownloadOutlined, 
  FileImageOutlined, 
  PlusOutlined, 
  SyncOutlined, 
  ClockCircleOutlined, 
  CheckCircleOutlined, 
  CloseCircleOutlined, 
  FolderOpenOutlined,
  FileTextOutlined,
  EditOutlined,
  SaveOutlined,
  EyeOutlined,
  PrinterOutlined,
  ReloadOutlined,
  SettingOutlined,
  CloudDownloadOutlined,
  CloudUploadOutlined,
  DatabaseOutlined,
  BarChartOutlined,
  ScheduleOutlined,
  DollarCircleOutlined,
  FileDoneOutlined,
  FileSearchOutlined,
  FileProtectOutlined,
  FileSyncOutlined,
  FileAddOutlined,
  FileUnknownOutlined,
  FileZipOutlined,
  FilePptOutlined,
  FileWordOutlined,
  FileMarkdownOutlined,
  FileExclamationOutlined
} from '@ant-design/icons';
import type { UploadProps as AntdUploadProps } from 'antd';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line, AreaChart, Area } from 'recharts';
import { apiService, LetterData, BudgetData, PPRData, TenderData, LetterResponse, BudgetResponse, PPRResponse, TenderResponse, Project, Template, AdvancedLetterData } from '../services/api';
import { useStore } from '../store';

const { TabPane } = Tabs;
const { Option } = Select;
const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;

const ProFeatures: React.FC = () => {
  const [activeTab, setActiveTab] = useState('letters');
  const [loading, setLoading] = useState(false);
  const [letterForm] = Form.useForm();
  const [budgetForm] = Form.useForm();
  const [pprForm] = Form.useForm();
  const [tenderForm] = Form.useForm();
  const [bimForm] = Form.useForm();
  const [dwgForm] = Form.useForm();
  const [monteCarloForm] = Form.useForm();
  const [estimateForm] = Form.useForm();
  const [letterDraftForm] = Form.useForm();
  
  // Project integration state
  const [selectedProject, setSelectedProject] = useState<string | null>(null);
  const [projectFiles, setProjectFiles] = useState<any[]>([]);
  const [isProjectLoading, setIsProjectLoading] = useState(false);
  
  // Add new state for project results
  const [projectResults, setProjectResults] = useState<any[]>([]);
  const [isResultsLoading, setIsResultsLoading] = useState(false);
  
  // Tool responses
  const [letterResponse, setLetterResponse] = useState<LetterResponse | null>(null);
  const [budgetResponse, setBudgetResponse] = useState<BudgetResponse | null>(null);
  const [pprResponse, setPprResponse] = useState<PPRResponse | null>(null);
  const [tenderResponse, setTenderResponse] = useState<TenderResponse | null>(null);
  const [bimResponse, setBimResponse] = useState<any | null>(null);
  const [dwgResponse, setDwgResponse] = useState<any | null>(null);
  const [monteCarloResponse, setMonteCarloResponse] = useState<any | null>(null);
  const [batchEstimateResults, setBatchEstimateResults] = useState<any>(null);
  
  // File lists
  const [estimateFileList, setEstimateFileList] = useState<any[]>([]);
  const [fileList, setFileList] = useState<any[]>([]);
  
  // Chart data
  const [budgetChartData, setBudgetChartData] = useState<any[]>([]);
  const [pprGanttData, setPprGanttData] = useState<any[]>([]);
  const [monteCarloChartData, setMonteCarloChartData] = useState<any[]>([]);
  
  // Advanced letter generation state
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
  
  // State for pro metrics from dashboard
  const [proMetrics, setProMetrics] = useState({
    budgetProfit: 0,
    budgetROI: 0,
    projectCount: 0,
    complianceRate: 0
  });
  
  // Get projects from store
  const { projects, fetchProjects } = useStore();

  // Load projects on component mount
  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  // Calculate real metrics from projects
  useEffect(() => {
    if (projects && projects.length > 0) {
      // Calculate real metrics
      const projectCount = projects.length;
      let totalProfit = 0;
      let totalROI = 0;
      let complianceCount = 0;
      let totalComplianceChecks = 0;
      
      projects.forEach(project => {
        // Add project profit (if available)
        totalProfit += project.roi > 0 ? (project.roi / 100) * 1000000 : 0; // Estimate based on ROI
        
        // Add project ROI
        totalROI += project.roi || 0;
        
        // Estimate compliance (using files count as a proxy)
        complianceCount += project.files_count || 0;
        totalComplianceChecks += project.files_count ? project.files_count + 10 : 10; // Base value
      });
      
      const avgROI = projectCount > 0 ? totalROI / projectCount : 0;
      const complianceRate = totalComplianceChecks > 0 ? Math.min(100, (complianceCount / totalComplianceChecks) * 100) : 0;
      
      setProMetrics({
        budgetProfit: totalProfit,
        budgetROI: Math.round(avgROI),
        projectCount,
        complianceRate: Math.round(complianceRate)
      });
    }
  }, [projects]);

  // Handle project selection with results loading
  const handleProjectSelect = async (projectId: string) => {
    setSelectedProject(projectId);
    
    if (projectId) {
      setIsProjectLoading(true);
      try {
        // Fetch project files from the backend
        const files = await apiService.getProjectFiles(projectId);
        setProjectFiles(files);
        message.info(`Загружено из проекта: ${files.length} файлов`);
        
        // Fetch project results
        setIsResultsLoading(true);
        try {
          const results = await apiService.getProjectResults(projectId);
          setProjectResults(results);
        } catch (error) {
          console.error('Error loading project results:', error);
        } finally {
          setIsResultsLoading(false);
        }
      } catch (error) {
        console.error('Error loading project files:', error);
        message.error('Не удалось загрузить файлы проекта');
      } finally {
        setIsProjectLoading(false);
      }
    } else {
      setProjectFiles([]);
      setProjectResults([]);
    }
  };

  // Generate official letter
  const handleGenerateLetter = async (values: any) => {
    // Check authentication token first
    const { user } = useStore.getState();
    const token = user?.token || localStorage.getItem('token');
    if (!token) {
      message.error('Нет токена аутентификации. Войдите в систему.');
      return;
    }
    
    // Validate minimum required fields
    if (!values.description) {
      message.error('Поле "Описание проблемы" обязательно для заполнения');
      return;
    }
    
    setLoading(true);
    try {
      // Check if this is an advanced letter generation (has description field)
      if (values.description) {
        // This is an advanced letter generation - only description is required
        const letterData: AdvancedLetterData = {
          description: values.description, // REQUIRED field
          template_id: values.template_id || 'compliance_sp31',
          project_id: values.project_id || undefined,
          tone: values.tone || 0,
          dryness: values.dryness || 0.5,
          humanity: values.humanity || 0.7,
          length: values.length || 'medium',
          formality: values.formality || 'formal',
          recipient: values.recipient || '', // Optional
          sender: values.sender || 'АО БЛДР', // Optional
          subject: values.subject || 'Официальное письмо' // Optional
        };
        
        const response = await apiService.generateAdvancedLetter(letterData);
        setLetterResponse(response);
        {
          const { ok, error } = (response?.status ? { ok: response.status === 'success', error: response.error || response.message } : { ok: true, error: null });
          if (ok) message.success('Письмо успешно сгенерировано');
          else message.error(String(error || 'Ошибка генерации письма'));
        }
      } else {
        // This is a regular letter generation
        const letterData: LetterData = {
          template: values.template,
          recipient: values.recipient,
          sender: values.sender,
          subject: values.subject,
          compliance_details: values.compliance_details,
          violations: values.violations
        };
        
        const response = await apiService.generateLetter(letterData);
        setLetterResponse(response);
        {
          const { ok, error } = (response?.status ? { ok: response.status === 'success', error: response.error || response.message } : { ok: true, error: null });
          if (ok) message.success('Письмо успешно сгенерировано');
          else message.error(String(error || 'Ошибка генерации письма'));
        }
      }
    } catch (error: any) {
      console.error('Error generating letter:', error);
      message.error(error.response?.data?.error || 'Ошибка генерации письма');
    } finally {
      setLoading(false);
    }
  };

  // Auto budget calculation
  const handleAutoBudget = async (values: any) => {
    setLoading(true);
    try {
      const budgetData: BudgetData = {
        project_name: values.project_name,
        positions: values.positions || [],
        regional_coefficients: {},
        overheads_percentage: values.overheads_percentage || 15,
        profit_percentage: values.profit_percentage || 10
      };
      
      const response = await apiService.autoBudget(budgetData);
      setBudgetResponse(response);
      {
        const ok = response?.status ? response.status === 'success' : true;
        if (ok) {
          const chartData = (response.budget?.sections || []).map((section: any) => ({
            name: section.position_code,
            cost: section.total_cost
          }));
          setBudgetChartData(chartData);
          message.success('Смета успешно рассчитана');
        } else {
          message.error(response.error || 'Ошибка расчета сметы');
        }
      }
    } catch (error: any) {
      console.error('Error calculating budget:', error);
      message.error(error.response?.data?.error || 'Ошибка расчета сметы');
    } finally {
      setLoading(false);
    }
  };

  // Generate PPR
  const handleGeneratePPR = async (values: any) => {
    setLoading(true);
    try {
      const pprData: PPRData = {
        project_name: values.project_name,
        project_code: values.project_code,
        location: values.location,
        client: values.client,
        works_seq: values.works_seq || []
      };
      
      const response = await apiService.generatePPR(pprData);
      setPprResponse(response);
      {
        const ok = response?.status ? response.status === 'success' : true;
        if (ok) message.success('ППР успешно сгенерирован');
        else message.error(response.error || 'Ошибка генерации ППР');
      }
    } catch (error: any) {
      console.error('Error generating PPR:', error);
      message.error(error.response?.data?.error || 'Ошибка генерации ППР');
    } finally {
      setLoading(false);
    }
  };

  // Analyze tender
  const handleAnalyzeTender = async (values: any) => {
    setLoading(true);
    try {
      // Validate that we have tender data
      const tenderData = values.tender_file || values.tender_text || values.tender_url;
      if (!tenderData) {
        message.error('Загрузите файл тендера или укажите данные');
        setLoading(false);
        return;
      }
      
      // Prepare request data with required tender_data field
      const requestData = {
        tender_data: {
          id: values.tender_id || Date.now().toString(),
          name: values.tender_name || 'Анализ тендера',
          project_id: values.project_id || 'Not specified',
          data: tenderData,
          analysis_type: values.analysis_type || 'full',
          budget_limit: values.budget_limit || 0
        }
      };

      const response = await apiService.analyzeTender(requestData);
      setTenderResponse(response);
      {
        const ok = response?.status ? response.status === 'success' : true;
        if (ok) message.success('Анализ тендера выполнен успешно');
        else message.error(response.error || 'Ошибка анализа тендера');
      }
    } catch (error: any) {
      console.error('Error analyzing tender:', error);
      message.error(error.response?.data?.error || 'Ошибка анализа тендера');
    } finally {
      setLoading(false);
    }
  };

  // File upload props
  const uploadProps: UploadProps = {
    onRemove: (file) => {
      const index = fileList.indexOf(file);
      const newFileList = fileList.slice();
      newFileList.splice(index, 1);
      setFileList(newFileList);
    },
    beforeUpload: (file) => {
      setFileList([...fileList, file]);
      return false;
    },
    fileList,
  };

  // Estimate file upload props
  const estimateUploadProps: UploadProps = {
    onRemove: (file) => {
      const index = estimateFileList.indexOf(file);
      const newFileList = estimateFileList.slice();
      newFileList.splice(index, 1);
      setEstimateFileList(newFileList);
    },
    beforeUpload: (file) => {
      setEstimateFileList([...estimateFileList, file]);
      return false;
    },
    fileList: estimateFileList,
  };

  // Render letter generation form
  const renderLetterForm = () => (
    <Card title="Генерация официального письма" style={{ marginBottom: 24 }}>
      <Form
        form={letterForm}
        layout="vertical"
        onFinish={handleGenerateLetter}
        initialValues={{
          template: 'compliance_sp31',
          sender: 'АО БЛДР',
          subject: 'Официальное письмо'
        }}
      >
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="template"
              label="Шаблон"
              rules={[{ required: true, message: 'Пожалуйста, выберите шаблон' }]}
            >
              <Select placeholder="Выберите шаблон">
                <Option value="compliance_sp31">Соответствие СП31</Option>
                <Option value="budget_approval">Согласование сметы</Option>
                <Option value="work_completion">Выполнение работ</Option>
                <Option value="technical_spec">Технические спецификации</Option>
                <Option value="contract_proposal">Договорное предложение</Option>
              </Select>
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="recipient"
              label="Получатель"
              rules={[{ required: true, message: 'Пожалуйста, укажите получателя' }]}
            >
              <Input placeholder="Кому адресовано письмо" />
            </Form.Item>
          </Col>
        </Row>
        
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="sender"
              label="Отправитель"
            >
              <Input placeholder="Кто отправляет письмо" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="subject"
              label="Тема"
              rules={[{ required: true, message: 'Пожалуйста, укажите тему' }]}
            >
              <Input placeholder="Тема письма" />
            </Form.Item>
          </Col>
        </Row>
        
        <Form.Item
          name="compliance_details"
          label="Детали соответствия"
        >
          <Input.TextArea rows={4} placeholder="Подробности соответствия требованиям" />
        </Form.Item>
        
        <Form.Item
          name="violations"
          label="Нарушения"
        >
          <Input.TextArea rows={4} placeholder="Выявленные нарушения (если есть)" />
        </Form.Item>
        
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>
            Сгенерировать письмо
          </Button>
        </Form.Item>
      </Form>
      
      {letterResponse && (
        <Card title="Результат" size="small" style={{ marginTop: 24 }}>
          <Descriptions column={1}>
            <Descriptions.Item label="Статус">{letterResponse.status}</Descriptions.Item>
            <Descriptions.Item label="Сообщение">{letterResponse.message}</Descriptions.Item>
            {letterResponse.file_path && (
              <Descriptions.Item label="Файл">
                <a href={letterResponse.file_path} download>Скачать письмо</a>
              </Descriptions.Item>
            )}
          </Descriptions>
          {letterResponse.letter && (
            <div style={{ marginTop: 16 }}>
              <Divider>Текст письма</Divider>
              <Paragraph style={{ whiteSpace: 'pre-wrap' }}>
                {letterResponse.letter}
              </Paragraph>
            </div>
          )}
        </Card>
      )}
    </Card>
  );

  // Render budget calculation form
  const renderBudgetForm = () => (
    <Card title="Автоматический расчет сметы" style={{ marginBottom: 24 }}>
      <Form
        form={budgetForm}
        layout="vertical"
        onFinish={handleAutoBudget}
        initialValues={{
          overheads_percentage: 15,
          profit_percentage: 10
        }}
      >
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="project_name"
              label="Название проекта"
              rules={[{ required: true, message: 'Пожалуйста, укажите название проекта' }]}
            >
              <Input placeholder="Название проекта" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="region"
              label="Регион"
            >
              <Select placeholder="Выберите регион">
                <Option value="ekaterinburg">Екатеринбург</Option>
                <Option value="moscow">Москва</Option>
                <Option value="novosibirsk">Новосибирск</Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>
        
        <Divider>Позиции сметы</Divider>
        <Form.List name="positions">
          {(fields, { add, remove }) => (
            <>
              {fields.map(({ key, name, ...restField }) => (
                <Card key={key} size="small" style={{ marginBottom: 16 }}>
                  <Row gutter={16}>
                    <Col span={6}>
                      <Form.Item
                        {...restField}
                        name={[name, 'code']}
                        label="Код"
                      >
                        <Input placeholder="Код позиции" />
                      </Form.Item>
                    </Col>
                    <Col span={6}>
                      <Form.Item
                        {...restField}
                        name={[name, 'name']}
                        label="Наименование"
                      >
                        <Input placeholder="Наименование" />
                      </Form.Item>
                    </Col>
                    <Col span={4}>
                      <Form.Item
                        {...restField}
                        name={[name, 'unit']}
                        label="Ед. изм."
                      >
                        <Input placeholder="Ед. изм." />
                      </Form.Item>
                    </Col>
                    <Col span={4}>
                      <Form.Item
                        {...restField}
                        name={[name, 'quantity']}
                        label="Количество"
                      >
                        <InputNumber style={{ width: '100%' }} placeholder="Количество" />
                      </Form.Item>
                    </Col>
                    <Col span={4}>
                      <Form.Item
                        {...restField}
                        name={[name, 'unit_cost']}
                        label="Цена за ед."
                      >
                        <InputNumber style={{ width: '100%' }} placeholder="Цена" />
                      </Form.Item>
                    </Col>
                  </Row>
                  <Button onClick={() => remove(name)} danger>Удалить</Button>
                </Card>
              ))}
              <Form.Item>
                <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                  Добавить позицию
                </Button>
              </Form.Item>
            </>
          )}
        </Form.List>
        
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="overheads_percentage"
              label="Накладные расходы (%)"
            >
              <Slider min={0} max={30} step={0.5} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="profit_percentage"
              label="Прибыль (%)"
            >
              <Slider min={0} max={30} step={0.5} />
            </Form.Item>
          </Col>
        </Row>
        
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>
            Рассчитать смету
          </Button>
        </Form.Item>
      </Form>
      
      {budgetResponse && (
        <Card title="Результат расчета" size="small" style={{ marginTop: 24 }}>
          <Descriptions column={2}>
            <Descriptions.Item label="Статус">{budgetResponse.status}</Descriptions.Item>
            <Descriptions.Item label="Общая стоимость">
              {budgetResponse.total_cost?.toLocaleString()} руб.
            </Descriptions.Item>
            {budgetResponse.budget && (
              <>
                <Descriptions.Item label="Накладные расходы">
                  {budgetResponse.budget.overheads?.toLocaleString()} руб.
                </Descriptions.Item>
                <Descriptions.Item label="Прибыль">
                  {budgetResponse.budget.profit?.toLocaleString()} руб.
                </Descriptions.Item>
                <Descriptions.Item label="ROI">
                  {budgetResponse.budget.roi?.toFixed(2)}%
                </Descriptions.Item>
              </>
            )}
          </Descriptions>
          
          {budgetChartData.length > 0 && (
            <div style={{ marginTop: 24 }}>
              <Divider>График стоимости по позициям</Divider>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={budgetChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip formatter={(value) => [`${value.toLocaleString()} руб.`, 'Стоимость']} />
                  <Legend />
                  <Bar dataKey="cost" name="Стоимость" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </Card>
      )}
    </Card>
  );

  // Render PPR generation form
  const renderPPRForm = () => (
    <Card title="Генерация проекта производства работ (ППР)" style={{ marginBottom: 24 }}>
      <Form
        form={pprForm}
        layout="vertical"
        onFinish={handleGeneratePPR}
        initialValues={{
          location: 'Екатеринбург'
        }}
      >
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="project_name"
              label="Название проекта"
              rules={[{ required: true, message: 'Пожалуйста, укажите название проекта' }]}
            >
              <Input placeholder="Название проекта" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="project_code"
              label="Код проекта"
            >
              <Input placeholder="Код проекта" />
            </Form.Item>
          </Col>
        </Row>
        
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="location"
              label="Местоположение"
            >
              <Input placeholder="Местоположение" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="client"
              label="Заказчик"
            >
              <Input placeholder="Заказчик" />
            </Form.Item>
          </Col>
        </Row>
        
        <Divider>Этапы работ</Divider>
        <Form.List name="works_seq">
          {(fields, { add, remove }) => (
            <>
              {fields.map(({ key, name, ...restField }) => (
                <Card key={key} size="small" style={{ marginBottom: 16 }}>
                  <Row gutter={16}>
                    <Col span={8}>
                      <Form.Item
                        {...restField}
                        name={[name, 'name']}
                        label="Название"
                      >
                        <Input placeholder="Название этапа" />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item
                        {...restField}
                        name={[name, 'description']}
                        label="Описание"
                      >
                        <Input placeholder="Описание этапа" />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item
                        {...restField}
                        name={[name, 'duration']}
                        label="Длительность (дни)"
                      >
                        <InputNumber style={{ width: '100%' }} placeholder="Длительность" />
                      </Form.Item>
                    </Col>
                  </Row>
                  <Form.Item
                    {...restField}
                    name={[name, 'deps']}
                    label="Зависимости"
                  >
                    <Select mode="tags" placeholder="Выберите зависимости" />
                  </Form.Item>
                  <Button onClick={() => remove(name)} danger>Удалить</Button>
                </Card>
              ))}
              <Form.Item>
                <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                  Добавить этап
                </Button>
              </Form.Item>
            </>
          )}
        </Form.List>
        
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>
            Сгенерировать ППР
          </Button>
        </Form.Item>
      </Form>
      
      {pprResponse && (
        <Card title="Результат" size="small" style={{ marginTop: 24 }}>
          <Descriptions column={2}>
            <Descriptions.Item label="Статус">{pprResponse.status}</Descriptions.Item>
            <Descriptions.Item label="Количество этапов">
              {pprResponse.stages_count}
            </Descriptions.Item>
            <Descriptions.Item label="Сообщение">{pprResponse.message}</Descriptions.Item>
          </Descriptions>
        </Card>
      )}
    </Card>
  );

  // Render tender analysis form
  const renderTenderAnalysisForm = () => (
    <Card title="Анализ тендера" style={{ marginBottom: 24 }}>
      <Form
        form={tenderForm}
        layout="vertical"
        onFinish={handleAnalyzeTender}
      >
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="project_id"
              label="Проект"
            >
              <Select 
                placeholder="Выберите проект" 
                onChange={handleProjectSelect}
                value={selectedProject}
              >
                {projects.map(project => (
                  <Option key={project.id} value={project.id}>
                    {project.name}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="tender_name"
              label="Название тендера"
              rules={[{ required: true, message: 'Пожалуйста, укажите название тендера' }]}
            >
              <Input placeholder="Название тендера" />
            </Form.Item>
          </Col>
        </Row>
        
        <Form.Item
          name="requirements"
          label="Требования"
        >
          <Select 
            mode="tags" 
            placeholder="Введите требования"
            tokenSeparators={[',']}
          >
            <Option value="Соответствие СП">Соответствие СП</Option>
            <Option value="Наличие лицензий">Наличие лицензий</Option>
            <Option value="Опыт работ">Опыт работ</Option>
            <Option value="Финансовая стабильность">Финансовая стабильность</Option>
            <Option value="Качество материалов">Качество материалов</Option>
          </Select>
        </Form.Item>
        
        <Form.Item
          label="Файлы сметы"
        >
          <Upload {...uploadProps}>
            <Button icon={<UploadOutlined />}>Загрузить файлы</Button>
          </Upload>
        </Form.Item>
        
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>
            Проанализировать тендер
          </Button>
        </Form.Item>
      </Form>
      
      {tenderResponse && (
        <Card title="Результат анализа" size="small" style={{ marginTop: 24 }}>
          <Descriptions column={1}>
            <Descriptions.Item label="Статус">{tenderResponse.status}</Descriptions.Item>
            <Descriptions.Item label="Сообщение">{tenderResponse.message}</Descriptions.Item>
          </Descriptions>
          
          {tenderResponse.analysis && (
            <div style={{ marginTop: 16 }}>
              <Divider>Подробный анализ</Divider>
              <Collapse>
                <Panel header="Финансовый анализ" key="1">
                  <Descriptions column={2}>
                    <Descriptions.Item label="ROI">
                      {tenderResponse.analysis.roi?.toFixed(2)}%
                    </Descriptions.Item>
                    <Descriptions.Item label="Прибыль">
                      {tenderResponse.analysis.profit?.toLocaleString()} руб.
                    </Descriptions.Item>
                  </Descriptions>
                </Panel>
                <Panel header="Анализ требований" key="2">
                  {tenderResponse.analysis.requirements_analysis && (
                    <Descriptions column={1}>
                      {Object.entries(tenderResponse.analysis.requirements_analysis).map(([req, analysis]: [string, any]) => (
                        <Descriptions.Item key={req} label={req}>
                          <Tag color={analysis.compliant ? 'green' : 'red'}>
                            {analysis.compliant ? 'Соответствует' : 'Не соответствует'}
                          </Tag>
                        </Descriptions.Item>
                      ))}
                    </Descriptions>
                  )}
                </Panel>
              </Collapse>
            </div>
          )}
        </Card>
      )}
    </Card>
  );

  // Render batch estimate parsing form
  const renderBatchEstimateForm = () => (
    <Card title="Пакетная обработка смет" style={{ marginBottom: 24 }}>
      <Form
        form={estimateForm}
        layout="vertical"
      >
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="project_id"
              label="Проект"
            >
              <Select 
                placeholder="Выберите проект" 
                onChange={handleProjectSelect}
                value={selectedProject}
              >
                {projects.map(project => (
                  <Option key={project.id} value={project.id}>
                    {project.name}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="region"
              label="Регион"
            >
              <Select placeholder="Выберите регион">
                <Option value="ekaterinburg">Екатеринбург</Option>
                <Option value="moscow">Москва</Option>
                <Option value="novosibirsk">Новосибирск</Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>
        
        <Form.Item
          label="Файлы смет"
        >
          <Upload {...estimateUploadProps}>
            <Button icon={<UploadOutlined />}>Загрузить файлы смет</Button>
          </Upload>
        </Form.Item>
        
        <Form.Item>
          <Button type="primary" loading={loading}>
            Обработать сметы
          </Button>
        </Form.Item>
      </Form>
      
      {batchEstimateResults && (
        <Card title="Результаты обработки" size="small" style={{ marginTop: 24 }}>
          <Descriptions column={2}>
            <Descriptions.Item label="Обработано файлов">
              {batchEstimateResults.files_processed}
            </Descriptions.Item>
            <Descriptions.Item label="Общая стоимость">
              {batchEstimateResults.all_totals?.total_cost?.toLocaleString()} руб.
            </Descriptions.Item>
          </Descriptions>
          
          {batchEstimateResults.merged_positions && (
            <Table
              style={{ marginTop: 16 }}
              dataSource={batchEstimateResults.merged_positions}
              columns={[
                {
                  title: 'Код',
                  dataIndex: 'code',
                  key: 'code',
                },
                {
                  title: 'Количество',
                  dataIndex: 'quantity',
                  key: 'quantity',
                },
                {
                  title: 'Общая стоимость',
                  dataIndex: 'total_cost',
                  key: 'total_cost',
                  render: (value: number) => value.toLocaleString() + ' руб.'
                }
              ]}
              pagination={{ pageSize: 10 }}
            />
          )}
        </Card>
      )}
    </Card>
  );

  // Render advanced letter generation form
  const renderAdvancedLetterForm = () => (
    <Card title="Продвинутая генерация писем" style={{ marginBottom: 24 }}>
      <Tabs defaultActiveKey="1">
        <TabPane tab="Новое письмо" key="1">
          <Form
            form={letterForm}
            layout="vertical"
            onFinish={handleGenerateLetter}
          >
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="description"
                  label="Описание проблемы"
                  rules={[{ required: true, message: 'Пожалуйста, опишите проблему' }]}
                >
                  <Input.TextArea rows={4} placeholder="Опишите проблему или ситуацию" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="template_id"
                  label="Шаблон"
                >
                  <Select placeholder="Выберите шаблон">
                    <Option value="compliance_sp31">Соответствие СП31</Option>
                    <Option value="violation_gesn">Нарушения ГЭСН</Option>
                    <Option value="tender_response_fz44">Ответ на тендер ФЗ-44</Option>
                    <Option value="delay_notice">Уведомление о задержке</Option>
                    <Option value="payment_dispute">Спор по оплате</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>
            
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="project_id"
                  label="Проект"
                >
                  <Select 
                    placeholder="Выберите проект" 
                    onChange={handleProjectSelect}
                    value={selectedProject}
                  >
                    {projects.map(project => (
                      <Option key={project.id} value={project.id}>
                        {project.name}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="recipient"
                  label="Получатель"
                >
                  <Input placeholder="Кому адресовано письмо" />
                </Form.Item>
              </Col>
            </Row>
            
            <Divider>Параметры стиля</Divider>
            <Row gutter={16}>
              <Col span={8}>
                <Form.Item
                  label="Тон (-1 жесткий ... +1 лояльный)"
                  name="tone"
                >
                  <Slider 
                    min={-1} 
                    max={1} 
                    step={0.1} 
                    value={tone}
                    onChange={setTone}
                  />
                  <div>Текущее значение: {tone}</div>
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item
                  label="Сухость (0 живой ... 1 сухой)"
                  name="dryness"
                >
                  <Slider 
                    min={0} 
                    max={1} 
                    step={0.1} 
                    value={dryness}
                    onChange={setDryness}
                  />
                  <div>Текущее значение: {dryness}</div>
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item
                  label="Человечность (0 робот ... 1 естественный)"
                  name="humanity"
                >
                  <Slider 
                    min={0} 
                    max={1} 
                    step={0.1} 
                    value={humanity}
                    onChange={setHumanity}
                  />
                  <div>Текущее значение: {humanity}</div>
                </Form.Item>
              </Col>
            </Row>
            
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  label="Длина"
                  name="length"
                >
                  <Select value={length} onChange={setLength}>
                    <Option value="short">Короткое</Option>
                    <Option value="medium">Среднее</Option>
                    <Option value="long">Длинное</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  label="Формальность"
                  name="formality"
                >
                  <Select value={formality} onChange={setFormality}>
                    <Option value="formal">Формальное</Option>
                    <Option value="informal">Неформальное</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>
            
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading}>
                Сгенерировать письмо
              </Button>
            </Form.Item>
          </Form>
        </TabPane>
        
        <TabPane tab="Улучшить черновик" key="2">
          <Form
            form={letterDraftForm}
            layout="vertical"
          >
            <Form.Item
              name="draft"
              label="Черновик письма"
              rules={[{ required: true, message: 'Пожалуйста, введите черновик' }]}
            >
              <Input.TextArea rows={8} placeholder="Введите черновик письма" />
            </Form.Item>
            
            <Form.Item
              name="description"
              label="Описание улучшений"
            >
              <Input.TextArea rows={4} placeholder="Что нужно улучшить в письме" />
            </Form.Item>
            
            <Form.Item>
              <Button type="primary" loading={improveLoading}>
                Улучшить письмо
              </Button>
            </Form.Item>
          </Form>
        </TabPane>
      </Tabs>
      
      {letterResponse && (
        <Card title="Результат" size="small" style={{ marginTop: 24 }}>
          <Descriptions column={1}>
            <Descriptions.Item label="Статус">{letterResponse.status}</Descriptions.Item>
            <Descriptions.Item label="Сообщение">{letterResponse.message}</Descriptions.Item>
            {letterResponse.file_path && (
              <Descriptions.Item label="Файл">
                <a href={letterResponse.file_path} download>Скачать письмо</a>
              </Descriptions.Item>
            )}
          </Descriptions>
          {letterResponse.letter && (
            <div style={{ marginTop: 16 }}>
              <Divider>Текст письма</Divider>
              <Paragraph style={{ whiteSpace: 'pre-wrap' }}>
                {letterResponse.letter}
              </Paragraph>
            </div>
          )}
        </Card>
      )}
    </Card>
  );

  // Render BIM analysis form
  const renderBIMForm = () => (
    <Card title="Анализ BIM модели" style={{ marginBottom: 24 }}>
      <Form
        form={bimForm}
        layout="vertical"
      >
        <Form.Item
          name="ifc_path"
          label="Путь к IFC файлу"
          rules={[{ required: true, message: 'Пожалуйста, укажите путь к IFC файлу' }]}
        >
          <Input placeholder="Путь к IFC файлу" />
        </Form.Item>
        
        <Form.Item
          name="analysis_type"
          label="Тип анализа"
        >
          <Select placeholder="Выберите тип анализа">
            <Option value="clash">Обнаружение коллизий</Option>
            <Option value="validation">Валидация модели</Option>
            <Option value="optimization">Оптимизация</Option>
          </Select>
        </Form.Item>
        
        <Form.Item>
          <Button type="primary" loading={loading}>
            Проанализировать модель
          </Button>
        </Form.Item>
      </Form>
      
      {bimResponse && (
        <Card title="Результаты анализа" size="small" style={{ marginTop: 24 }}>
          <Descriptions column={2}>
            <Descriptions.Item label="Статус">{bimResponse.status}</Descriptions.Item>
            <Descriptions.Item label="Количество элементов">
              {bimResponse.elements_count}
            </Descriptions.Item>
            <Descriptions.Item label="Количество коллизий">
              {bimResponse.clashes?.length || 0}
            </Descriptions.Item>
            <Descriptions.Item label="Сообщение">{bimResponse.message}</Descriptions.Item>
          </Descriptions>
          
          {bimResponse.clashes && bimResponse.clashes.length > 0 && (
            <Table
              style={{ marginTop: 16 }}
              dataSource={bimResponse.clashes}
              columns={[
                {
                  title: 'Тип коллизии',
                  dataIndex: 'type',
                  key: 'type',
                },
                {
                  title: 'Элемент 1',
                  dataIndex: 'element1',
                  key: 'element1',
                },
                {
                  title: 'Элемент 2',
                  dataIndex: 'element2',
                  key: 'element2',
                }
              ]}
              pagination={{ pageSize: 5 }}
            />
          )}
        </Card>
      )}
    </Card>
  );

  // Render DWG export form
  const renderDWGForm = () => (
    <Card title="Экспорт в AutoCAD (DWG)" style={{ marginBottom: 24 }}>
      <Form
        form={dwgForm}
        layout="vertical"
      >
        <Form.Item
          name="dwg_data"
          label="Данные для экспорта"
          rules={[{ required: true, message: 'Пожалуйста, укажите данные для экспорта' }]}
        >
          <Input.TextArea rows={6} placeholder="Введите данные для экспорта в DWG" />
        </Form.Item>
        
        <Form.Item>
          <Button type="primary" loading={loading}>
            Экспортировать в DWG
          </Button>
        </Form.Item>
      </Form>
      
      {dwgResponse && (
        <Card title="Результат экспорта" size="small" style={{ marginTop: 24 }}>
          <Descriptions column={1}>
            <Descriptions.Item label="Статус">{dwgResponse.status}</Descriptions.Item>
            <Descriptions.Item label="Путь к файлу">{dwgResponse.file_path}</Descriptions.Item>
            <Descriptions.Item label="Сообщение">{dwgResponse.message}</Descriptions.Item>
          </Descriptions>
        </Card>
      )}
    </Card>
  );

  // Render Monte Carlo simulation form
  const renderMonteCarloForm = () => (
    <Card title="Монте-Карло симуляция рисков" style={{ marginBottom: 24 }}>
      <Form
        form={monteCarloForm}
        layout="vertical"
      >
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="base_cost"
              label="Базовая стоимость (руб.)"
              rules={[{ required: true, message: 'Пожалуйста, укажите базовую стоимость' }]}
            >
              <InputNumber 
                style={{ width: '100%' }} 
                placeholder="Базовая стоимость" 
                formatter={value => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
                parser={value => value ? parseFloat(value.replace(/\s/g, '')) : 0}
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="profit"
              label="Планируемая прибыль (руб.)"
              rules={[{ required: true, message: 'Пожалуйста, укажите прибыль' }]}
            >
              <InputNumber 
                style={{ width: '100%' }} 
                placeholder="Планируемая прибыль" 
                formatter={value => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
                parser={value => value ? parseFloat(value.replace(/\s/g, '')) : 0}
              />
            </Form.Item>
          </Col>
        </Row>
        
        <Divider>Параметры вариаций</Divider>
        <Row gutter={16}>
          <Col span={8}>
            <Form.Item
              name="cost_variation"
              label="Вариация стоимости (%)"
            >
              <Slider min={0} max={50} step={1} defaultValue={15} />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              name="time_variation"
              label="Вариация сроков (%)"
            >
              <Slider min={0} max={50} step={1} defaultValue={10} />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              name="roi_variation"
              label="Вариация ROI (%)"
            >
              <Slider min={0} max={20} step={0.5} defaultValue={5} />
            </Form.Item>
          </Col>
        </Row>
        
        <Form.Item>
          <Button type="primary" loading={loading}>
            Запустить симуляцию
          </Button>
        </Form.Item>
      </Form>
      
      {monteCarloResponse && (
        <Card title="Результаты симуляции" size="small" style={{ marginTop: 24 }}>
          <Descriptions column={2}>
            <Descriptions.Item label="Статус">{monteCarloResponse.status}</Descriptions.Item>
            <Descriptions.Item label="Средний ROI">
              {monteCarloResponse.roi_stats?.mean?.toFixed(2)}%
            </Descriptions.Item>
            <Descriptions.Item label="ROI (10%)">
              {monteCarloResponse.roi_stats?.p10?.toFixed(2)}%
            </Descriptions.Item>
            <Descriptions.Item label="ROI (90%)">
              {monteCarloResponse.roi_stats?.p90?.toFixed(2)}%
            </Descriptions.Item>
          </Descriptions>
          
          {monteCarloChartData.length > 0 && (
            <div style={{ marginTop: 24 }}>
              <Divider>Распределение ROI</Divider>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={monteCarloChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="bin" />
                  <YAxis />
                  <Tooltip />
                  <Area type="monotone" dataKey="count" stroke="#8884d8" fill="#8884d8" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
        </Card>
      )}
    </Card>
  );

  return (
    <div>
      <Title level={2}>Профессиональные инструменты</Title>
      
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={16}>
          <Col span={6}>
            <Statistic 
              title="Проектов" 
              value={proMetrics.projectCount} 
              prefix={<FolderOpenOutlined />} 
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="Прибыль" 
              value={proMetrics.budgetProfit} 
              prefix={<DollarCircleOutlined />} 
              suffix="руб."
              formatter={(value) => `${(value as number / 1000000).toFixed(0)} млн`}
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="ROI" 
              value={proMetrics.budgetROI} 
              prefix={<BarChartOutlined />} 
              suffix="%" 
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="Соответствие" 
              value={proMetrics.complianceRate} 
              prefix={<FileProtectOutlined />} 
              suffix="%" 
            />
          </Col>
        </Row>
      </Card>
      
      <Tabs 
        activeKey={activeTab} 
        onChange={setActiveTab}
        type="card"
      >
        <TabPane tab={<span><FileTextOutlined />Письма</span>} key="letters">
          {renderLetterForm()}
        </TabPane>
        <TabPane tab={<span><DollarCircleOutlined />Сметы</span>} key="budget">
          {renderBudgetForm()}
        </TabPane>
        <TabPane tab={<span><ScheduleOutlined />ППР</span>} key="ppr">
          {renderPPRForm()}
        </TabPane>
        <TabPane tab={<span><FileSearchOutlined />Анализ тендера</span>} key="tender">
          {renderTenderAnalysisForm()}
        </TabPane>
        <TabPane tab={<span><FileSyncOutlined />Пакетная обработка смет</span>} key="batch-estimate">
          {renderBatchEstimateForm()}
        </TabPane>
        <TabPane tab={<span><EditOutlined />Продвинутые письма</span>} key="advanced-letters">
          {renderAdvancedLetterForm()}
        </TabPane>
        <TabPane tab={<span><FilePptOutlined />BIM анализ</span>} key="bim">
          {renderBIMForm()}
        </TabPane>
        <TabPane tab={<span><FileZipOutlined />Экспорт DWG</span>} key="dwg">
          {renderDWGForm()}
        </TabPane>
        <TabPane tab={<span><FileExclamationOutlined />Монте-Карло</span>} key="monte-carlo">
          {renderMonteCarloForm()}
        </TabPane>
      </Tabs>
    </div>
  );
};

export default ProFeatures;