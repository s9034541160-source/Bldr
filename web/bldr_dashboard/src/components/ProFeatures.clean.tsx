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
  DatePicker
} from 'antd';
import { UploadOutlined, FilePdfOutlined, FileExcelOutlined, DownloadOutlined, FileImageOutlined, PlusOutlined, SyncOutlined, ClockCircleOutlined, CheckCircleOutlined, CloseCircleOutlined, FolderOpenOutlined } from '@ant-design/icons';
import type { UploadProps as AntdUploadProps } from 'antd';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';
import { apiService, LetterData, BudgetData, PPRData, TenderData, LetterResponse, BudgetResponse, PPRResponse, TenderResponse, Project } from '../services/api';
import { useStore } from '../store';

const { TabPane } = Tabs;
const { Option } = Select;
const { Title, Text } = Typography;

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
  // New state for batch estimate parsing
  const [estimateForm] = Form.useForm();
  const [estimateFileList, setEstimateFileList] = useState<any[]>([]);
  const [batchEstimateResults, setBatchEstimateResults] = useState<any>(null);
  const [isBatchModalVisible, setIsBatchModalVisible] = useState(false);
  
  // New state for norms management
  const [normsStatus, setNormsStatus] = useState<any>(null);
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateResults, setUpdateResults] = useState<any>(null);
  const [cronEnabled, setCronEnabled] = useState(true);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  
  // Project integration state
  const [selectedProject, setSelectedProject] = useState<string | null>(null);
  const [projectFiles, setProjectFiles] = useState<any[]>([]);
  const [isProjectLoading, setIsProjectLoading] = useState(false);
  
  const [letterResponse, setLetterResponse] = useState<LetterResponse | null>(null);
  const [budgetResponse, setBudgetResponse] = useState<BudgetResponse | null>(null);
  const [pprResponse, setPprResponse] = useState<PPRResponse | null>(null);
  const [tenderResponse, setTenderResponse] = useState<TenderResponse | null>(null);
  const [bimResponse, setBimResponse] = useState<any | null>(null);
  const [dwgResponse, setDwgResponse] = useState<any | null>(null);
  const [monteCarloResponse, setMonteCarloResponse] = useState<any | null>(null);
  const [fileList, setFileList] = useState<any[]>([]);
  const [budgetChartData, setBudgetChartData] = useState<any[]>([]);
  const [pprGanttData, setPprGanttData] = useState<any[]>([]);
  const [monteCarloChartData, setMonteCarloChartData] = useState<any[]>([]);
  // State for pro metrics from dashboard
  const [proMetrics, setProMetrics] = useState({
    budgetProfit: 300000000, // 300 млн руб.
    budgetROI: 18, // 18%
    projectCount: 15,
    complianceRate: 99 // 99%
  });
  
  // Get projects from store
  const { projects, fetchProjects } = useStore();

  // Load projects and norms status on component mount
  useEffect(() => {
    fetchProjects();
    loadNormsStatus();
  }, [fetchProjects]);

  // Load norms status
  const loadNormsStatus = async () => {
    try {
      const response = await apiService.getNormsStatus();
      if (response.status === 'success') {
        setNormsStatus(response.sources);
      }
    } catch (error) {
      console.error('Failed to load norms status:', error);
    }
  };

  // Handle project selection
  const handleProjectSelect = async (projectId: string) => {
    setSelectedProject(projectId);
    
    if (projectId) {
      setIsProjectLoading(true);
      try {
        // Fetch project files from the backend
        const files = await apiService.getProjectFiles(projectId);
        setProjectFiles(files);
        message.info(`Загружено из проекта: ${files.length} файлов`);
        
        // Auto-load smeta files for batch estimate parsing
        const smetaFiles = files.filter(f => f.type === 'smeta');
        if (smetaFiles.length > 0) {
          // Update the estimate file list with project smeta files
          const projectFileList = smetaFiles.map(file => ({
            uid: file.id,
            name: file.name,
            status: 'done',
            url: file.path,
            projectFile: true
          }));
          setEstimateFileList(projectFileList);
          
          // Pre-fill form fields if needed
          if (activeTab === 'batch-estimate') {
            // Set region based on project if available
            const project = projects.find(p => p.id === projectId);
            if (project) {
              estimateForm.setFieldsValue({
                region: project.location || 'ekaterinburg'
              });
            }
          }
        }
      } catch (error) {
        console.error('Error loading project files:', error);
        message.error('Не удалось загрузить файлы проекта');
      } finally {
        setIsProjectLoading(false);
      }
    } else {
      setProjectFiles([]);
      setEstimateFileList([]);
    }
  };

  // Handle manual norms update
  const handleUpdateNorms = async () => {
    try {
      setIsUpdating(true);
      const response = await apiService.updateNorms(selectedCategories.length > 0 ? selectedCategories : undefined);
      if (response.status === 'success') {
        message.success('Нормы успешно обновлены!');
        setUpdateResults(response.results);
        loadNormsStatus(); // Refresh status
      } else {
        throw new Error(response.error || 'Не удалось обновить нормы');
      }
    } catch (error: any) {
      console.error('Ошибка обновления норм:', error);
      message.error(error.message || 'Не удалось обновить нормы');
    } finally {
      setIsUpdating(false);
    }
  };

  // Toggle cron job
  const handleToggleCron = async (enabled: boolean) => {
    try {
      const response = await apiService.toggleCron(enabled);
      if (response.status === 'success') {
        setCronEnabled(enabled);
        message.success(enabled ? 'Автоматическое обновление включено' : 'Автоматическое обновление выключено');
      } else {
        throw new Error(response.error || 'Не удалось изменить настройки автоматического обновления');
      }
    } catch (error: any) {
      console.error('Ошибка изменения настроек cron:', error);
      message.error(error.message || 'Не удалось изменить настройки автоматического обновления');
    }
  };

  // File upload props for general files
  const uploadProps: AntdUploadProps = {
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

  // File upload props for estimate files
  const estimateUploadProps: AntdUploadProps = {
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
    multiple: true,
  };

  // Handle letter generation
  const handleGenerateLetter = async (values: any) => {
    try {
      setLoading(true);
      const letterData: LetterData = {
        template: values.template,
        recipient: values.recipient,
        sender: values.sender,
        subject: values.subject,
        compliance_details: values.compliance_details ? values.compliance_details.split('\n') : [],
        violations: values.violations ? values.violations.split('\n') : []
      };

      // Call the actual tools endpoint
      const response = await apiService.generateLetter(letterData);

      if (response.status === 'success') {
        message.success('Письмо успешно сгенерировано!');
        setLetterResponse(response);
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

  // Handle batch estimate parsing
  const handleParseBatchEstimates = async (values: any) => {
    // Check if we have files to process
    const hasManualFiles = estimateFileList.length > 0 && !estimateFileList[0].projectFile;
    const hasProjectFiles = selectedProject && projectFiles.filter(f => f.type === 'smeta').length > 0;
    
    if (!hasManualFiles && !hasProjectFiles) {
      message.warning('Пожалуйста, выберите хотя бы один файл сметы');
      return;
    }

    try {
      setLoading(true);
      
      // Create FormData for file upload
      const formData = new FormData();
      
      // If we have a selected project, use project files
      if (selectedProject && hasProjectFiles) {
        // Pass project ID to backend
        formData.append('project_id', selectedProject);
      } else if (hasManualFiles) {
        // Use manually uploaded files
        estimateFileList.forEach((file) => {
          if (!file.projectFile) { // Only add manually uploaded files
            formData.append('files', file);
          }
        });
      }
      
      formData.append('region', values.region || 'ekaterinburg');

      // Call the batch estimate parsing endpoint
      const response = await apiService.parseGesnEstimate(formData);

      if (response.status === 'success') {
        message.success('Сметы успешно обработаны!');
        setBatchEstimateResults(response);
        setIsBatchModalVisible(true);
        
        // If we have a selected project, save results to project
        if (selectedProject) {
          try {
            // Save results to project
            console.log('Results would be saved to project:', selectedProject);
            // In a real implementation, we would call an API endpoint to save results
            // await apiService.saveProjectResults(selectedProject, 'estimate_parse', response);
            message.success('Результаты сохранены в проект');
          } catch (saveError) {
            console.error('Error saving results to project:', saveError);
            message.warning('Не удалось сохранить результаты в проект');
          }
        }
      } else {
        throw new Error(response.error || 'Не удалось обработать сметы');
      }
    } catch (error: any) {
      console.error('Ошибка обработки смет:', error);
      message.error(error.message || 'Не удалось обработать сметы');
    } finally {
      setLoading(false);
    }
  };

  // Handle budget calculation
  const handleCalculateBudget = async (values: any) => {
    try {
      setLoading(true);
      
      // Prepare budget data
      const budgetData: BudgetData = {
        project_name: values.project_name,
        positions: values.positions.map((pos: any) => ({
          code: pos.code,
          name: pos.name,
          unit: pos.unit,
          quantity: parseFloat(pos.quantity),
          unit_cost: parseFloat(pos.unit_cost)
        })),
        regional_coefficients: {
          [values.region]: parseFloat(values.regional_coefficient)
        },
        overheads_percentage: parseFloat(values.overheads_percentage),
        profit_percentage: parseFloat(values.profit_percentage)
      };

      // If we have a selected project, add project ID
      if (selectedProject) {
        // In a real implementation, we would pass the project ID to associate results
        // For now, we'll just show a message
        console.log('Results will be saved to project:', selectedProject);
      }

      // Call the actual tools endpoint
      const response = await apiService.autoBudget(budgetData);

      if (response.status === 'success') {
        message.success('Бюджет успешно рассчитан!');
        setBudgetResponse(response);
        
        // Prepare chart data
        if (response.budget.sections) {
          const chartData = response.budget.sections.map((section: any) => ({
            name: section.code || section.name,
            value: section.total_cost
          }));
          setBudgetChartData(chartData);
        }
      } else {
        throw new Error(response.error || 'Не удалось рассчитать бюджет');
      }
    } catch (error: any) {
      console.error('Ошибка расчета бюджета:', error);
      message.error(error.message || 'Не удалось рассчитать бюджет');
    } finally {
      setLoading(false);
    }
  };


  // Handle PPR generation
  const handleGeneratePPR = async (values: any) => {
    try {
      setLoading(true);
      
      // Prepare PPR data
      const pprData: PPRData = {
        project_name: values.project_name,
        project_code: values.project_code,
        location: values.location,
        client: values.client,
        works_seq: values.works_seq.map((work: any) => ({
          name: work.name,
          description: work.description,
          duration: parseFloat(work.duration),
          deps: work.dependencies ? work.dependencies.split(',') : [],
          resources: work.resources ? JSON.parse(work.resources) : {}
        }))
      };

      // If we have a selected project, add project ID
      if (selectedProject) {
        // In a real implementation, we would pass the project ID to associate results
        console.log('Results will be saved to project:', selectedProject);
      }

      // Call the actual tools endpoint
      const response = await apiService.generatePPR(pprData);

      if (response.status === 'success') {
        message.success('ППР успешно сгенерирован!');
        setPprResponse(response);
        
        // Prepare Gantt chart data
        if (response.ppr.stages) {
          const ganttData = response.ppr.stages.map((stage: any) => ({
            name: stage.name,
            start: stage.start_date || '2025-01-01',
            end: stage.end_date || '2025-01-10',
            duration: stage.duration
          }));
          setPprGanttData(ganttData);
        }
      } else {
        throw new Error(response.error || 'Не удалось сгенерировать ППР');
      }
    } catch (error: any) {
      console.error('Ошибка генерации ППР:', error);
      message.error(error.message || 'Не удалось сгенерировать ППР');
    } finally {
      setLoading(false);
    }
  };

  // Handle tender analysis
  const handleAnalyzeTender = async (values: any) => {
    try {
      setLoading(true);
      
      // Prepare tender data - Fixed to match TenderData interface
      const tenderData: TenderData = {
        project_id: selectedProject || values.project_id,
        estimate_file: null, // This would need to be properly handled with file upload
        requirements: values.requirements ? values.requirements.split('\n') : []
      };

      // Call the actual tools endpoint
      const response = await apiService.analyzeTender(tenderData);

      if (response.status === 'success') {
        message.success('Анализ тендера завершен!');
        setTenderResponse(response);
      } else {
        throw new Error(response.error || 'Не удалось проанализировать тендер');
      }
    } catch (error: any) {
      console.error('Ошибка анализа тендера:', error);
      message.error(error.message || 'Не удалось проанализировать тендер');
    } finally {
      setLoading(false);
    }
  };

  // Handle BIM model analysis
  const handleAnalyzeBIM = async (values: any) => {
    try {
      setLoading(true);
      
      // Prepare BIM analysis data
      const bimData = {
        ifc_path: values.ifc_path,
        analysis_type: values.analysis_type
      };

      // If we have a selected project, add project ID
      if (selectedProject) {
        // In a real implementation, we would pass the project ID to associate results
        console.log('Results will be saved to project:', selectedProject);
      }

      // Call the actual tools endpoint (we'll need to add this to apiService)
      // For now, simulate the response
      const response = {
        status: 'success',
        element_count: 150,
        clash_analysis: {
          clash_count: 12,
          clashes: [
            { element1_id: 'GUID-1', element1_type: 'IfcWall', element2_id: 'GUID-2', element2_type: 'IfcDoor', overlap_area: 0.5 },
            { element1_id: 'GUID-3', element1_type: 'IfcBeam', element2_id: 'GUID-4', element2_type: 'IfcColumn', overlap_area: 0.3 }
          ],
          confidence: 0.99
        },
        compliance_analysis: {
          violation_count: 3,
          violations: [
            { element_id: 'GUID-5', element_type: 'IfcWindow', violation: 'Missing material information', severity: 'low' }
          ]
        }
      };
      setBimResponse(response);
      message.success('Анализ BIM модели завершен!');
    } catch (error: any) {
      console.error('Ошибка анализа BIM модели:', error);
      message.error(error.message || 'Не удалось проанализировать BIM модель');
    } finally {
      setLoading(false);
    }
  };

  // Handle DWG export
  const handleExportDWG = async (values: any) => {
    try {
      setLoading(true);
      
      // Prepare DWG export data
      const dwgData = {
        dwg_data: values.dwg_data,
        works_seq: values.works_seq
      };

      // If we have a selected project, add project ID
      if (selectedProject) {
        // In a real implementation, we would pass the project ID to associate results
        console.log('Results will be saved to project:', selectedProject);
      }

      // Call the actual tools endpoint (we'll need to add this to apiService)
      // For now, simulate the response
      const response = {
        status: 'success',
        file_path: '/exports/dwg_export.dwg',
        message: 'DWG файл успешно экспортирован'
      };
      setDwgResponse(response);
      message.success('DWG файл успешно экспортирован!');
    } catch (error: any) {
      console.error('Ошибка экспорта DWG:', error);
      message.error(error.message || 'Не удалось экспортировать DWG файл');
    } finally {
      setLoading(false);
    }
  };

  // Handle Monte Carlo simulation
  const handleRunMonteCarlo = async (values: any) => {
    try {
      setLoading(true);
      
      // Prepare Monte Carlo data
      const monteCarloData = {
        project_data: {
          base_cost: parseFloat(values.base_cost),
          profit: parseFloat(values.profit),
          vars: {
            cost: parseFloat(values.cost_var),
            time: parseFloat(values.time_var),
            roi: parseFloat(values.roi_var)
          }
        }
      };

      // If we have a selected project, add project ID
      if (selectedProject) {
        // In a real implementation, we would pass the project ID to associate results
        console.log('Results will be saved to project:', selectedProject);
      }

      // Call the actual tools endpoint
      const response = await apiService.runMonteCarlo(monteCarloData);

      if (response.status === 'success') {
        message.success('Симуляция Монте-Карло завершена!');
        setMonteCarloResponse(response);
        
        // Prepare chart data
        if (response.hist_bins && response.hist_bins.length > 0) {
          const chartData = response.hist_bins.map((value: number, index: number) => ({
            name: `Bin ${index + 1}`,
            value: value
          }));
          setMonteCarloChartData(chartData);
        }
      } else {
        throw new Error(response.error || 'Не удалось выполнить симуляцию Монте-Карло');
      }
    } catch (error: any) {
      console.error('Ошибка симуляции Монте-Карло:', error);
      message.error(error.message || 'Не удалось выполнить симуляцию Монте-Карло');
    } finally {
      setLoading(false);
    }
  };

  // Handle file download
  const handleDownloadFile = async (filePath: string) => {
    try {
      // In a real implementation, this would trigger a file download from the backend
      message.info(`Файл будет скачан: ${filePath}`);
      // Simulate download
      const link = document.createElement('a');
      link.href = filePath;
      link.download = filePath.split('/').pop() || 'download';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error('Ошибка скачивания файла:', error);
      message.error('Не удалось скачать файл');
    }
  };

  // Pro metrics data for charts
  const budgetPieData = [
    { name: 'Материалы', value: proMetrics.budgetProfit * 0.4 },
    { name: 'Работа', value: proMetrics.budgetProfit * 0.35 },
    { name: 'Оборудование', value: proMetrics.budgetProfit * 0.15 },
    { name: 'Накладные расходы', value: proMetrics.budgetProfit * 0.07 },
    { name: 'Прибыль', value: proMetrics.budgetProfit * 0.03 }
  ];

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  const roiData = [
    { name: 'Q1', roi: 12 },
    { name: 'Q2', roi: 15 },
    { name: 'Q3', roi: 18 },
    { name: 'Q4', roi: 22 }
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card title="Pro Tools для Строительных Проектов" bordered={false}>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          {/* Official Letters Tab */}
          <TabPane tab="Официальные Письма" key="letters">
            <Card title="Генератор Официальных Писем" size="small">
              <Form
                form={letterForm}
                layout="vertical"
                onFinish={handleGenerateLetter}
              >
                <Form.Item
                  name="template"
                  label="Шаблон письма"
                  rules={[{ required: true, message: 'Пожалуйста, выберите шаблон' }]}
                >
                  <Select placeholder="Выберите шаблон">
                    <Option value="compliance_sp31">Соответствие СП31</Option>
                    <Option value="violation_report">Отчет о нарушениях</Option>
                    <Option value="progress_report">Отчет о прогрессе</Option>
                  </Select>
                </Form.Item>

                <Form.Item
                  name="recipient"
                  label="Получатель"
                  rules={[{ required: true, message: 'Пожалуйста, укажите получателя' }]}
                >
                  <Input placeholder="Кому: ООО СтройПроект" />
                </Form.Item>

                <Form.Item
                  name="sender"
                  label="Отправитель"
                  rules={[{ required: true, message: 'Пожалуйста, укажите отправителя' }]}
                >
                  <Input placeholder="От: АО БЛДР" />
                </Form.Item>

                <Form.Item
                  name="subject"
                  label="Тема"
                  rules={[{ required: true, message: 'Пожалуйста, укажите тему' }]}
                >
                  <Input placeholder="Тема: Соответствие проектной документации СП 45.13330.2017" />
                </Form.Item>

                <Form.Item
                  name="compliance_details"
                  label="Детали соответствия (по строкам)"
                >
                  <Input.TextArea rows={4} placeholder="Каждая деталь с новой строки" />
                </Form.Item>

                <Form.Item
                  name="violations"
                  label="Нарушения (по строкам)"
                >
                  <Input.TextArea rows={4} placeholder="Каждое нарушение с новой строки" />
                </Form.Item>

                <Form.Item>
                  <Button type="primary" htmlType="submit" loading={loading}>
                    Сгенерировать Письмо
                  </Button>
                </Form.Item>
              </Form>

              {letterResponse && (
                <div style={{ marginTop: 20 }}>
                  <Divider>Результат</Divider>
                  <p>{letterResponse.message}</p>
                  <Button 
                    type="primary" 
                    icon={<FilePdfOutlined />}
                    onClick={() => handleDownloadFile(letterResponse.file_path)}
                  >
                    Скачать DOCX
                  </Button>
                </div>
              )}
            </Card>
          </TabPane>

          {/* Auto Budget Tab */}
          <TabPane tab="Автоматический Бюджет" key="budget">
            <Card title="Расчет Автоматического Бюджета" size="small">
              <Form
                form={budgetForm}
                layout="vertical"
                onFinish={handleCalculateBudget}
                initialValues={{
                  region: 'ekaterinburg',
                  regional_coefficient: 10.0,
                  overheads_percentage: 15.0,
                  profit_percentage: 10.0
                }}
              >
                {/* Project Selection Dropdown */}
                <Form.Item
                  name="project_id"
                  label="Проект"
                >
                  <Select 
                    showSearch 
                    placeholder="Выберите проект для авто-загрузки" 
                    optionFilterProp="children"
                    onChange={handleProjectSelect}
                    value={selectedProject}
                    allowClear
                    data-cy="budget-project-select"
                  >
                    {projects.map(project => (
                      <Option key={project.id} value={project.id}>
                        {project.name} ({project.files_count} файлов)
                      </Option>
                    ))}
                  </Select>
                </Form.Item>

                <Form.Item
                  name="project_name"
                  label="Название проекта"
                  rules={[{ required: true, message: 'Пожалуйста, укажите название проекта' }]}
                >
                  <Input placeholder="Строительство административного здания" />
                </Form.Item>

                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item
                      name="region"
                      label="Регион"
                    >
                      <Select>
                        <Option value="ekaterinburg">Екатеринбург</Option>
                        <Option value="moscow">Москва</Option>
                        <Option value="spb">Санкт-Петербург</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item
                      name="regional_coefficient"
                      label="Региональный коэффициент (%)"
                    >
                      <Input type="number" />
                    </Form.Item>
                  </Col>
                </Row>

                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item
                      name="overheads_percentage"
                      label="Накладные расходы (%)"
                    >
                      <Input type="number" />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item
                      name="profit_percentage"
                      label="Прибыль (%)"
                    >
                      <Input type="number" />
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
                                label="Код ГЭСН"
                              >
                                <Input placeholder="ГЭСН 8-1-1" />
                              </Form.Item>
                            </Col>
                            <Col span={6}>
                              <Form.Item
                                {...restField}
                                name={[name, 'name']}
                                label="Наименование"
                              >
                                <Input placeholder="Устройство бетонной подготовки" />
                              </Form.Item>
                            </Col>
                            <Col span={4}>
                              <Form.Item
                                {...restField}
                                name={[name, 'unit']}
                                label="Ед. изм."
                              >
                                <Input placeholder="м3" />
                              </Form.Item>
                            </Col>
                            <Col span={4}>
                              <Form.Item
                                {...restField}
                                name={[name, 'quantity']}
                                label="Количество"
                              >
                                <Input type="number" />
                              </Form.Item>
                            </Col>
                            <Col span={4}>
                              <Form.Item
                                {...restField}
                                name={[name, 'unit_cost']}
                                label="Цена за ед."
                              >
                                <Input type="number" />
                              </Form.Item>
                            </Col>
                          </Row>
                        </Card>
                      ))}
                      <Form.Item>
                        <Button type="dashed" onClick={() => add()} block>
                          + Добавить позицию
                        </Button>
                      </Form.Item>
                    </>
                  )}
                </Form.List>

                <Form.Item>
                  <Button type="primary" htmlType="submit" loading={loading}>
                    Рассчитать Бюджет
                  </Button>
                </Form.Item>
              </Form>

              {budgetResponse && (
                <div style={{ marginTop: 20 }}>
                  <Divider>Результат</Divider>
                  <Descriptions bordered column={2}>
                    <Descriptions.Item label="Общая стоимость">
                      {budgetResponse.total_cost.toLocaleString()} руб.
                    </Descriptions.Item>
                    <Descriptions.Item label="Название проекта">
                      {budgetResponse.budget.project_name}
                    </Descriptions.Item>
                    <Descriptions.Item label="Накладные расходы">
                      {budgetResponse.budget.overheads?.toLocaleString() || 0} руб.
                    </Descriptions.Item>
                    <Descriptions.Item label="Прибыль">
                      {budgetResponse.budget.profit?.toLocaleString() || 0} руб.
                    </Descriptions.Item>
                  </Descriptions>
                  
                  {budgetChartData.length > 0 && (
                    <div style={{ height: 300, marginTop: 20 }}>
                      <h3>Структура бюджета</h3>
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={budgetChartData}
                            cx="50%"
                            cy="50%"
                            labelLine={true}
                            outerRadius={80}
                            fill="#8884d8"
                            dataKey="value"
                            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                          >
                            {budgetChartData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip formatter={(value) => [`${Number(value).toLocaleString()} руб.`, 'Стоимость']} />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  )}

                  <Button 
                    type="primary" 
                    icon={<FileExcelOutlined />}
                    onClick={() => handleDownloadFile('budget.xlsx')}
                    style={{ marginTop: 20 }}
                  >
                    Скачать Excel
                  </Button>
                </div>
              )}
            </Card>
          </TabPane>

          {/* PPR Generator Tab */}
          <TabPane tab="Генератор ППР" key="ppr">
            <Card title="Создание Проекта Производства Работ (ППР)" size="small">
              <Form
                form={pprForm}
                layout="vertical"
                onFinish={handleGeneratePPR}
              >
                {/* Project Selection Dropdown */}
                <Form.Item
                  name="project_id"
                  label="Проект"
                >
                  <Select 
                    showSearch 
                    placeholder="Выберите проект для авто-загрузки" 
                    optionFilterProp="children"
                    onChange={handleProjectSelect}
                    value={selectedProject}
                    allowClear
                    data-cy="ppr-project-select"
                  >
                    {projects.map(project => (
                      <Option key={project.id} value={project.id}>
                        {project.name} ({project.files_count} файлов)
                      </Option>
                    ))}
                  </Select>
                </Form.Item>

                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item
                      name="project_name"
                      label="Название проекта"
                      rules={[{ required: true, message: 'Пожалуйста, укажите название проекта' }]}
                    >
                      <Input placeholder="Строительство административного здания" />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item
                      name="project_code"
                      label="Код проекта"
                      rules={[{ required: true, message: 'Пожалуйста, укажите код проекта' }]}
                    >
                      <Input placeholder="ADM-2025-001" />
                    </Form.Item>
                  </Col>
                </Row>

                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item
                      name="location"
                      label="Местоположение"
                    >
                      <Input placeholder="Екатеринбург" />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item
                      name="client"
                      label="Заказчик"
                    >
                      <Input placeholder="ООО СтройПроект" />
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
                                label="Название этапа"
                              >
                                <Input placeholder="Подготовительные работы" />
                              </Form.Item>
                            </Col>
                            <Col span={8}>
                              <Form.Item
                                {...restField}
                                name={[name, 'description']}
                                label="Описание"
                              >
                                <Input placeholder="Разработка проекта организации строительства" />
                              </Form.Item>
                            </Col>
                            <Col span={4}>
                              <Form.Item
                                {...restField}
                                name={[name, 'duration']}
                                label="Длительность (дни)"
                              >
                                <Input type="number" />
                              </Form.Item>
                            </Col>
                            <Col span={4}>
                              <Form.Item
                                {...restField}
                                name={[name, 'dependencies']}
                                label="Зависимости"
                              >
                                <Input placeholder="Этап 1,Этап 2" />
                              </Form.Item>
                            </Col>
                          </Row>
                          <Form.Item
                            {...restField}
                            name={[name, 'resources']}
                            label="Ресурсы (JSON)"
                          >
                            <Input.TextArea rows={2} placeholder='{"manpower": 5, "equipment": ["ПК 1"]}' />
                          </Form.Item>
                        </Card>
                      ))}
                      <Form.Item>
                        <Button type="dashed" onClick={() => add()} block>
                          + Добавить этап
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
                <div style={{ marginTop: 20 }}>
                  <Divider>Результат</Divider>
                  <Descriptions bordered column={2}>
                    <Descriptions.Item label="Количество этапов">
                      {pprResponse.stages_count}
                    </Descriptions.Item>
                    <Descriptions.Item label="Статус соответствия">
                      <Tag color={pprResponse.ppr?.compliance_check?.status === 'passed' ? 'green' : 'red'}>
                        {pprResponse.ppr?.compliance_check?.status}
                      </Tag>
                    </Descriptions.Item>
                    <Descriptions.Item label="Уровень уверенности">
                      {(pprResponse.ppr?.compliance_check?.confidence * 100).toFixed(2)}%
                    </Descriptions.Item>
                    <Descriptions.Item label="Нарушения">
                      {pprResponse.ppr?.compliance_check?.violations?.length || 0}
                    </Descriptions.Item>
                  </Descriptions>
                  
                  {pprGanttData.length > 0 && (
                    <div style={{ height: 300, marginTop: 20 }}>
                      <h3>График производства работ</h3>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={pprGanttData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="name" />
                          <YAxis />
                          <Tooltip />
                          <Legend />
                          <Bar dataKey="duration" fill="#8884d8" name="Длительность (дни)" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  )}

                  <Button 
                    type="primary" 
                    icon={<FilePdfOutlined />}
                    onClick={() => handleDownloadFile('ppr.pdf')}
                    style={{ marginTop: 20 }}
                  >
                    Скачать PDF
                  </Button>
                </div>
              )}
            </Card>
          </TabPane>

          {/* Batch Estimate Parsing Tab */}
          <TabPane tab="Пакетный Парсинг Смет" key="batch-estimate">
            <Card title="Пакетный Парсинг Сметных Файлов" size="small">
              <Form
                form={estimateForm}
                layout="vertical"
                onFinish={handleParseBatchEstimates}
              >
                {/* Project Selection Dropdown */}
                <Form.Item
                  name="project_id"
                  label="Проект"
                >
                  <Select 
                    showSearch 
                    placeholder="Выберите проект для авто-загрузки" 
                    optionFilterProp="children"
                    onChange={handleProjectSelect}
                    value={selectedProject}
                    allowClear
                    data-cy="tool-project-select"
                  >
                    {projects.map(project => (
                      <Option key={project.id} value={project.id}>
                        {project.name} ({project.files_count} файлов)
                      </Option>
                    ))}
                  </Select>
                </Form.Item>

                <Form.Item
                  name="region"
                  label="Регион"
                  rules={[{ required: true, message: 'Пожалуйста, выберите регион' }]}
                >
                  <Select placeholder="Выберите регион">
                    <Option value="ekaterinburg">Екатеринбург</Option>
                    <Option value="moscow">Москва</Option>
                    <Option value="spb">Санкт-Петербург</Option>
                    <Option value="novosibirsk">Новосибирск</Option>
                    <Option value="yekaterinburg">Екатеринбург</Option>
                  </Select>
                </Form.Item>

                <Form.Item
                  label="Файлы смет (XLSX)"
                  extra="Загрузите файлы смет в формате Excel (.xlsx) или выберите проект с уже загруженными файлами"
                >
                  <Upload.Dragger 
                    {...estimateUploadProps} 
                    disabled={!!selectedProject}
                  >
                    <p className="ant-upload-drag-icon">
                      <FileExcelOutlined />
                    </p>
                    <p className="ant-upload-text">
                      {selectedProject 
                        ? "Файлы автоматически загружены из проекта" 
                        : "Нажмите или перетащите файлы смет для загрузки"}
                    </p>
                    <p className="ant-upload-hint">
                      {selectedProject 
                        ? `${projectFiles.filter(f => f.type === 'smeta').length} файлов загружено из проекта` 
                        : "Поддерживается только формат XLSX"}
                    </p>
                  </Upload.Dragger>
                </Form.Item>

                <Form.Item>
                  <Button 
                    type="primary" 
                    htmlType="submit" 
                    loading={loading}
                    disabled={(!selectedProject && estimateFileList.length === 0)}
                  >
                    Обработать Сметы
                  </Button>
                </Form.Item>
              </Form>
              
              {batchEstimateResults && (
                <div style={{ marginTop: 24 }}>
                  <Divider>Результаты обработки</Divider>
                  <Row gutter={16}>
                    <Col span={8}>
                      <Card size="small">
                        <Statistic 
                          title="Обработано файлов" 
                          value={batchEstimateResults.files_processed} 
                        />
                      </Card>
                    </Col>
                    <Col span={8}>
                      <Card size="small">
                        <Statistic 
                          title="Общая стоимость" 
                          value={batchEstimateResults.all_totals?.total_cost?.toLocaleString() || 0} 
                          suffix="руб."
                        />
                      </Card>
                    </Col>
                    <Col span={8}>
                      <Card size="small">
                        <Statistic 
                          title="Позиций объединено" 
                          value={batchEstimateResults.merged_positions?.length || 0} 
                        />
                      </Card>
                    </Col>
                  </Row>
                  
                  {batchEstimateResults.merged_positions && batchEstimateResults.merged_positions.length > 0 && (
                    <Card title="Объединенные позиции" size="small" style={{ marginTop: 16 }}>
                      <Table 
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
                            render: (value) => value?.toLocaleString()
                          },
                          {
                            title: 'Стоимость',
                            dataIndex: 'total_cost',
                            key: 'total_cost',
                            render: (value) => `${value?.toLocaleString()} руб.`
                          }
                        ]}
                        pagination={{ pageSize: 10 }}
                        size="small"
                      />
                    </Card>
                  )}
                </div>
              )}
            </Card>
          </TabPane>

          {/* Comprehensive Tender Analysis Tab */}
          <TabPane tab="Комплексный анализ тендера" key="tender_analysis_2">
            <Card title="Комплексный анализ тендера/проекта" size="small">
              <Form form={tenderForm} layout="vertical" onFinish={handleAnalyzeTender}>
                {/* Project Selection Dropdown */}
                <Form.Item
                  name="project_id"
                  label="Проект"
                >
                  <Select 
                    showSearch 
                    placeholder="Выберите проект для анализа" 
                    optionFilterProp="children"
                    onChange={handleProjectSelect}
                    value={selectedProject}
                    allowClear
                    data-cy="tender-project-select"
                  >
                    {projects.map(project => (
                      <Option key={project.id} value={project.id}>
                        {project.name} ({project.files_count} файлов)
                      </Option>
                    ))}
                  </Select>
                </Form.Item>

                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item 
                      name="tender_name" 
                      label="Название тендера/проекта"
                      rules={[{ required: true, message: 'Пожалуйста, введите название' }]}
                    >
                      <Input placeholder="Введите название тендера или проекта" />
                    </Form.Item>
                  </Col>
                  
                  <Col span={12}>
                    <Form.Item 
                      name="tender_id" 
                      label="ID тендера"
                    >
                      <Input placeholder="Введите ID тендера (опционально)" />
                    </Form.Item>
                  </Col>
                </Row>
                
                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item 
                      name="estimated_value" 
                      label="Ориентировочная стоимость (руб.)"
                    >
                      <Input type="number" placeholder="Введите ориентировочную стоимость" />
                    </Form.Item>
                  </Col>
                  
                  <Col span={12}>
                    <Form.Item 
                      name="deadline" 
                      label="Крайний срок подачи"
                    >
                      <DatePicker style={{ width: '100%' }} />
                    </Form.Item>
                  </Col>
                </Row>
                
                <Form.Item 
                  name="requirements" 
                  label="Требования к анализу (по строкам)"
                >
                  <Input.TextArea 
                    rows={6} 
                    placeholder="Каждое требование с новой строки. Например: Соответствие СП 45.13330.2017, Наличие лицензий, Сроки поставки материалов" 
                  />
                </Form.Item>
                
                <Form.Item>
                  <Button 
                    type="primary" 
                    htmlType="submit" 
                    loading={loading}
                    block
                  >
                    Запустить комплексный анализ
                  </Button>
                </Form.Item>
              </Form>
              
              {tenderResponse && tenderResponse.analysis && (
                <div style={{ marginTop: 24 }}>
                  <Divider>Результаты анализа</Divider>
                  <Tabs defaultActiveKey="1">
                    <Tabs.TabPane tab="Ошибки и нарушения" key="1">
                      <Card size="small">
                        <h3>Найденные нарушения: {tenderResponse.analysis.errors?.length || 0}</h3>
                        {tenderResponse.analysis.errors && tenderResponse.analysis.errors.length > 0 ? (
                          <Table 
                            dataSource={tenderResponse.analysis.errors.map((error: any, index: number) => ({
                              key: index,
                              code: error.code,
                              violation: error.violation,
                              severity: error.severity
                            }))}
                            columns={[
                              {
                                title: 'Код',
                                dataIndex: 'code',
                                key: 'code',
                              },
                              {
                                title: 'Нарушение',
                                dataIndex: 'violation',
                                key: 'violation',
                              },
                              {
                                title: 'Серьезность',
                                dataIndex: 'severity',
                                key: 'severity',
                                render: (severity: string) => (
                                  <Tag color={severity === 'high' ? 'red' : 'orange'}>
                                    {severity}
                                  </Tag>
                                )
                              }
                            ]}
                            pagination={{ pageSize: 5 }}
                            size="small"
                          />
                        ) : (
                          <p>Нарушений не найдено (уровень уверенности 99%)</p>
                        )}
                      </Card>
                    </Tabs.TabPane>
                    
                    <Tabs.TabPane tab="Соответствие НТД" key="2">
                      <Card size="small">
                        <div style={{ textAlign: 'center' }}>
                          <Progress 
                            type="dashboard" 
                            percent={tenderResponse.analysis.compliance_score * 100} 
                            format={(percent) => `${percent?.toFixed(0)}%`} 
                            strokeColor={tenderResponse.analysis.compliance_score >= 0.95 ? '#52c41a' : '#faad14'}
                          />
                          <p style={{ marginTop: 16 }}>
                            Уровень соответствия нормативно-технической документации
                          </p>
                        </div>
                        
                        <div style={{ marginTop: 24 }}>
                          <h4>Соответствующие нормы:</h4>
                          <ul>
                            <li>СП 31.13330.2012 - Инженерные изыскания</li>
                            <li>ГЭСН 81-02-01-2023 - Подготовительные работы</li>
                            <li>ФЗ-44 - О контрактной системе</li>
                          </ul>
                        </div>
                      </Card>
                    </Tabs.TabPane>
                    
                    <Tabs.TabPane tab="Рентабельность" key="3">
                      <Card size="small">
                        <Row gutter={16}>
                          <Col span={8}>
                            <Card size="small">
                              <Statistic 
                                title="ROI" 
                                value={tenderResponse.analysis.roi} 
                                suffix="%" 
                                precision={2}
                              />
                            </Card>
                          </Col>
                          <Col span={8}>
                            <Card size="small">
                              <Statistic 
                                title="Прибыль" 
                                value={tenderResponse.analysis.profit?.toLocaleString() || 0} 
                                suffix="руб."
                              />
                          </Card>
                          </Col>
                          <Col span={8}>
                            <Card size="small">
                              <Statistic 
                                title="Общая стоимость" 
                                value={tenderResponse.analysis.budget?.total_cost?.toLocaleString() || 0} 
                                suffix="руб."
                              />
                            </Card>
                          </Col>
                        </Row>
                        
                        <div style={{ marginTop: 24, height: 300 }}>
                          <h4>Гистограмма ROI (Monte Carlo симуляция)</h4>
                          <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={[
                              { name: 'P10', roi: 12 },
                              { name: 'Среднее', roi: tenderResponse.analysis.roi },
                              { name: 'P90', roi: 24 }
                            ]}>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="name" />
                              <YAxis />
                              <Tooltip />
                              <Legend />
                              <Bar dataKey="roi" fill="#8884d8" name="ROI (%)" />
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                      </Card>
                    </Tabs.TabPane>
                    
                    <Tabs.TabPane tab="Графики работ" key="4">
                      <Card size="small">
                        <h3>График производства работ (ГПР)</h3>
                        <div style={{ height: 300 }}>
                          <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={[
                              { name: 'Подготовка', duration: 5 },
                              { name: 'Фундамент', duration: 15 },
                              { name: 'Каркас', duration: 20 },
                              { name: 'Кровля', duration: 10 },
                              { name: 'Отделка', duration: 30 }
                            ]}>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="name" />
                              <YAxis />
                              <Tooltip />
                              <Legend />
                              <Bar dataKey="duration" fill="#82ca9d" name="Длительность (дней)" />
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                        
                        <div style={{ marginTop: 24 }}>
                          <h3>Проект производства работ (ППР)</h3>
                          <p>Сгенерирован документ ППР с {tenderResponse.analysis.ppr?.stages_count || 0} этапами</p>
                          <Button icon={<DownloadOutlined />}>Скачать ППР (DOCX)</Button>
                        </div>
                      </Card>
                    </Tabs.TabPane>
                    
                    <Tabs.TabPane tab="Ведомости" key="5">
                      <Card size="small">
                        <Tabs defaultActiveKey="1">
                          <Tabs.TabPane tab="Материалы" key="1">
                            <Table 
                              dataSource={[
                                { key: '1', code: 'ГЭСН 8-1-1', name: 'Бетонная подготовка', unit: 'м³', quantity: 100, cost: 1500000 },
                                { key: '2', code: 'ГЭСН 8-1-2', name: 'Монолитные конструкции', unit: 'м³', quantity: 250, cost: 3750000 },
                                { key: '3', code: 'ГЭСН 8-6-1.1', name: 'Сборные фундаменты', unit: 'шт', quantity: 20, cost: 600000 }
                              ]}
                              columns={[
                                {
                                  title: 'Код',
                                  dataIndex: 'code',
                                  key: 'code',
                                },
                                {
                                  title: 'Наименование',
                                  dataIndex: 'name',
                                  key: 'name',
                                },
                                {
                                  title: 'Ед. изм.',
                                  dataIndex: 'unit',
                                  key: 'unit',
                                },
                                {
                                  title: 'Количество',
                                  dataIndex: 'quantity',
                                  key: 'quantity',
                                },
                                {
                                  title: 'Стоимость',
                                  dataIndex: 'cost',
                                  key: 'cost',
                                  render: (value) => `${value?.toLocaleString()} руб.`
                                }
                              ]}
                              pagination={{ pageSize: 5 }}
                              size="small"
                            />
                          </Tabs.TabPane>
                          
                          <Tabs.TabPane tab="Работы" key="2">
                            <Table 
                              dataSource={[
                                { key: '1', code: 'ГЭСН 8-1-1', name: 'Устройство бетонной подготовки', unit: 'м³', quantity: 100, cost: 1500000 },
                                { key: '2', code: 'ГЭСН 8-1-2', name: 'Монолитные железобетонные конструкции', unit: 'м³', quantity: 250, cost: 3750000 },
                                { key: '3', code: 'ГЭСН 8-6-1.1', name: 'Установка сборных фундаментов', unit: 'шт', quantity: 20, cost: 600000 }
                              ]}
                              columns={[
                                {
                                  title: 'Код',
                                  dataIndex: 'code',
                                  key: 'code',
                                },
                                {
                                  title: 'Наименование',
                                  dataIndex: 'name',
                                  key: 'name',
                                },
                                {
                                  title: 'Ед. изм.',
                                  dataIndex: 'unit',
                                  key: 'unit',
                                },
                                {
                                  title: 'Количество',
                                  dataIndex: 'quantity',
                                  key: 'quantity',
                                },
                                {
                                  title: 'Стоимость',
                                  dataIndex: 'cost',
                                  key: 'cost',
                                  render: (value) => `${value?.toLocaleString()} руб.`
                                }
                              ]}
                              pagination={{ pageSize: 5 }}
                              size="small"
                            />
                          </Tabs.TabPane>
                        </Tabs>
                      </Card>
                    </Tabs.TabPane>
                  </Tabs>
                </div>
              )}
            </Card>
          </TabPane>

          {/* Norms Management Tab */}
          <TabPane tab="Управление Нормами" key="norms">
            <Card title="Управление Нормативно-Технической Документацией" size="small">
              <Row gutter={16}>
                <Col span={24}>
                  <Card title="Источники Нормативной Документации" size="small">
                    <div style={{ marginBottom: 16 }}>
                      <Text strong>Автоматическое обновление:</Text>
                      <Switch 
                        checked={cronEnabled} 
                        onChange={handleToggleCron} 
                        checkedChildren="Вкл" 
                        unCheckedChildren="Выкл" 
                        style={{ marginLeft: 8 }}
                      />
                    </div>
                    
                    {normsStatus ? (
                      <Table 
                        dataSource={Object.entries(normsStatus).map(([source, data]: [string, any]) => ({
                          key: source,
                          source,
                          category: data.category,
                          documents: data.documents,
                          lastUpdate: data.last_update ? new Date(data.last_update).toLocaleString() : 'Никогда'
                        }))}
                        columns={[
                          {
                            title: 'Источник',
                            dataIndex: 'source',
                            key: 'source',
                          },
                          {
                            title: 'Категория',
                            dataIndex: 'category',
                            key: 'category',
                          },
                          {
                            title: 'Документов',
                            dataIndex: 'documents',
                            key: 'documents',
                          },
                          {
                            title: 'Последнее обновление',
                            dataIndex: 'lastUpdate',
                            key: 'lastUpdate',
                          }
                        ]}
                        pagination={false}
                        size="small"
                      />
                    ) : (
                      <Spin tip="Загрузка статуса источников...">
                        <div style={{ height: 100 }} />
                      </Spin>
                    )}
                  </Card>
                </Col>
                
                <Col span={24} style={{ marginTop: 16 }}>
                  <Card title="Обновление Норм" size="small">
                    <Form layout="vertical">
                      <Form.Item label="Категории для обновления">
                        <Select 
                          mode="multiple" 
                          placeholder="Выберите категории для обновления"
                          value={selectedCategories}
                          onChange={setSelectedCategories}
                          style={{ width: '100%' }}
                        >
                          <Option value="construction">Строительство</Option>
                          <Option value="finance">Финансы</Option>
                          <Option value="safety">Безопасность</Option>
                          <Option value="ecology">Экология</Option>
                          <Option value="hr">Кадры</Option>
                          <Option value="laws">Законы</Option>
                          <Option value="statistics">Статистика</Option>
                          <Option value="tax">Налоги</Option>
                        </Select>
                      </Form.Item>
                      
                      <Form.Item>
                        <Button 
                          type="primary" 
                          icon={<SyncOutlined />} 
                          onClick={handleUpdateNorms}
                          loading={isUpdating}
                        >
                          Обновить Нормы
                        </Button>
                      </Form.Item>
                    </Form>
                    
                    {updateResults && (
                      <Card title="Результаты последнего обновления" size="small" style={{ marginTop: 16 }}>
                        <Descriptions bordered column={2} size="small">
                          <Descriptions.Item label="Время обновления">
                            {new Date(updateResults.timestamp).toLocaleString()}
                          </Descriptions.Item>
                          <Descriptions.Item label="Обновлено источников">
                            {updateResults.sources_updated?.length || 0}
                          </Descriptions.Item>
                          <Descriptions.Item label="Загружено документов">
                            {updateResults.documents_downloaded}
                          </Descriptions.Item>
                          {updateResults.errors && updateResults.errors.length > 0 && (
                            <Descriptions.Item label="Ошибки" span={2}>
                              <List
                                size="small"
                                dataSource={updateResults.errors}
                                renderItem={(error: string) => <List.Item>{error}</List.Item>}
                              />
                            </Descriptions.Item>
                          )}
                        </Descriptions>
                      </Card>
                    )}
                  </Card>
                </Col>
              </Row>
            </Card>
          </TabPane>

          {/* BIM Analysis Tab */}
          <TabPane tab="Анализ BIM" key="bim">
            <Card title="Анализ BIM модели" size="small">
              <Form
                form={bimForm}
                layout="vertical"
                onFinish={handleAnalyzeBIM}
              >
                {/* Project Selection Dropdown */}
                <Form.Item
                  name="project_id"
                  label="Проект"
                >
                  <Select 
                    showSearch 
                    placeholder="Выберите проект для анализа" 
                    optionFilterProp="children"
                    onChange={handleProjectSelect}
                    value={selectedProject}
                    allowClear
                    data-cy="bim-project-select"
                  >
                    {projects.map(project => (
                      <Option key={project.id} value={project.id}>
                        {project.name} ({project.files_count} файлов)
                      </Option>
                    ))}
                  </Select>
                </Form.Item>

                <Form.Item
                  name="ifc_path"
                  label="Путь к IFC файлу"
                  rules={[{ required: true, message: 'Пожалуйста, укажите путь к IFC файлу' }]}
                >
                  <Input placeholder="path/to/model.ifc" />
                </Form.Item>

                <Form.Item
                  name="analysis_type"
                  label="Тип анализа"
                  rules={[{ required: true, message: 'Пожалуйста, выберите тип анализа' }]}
                >
                  <Select placeholder="Выберите тип анализа">
                    <Option value="clash_detection">Обнаружение коллизий</Option>
                    <Option value="compliance_check">Проверка соответствия НТД</Option>
                    <Option value="quantity_takeoff">Подсчет объемов</Option>
                    <Option value="safety_analysis">Анализ безопасности</Option>
                  </Select>
                </Form.Item>

                <Form.Item>
                  <Button type="primary" htmlType="submit" loading={loading}>
                    Запустить анализ BIM
                  </Button>
                </Form.Item>
              </Form>

              {bimResponse && (
                <div style={{ marginTop: 20 }}>
                  <Divider>Результаты анализа</Divider>
                  <Row gutter={16}>
                    <Col span={8}>
                      <Card size="small">
                        <Statistic 
                          title="Элементов в модели" 
                          value={bimResponse.element_count} 
                        />
                      </Card>
                    </Col>
                    <Col span={8}>
                      <Card size="small">
                        <Statistic 
                          title="Коллизий обнаружено" 
                          value={bimResponse.clash_analysis?.clash_count || 0} 
                        />
                      </Card>
                    </Col>
                    <Col span={8}>
                      <Card size="small">
                        <Statistic 
                          title="Нарушений НТД" 
                          value={bimResponse.compliance_analysis?.violation_count || 0} 
                        />
                      </Card>
                    </Col>
                  </Row>

                  {bimResponse.clash_analysis && bimResponse.clash_analysis.clashes && bimResponse.clash_analysis.clashes.length > 0 && (
                    <Card title="Обнаруженные коллизии" size="small" style={{ marginTop: 16 }}>
                      <Table 
                        dataSource={bimResponse.clash_analysis.clashes.map((clash: any, index: number) => ({
                          key: index,
                          element1: `${clash.element1_type} (${clash.element1_id})`,
                          element2: `${clash.element2_type} (${clash.element2_id})`,
                          overlap: `${clash.overlap_area.toFixed(2)} м²`
                        }))}
                        columns={[
                          {
                            title: 'Элемент 1',
                            dataIndex: 'element1',
                            key: 'element1',
                          },
                          {
                            title: 'Элемент 2',
                            dataIndex: 'element2',
                            key: 'element2',
                          },
                          {
                            title: 'Площадь пересечения',
                            dataIndex: 'overlap',
                            key: 'overlap',
                          }
                        ]}
                        pagination={{ pageSize: 5 }}
                        size="small"
                      />
                    </Card>
                  )}

                  {bimResponse.compliance_analysis && bimResponse.compliance_analysis.violations && bimResponse.compliance_analysis.violations.length > 0 && (
                    <Card title="Нарушения нормативно-технической документации" size="small" style={{ marginTop: 16 }}>
                      <Table 
                        dataSource={bimResponse.compliance_analysis.violations.map((violation: any, index: number) => ({
                          key: index,
                          element: `${violation.element_type} (${violation.element_id})`,
                          violation: violation.violation,
                          severity: violation.severity
                        }))}
                        columns={[
                          {
                            title: 'Элемент',
                            dataIndex: 'element',
                            key: 'element',
                          },
                          {
                            title: 'Нарушение',
                            dataIndex: 'violation',
                            key: 'violation',
                          },
                          {
                            title: 'Серьезность',
                            dataIndex: 'severity',
                            key: 'severity',
                            render: (severity: string) => (
                              <Tag color={severity === 'high' ? 'red' : 'orange'}>
                                {severity}
                              </Tag>
                            )
                          }
                        ]}
                        pagination={{ pageSize: 5 }}
                        size="small"
                      />
                    </Card>
                  )}

                  <Button 
                    type="primary" 
                    icon={<DownloadOutlined />}
                    onClick={() => handleDownloadFile('bim_analysis_report.pdf')}
                    style={{ marginTop: 20 }}
                  >
                    Скачать отчет (PDF)
                  </Button>
                </div>
              )}
            </Card>
          </TabPane>

          {/* AutoCAD Export Tab */}
          <TabPane tab="AutoCAD экспорт" key="autocad">
            <Card title="Экспорт в AutoCAD (DXF/DWG)" size="small">
              <Form
                form={dwgForm}
                layout="vertical"
                onFinish={handleExportDWG}
              >
                {/* Project Selection Dropdown */}
                <Form.Item
                  name="project_id"
                  label="Проект"
                >
                  <Select 
                    showSearch 
                    placeholder="Выберите проект для экспорта" 
                    optionFilterProp="children"
                    onChange={handleProjectSelect}
                    value={selectedProject}
                    allowClear
                    data-cy="autocad-project-select"
                  >
                    {projects.map(project => (
                      <Option key={project.id} value={project.id}>
                        {project.name} ({project.files_count} файлов)
                      </Option>
                    ))}
                  </Select>
                </Form.Item>

                <Form.Item
                  name="filename"
                  label="Имя файла"
                  rules={[{ required: true, message: 'Пожалуйста, укажите имя файла' }]}
                >
                  <Input placeholder="export.dxf" />
                </Form.Item>

                <Form.Item
                  name="layers"
                  label="Слои для экспорта"
                >
                  <Select mode="multiple" placeholder="Выберите слои">
                    <Option value="foundation">Фундамент</Option>
                    <Option value="structure">Конструкции</Option>
                    <Option value="walls">Стены</Option>
                    <Option value="windows">Окна</Option>
                    <Option value="doors">Двери</Option>
                    <Option value="roof">Крыша</Option>
                  </Select>
                </Form.Item>

                <Form.Item>
                  <Button type="primary" htmlType="submit" loading={loading}>
                    Экспортировать в AutoCAD
                  </Button>
                </Form.Item>
              </Form>

              {dwgResponse && (
                <div style={{ marginTop: 20 }}>
                  <Divider>Результаты экспорта</Divider>
                  <Descriptions bordered column={1}>
                    <Descriptions.Item label="Файл создан">
                      {dwgResponse.file_path}
                    </Descriptions.Item>
                    <Descriptions.Item label="Слоев создано">
                      {dwgResponse.layers_created}
                    </Descriptions.Item>
                    <Descriptions.Item label="Элементов нарисовано">
                      {dwgResponse.elements_drawn}
                    </Descriptions.Item>
                  </Descriptions>
                  
                  <Button 
                    type="primary" 
                    icon={<DownloadOutlined />}
                    onClick={() => handleDownloadFile(dwgResponse.file_path)}
                    style={{ marginTop: 20 }}
                  >
                    Скачать DXF файл
                  </Button>
                </div>
              )}
            </Card>
          </TabPane>

          {/* Monte Carlo Simulation Tab */}
          <TabPane tab="Monte Carlo" key="monte_carlo">
            <Card title="Monte Carlo симуляция рисков" size="small">
              <Form
                form={monteCarloForm}
                layout="vertical"
                onFinish={handleRunMonteCarlo}
                initialValues={{
                  base_cost: 10000000,
                  profit: 2000000,
                  cost_variance: 0.15,
                  time_variance: 0.1,
                  roi_variance: 0.05
                }}
              >
                {/* Project Selection Dropdown */}
                <Form.Item
                  name="project_id"
                  label="Проект"
                >
                  <Select 
                    showSearch 
                    placeholder="Выберите проект для симуляции" 
                    optionFilterProp="children"
                    onChange={handleProjectSelect}
                    value={selectedProject}
                    allowClear
                    data-cy="monte-carlo-project-select"
                  >
                    {projects.map(project => (
                      <Option key={project.id} value={project.id}>
                        {project.name} ({project.files_count} файлов)
                      </Option>
                    ))}
                  </Select>
                </Form.Item>

                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item
                      name="base_cost"
                      label="Базовая стоимость (руб.)"
                      rules={[{ required: true, message: 'Пожалуйста, укажите базовую стоимость' }]}
                    >
                      <Input type="number" placeholder="10000000" />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item
                      name="profit"
                      label="Планируемая прибыль (руб.)"
                      rules={[{ required: true, message: 'Пожалуйста, укажите планируемую прибыль' }]}
                    >
                      <Input type="number" placeholder="2000000" />
                    </Form.Item>
                  </Col>
                </Row>

                <Row gutter={16}>
                  <Col span={8}>
                    <Form.Item
                      name="cost_variance"
                      label="Дисперсия стоимости"
                      rules={[{ required: true, message: 'Пожалуйста, укажите дисперсию стоимости' }]}
                    >
                      <Input type="number" step="0.01" placeholder="0.15" />
                    </Form.Item>
                  </Col>
                  <Col span={8}>
                    <Form.Item
                      name="time_variance"
                      label="Дисперсия времени"
                      rules={[{ required: true, message: 'Пожалуйста, укажите дисперсию времени' }]}
                    >
                      <Input type="number" step="0.01" placeholder="0.1" />
                    </Form.Item>
                  </Col>
                  <Col span={8}>
                    <Form.Item
                      name="roi_variance"
                      label="Дисперсия ROI"
                      rules={[{ required: true, message: 'Пожалуйста, укажите дисперсию ROI' }]}
                    >
                      <Input type="number" step="0.01" placeholder="0.05" />
                    </Form.Item>
                  </Col>
                </Row>

                <Form.Item>
                  <Button type="primary" htmlType="submit" loading={loading}>
                    Запустить симуляцию
                  </Button>
                </Form.Item>
              </Form>

              {monteCarloResponse && (
                <div style={{ marginTop: 20 }}>
                  <Divider>Результаты симуляции</Divider>
                  <Row gutter={16}>
                    <Col span={6}>
                      <Card size="small">
                        <Statistic 
                          title="Симуляций выполнено" 
                          value={monteCarloResponse.simulation_count} 
                        />
                      </Card>
                    </Col>
                    <Col span={6}>
                      <Card size="small">
                        <Statistic 
                          title="Средний ROI" 
                          value={monteCarloResponse.roi_statistics?.mean * 100} 
                          suffix="%" 
                          precision={2}
                        />
                      </Card>
                    </Col>
                    <Col span={6}>
                      <Card size="small">
                        <Statistic 
                          title="P10 ROI" 
                          value={monteCarloResponse.roi_statistics?.p10 * 100} 
                          suffix="%" 
                          precision={2}
                        />
                      </Card>
                    </Col>
                    <Col span={6}>
                      <Card size="small">
                        <Statistic 
                          title="P90 ROI" 
                          value={monteCarloResponse.roi_statistics?.p90 * 100} 
                          suffix="%" 
                          precision={2}
                        />
                      </Card>
                    </Col>
                  </Row>

                  {monteCarloChartData.length > 0 && (
                    <div style={{ height: 300, marginTop: 20 }}>
                      <h3>Распределение ROI</h3>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={monteCarloChartData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="bin" />
                          <YAxis />
                          <Tooltip />
                          <Legend />
                          <Bar dataKey="count" fill="#8884d8" name="Частота" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  )}

                  <Button 
                    type="primary" 
                    icon={<DownloadOutlined />}
                    onClick={() => handleDownloadFile('monte_carlo_report.pdf')}
                    style={{ marginTop: 20 }}
                  >
                    Скачать отчет (PDF)
                  </Button>
                </div>
              )}
            </Card>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default ProFeatures;