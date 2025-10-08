import React, { useState, useCallback } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Alert,
  LinearProgress,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Switch,
  FormControlLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tabs,
  Tab,
  Slider,
  Tooltip
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  AttachFile as AttachIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Download as DownloadIcon,
  Calculate as CalculateIcon,
  Assessment as AssessmentIcon,
  ExpandMore as ExpandMoreIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  TableChart as TableIcon,
  PictureAsPdf as PdfIcon,
  Description as DocIcon,
  AccountBalance as BudgetIcon,
  Engineering as WorkerIcon,
  Schedule as TimeIcon,
  LocalAtm as CostIcon,
  HealthAndSafety as SafetyIcon,
  Flight as TravelIcon
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';

const AutoBudget = ({ toolId, onJobStart, onJobComplete }) => {
  // State management
  const [activeTab, setActiveTab] = useState(0);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [jobProgress, setJobProgress] = useState(0);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false);
  const [extractedBaseCost, setExtractedBaseCost] = useState(0);
  const [manualBaseCost, setManualBaseCost] = useState(0);
  const [useExtractedCost, setUseExtractedCost] = useState(false);
  
  // Budget parameters
  const [budgetParams, setBudgetParams] = useState({
    project_name: '',
    base_cost: 0,
    project_type: 'residential',
    worker_daily_wage: 6700,
    total_labor_hours: 40000,
    project_duration_months: 12,
    shifts_per_day: 1,
    hours_per_shift: 10,
    shifts_per_month: 30,
    shift_mode_days: 45,
    efficiency_coefficient: 0.8,
    siz_cost: 30000,
    ticket_cost: 15000,
    meal_cost: 800,
    accommodation_cost: 1200,
    engineer_daily_wage: 8335,
    engineer_ratio: 0.14,
    mandatory_engineers: 8,
    insurance_rate: 0.32,
    currency: 'RUB'
  });

  // Supported file types
  const supportedTypes = {
    '.xlsx': 'Excel файл',
    '.xls': 'Excel файл (старый формат)',
    '.pdf': 'PDF документ',
    '.csv': 'CSV файл',
    '.doc': 'Word документ',
    '.docx': 'Word документ'
  };

  // Project types
  const projectTypes = [
    { value: 'residential', label: 'Жилой дом' },
    { value: 'commercial', label: 'Коммерческое здание' },
    { value: 'industrial', label: 'Промышленный объект' },
    { value: 'infrastructure', label: 'Инфраструктура' },
    { value: 'renovation', label: 'Реконструкция' },
    { value: 'repair', label: 'Ремонт' }
  ];

  // Currency options
  const currencyOptions = [
    { value: 'RUB', label: 'Рубли (₽)' },
    { value: 'USD', label: 'Доллары ($)' },
    { value: 'EUR', label: 'Евро (€)' }
  ];

  // File drop handling
  const onDrop = useCallback((acceptedFiles) => {
    const newFiles = acceptedFiles.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      name: file.name,
      size: file.size,
      type: file.type,
      uploadedAt: new Date(),
      status: 'ready'
    }));
    
    setUploadedFiles(prev => [...prev, ...newFiles]);
    
    // If we have estimate files, try to extract base cost from the first one
    if (newFiles.length > 0) {
      // The actual extraction will be done by the backend when the calculation is started
      // For now, we just set a flag to indicate that we have files that can be parsed
      console.log('Files uploaded, base cost extraction will be done by backend');
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'application/pdf': ['.pdf'],
      'text/csv': ['.csv'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    },
    maxSize: 50 * 1024 * 1024 // 50MB
  });

  // Remove file
  const removeFile = (fileId) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
  };

  // Preview file
  const previewFile = (file) => {
    setSelectedFile(file);
    setPreviewDialogOpen(true);
  };

  // Handle parameter changes
  const handleParamChange = (paramName, value) => {
    setBudgetParams(prev => ({ ...prev, [paramName]: value }));
    
    // If base cost is changed manually, disable using extracted cost
    if (paramName === 'base_cost') {
      setUseExtractedCost(false);
    }
  };

  // Toggle use of extracted cost
  const toggleUseExtractedCost = (use) => {
    setUseExtractedCost(use);
    if (use && extractedBaseCost > 0) {
      setBudgetParams(prev => ({ ...prev, base_cost: extractedBaseCost }));
    }
  };

  // Extract base cost from uploaded files
  const extractBaseCost = async () => {
    if (uploadedFiles.length === 0) {
      alert('Пожалуйста, загрузите файлы смет перед извлечением стоимости');
      return;
    }

    setIsAnalyzing(true);
    
    try {
      // Prepare form data
      const formData = new FormData();
      
      // Add uploaded files
      uploadedFiles.forEach((fileData, index) => {
        formData.append(`estimate_files`, fileData.file);
      });

      // Call extract base cost endpoint
      const response = await fetch('/api/tools/extract/base-cost', {
        method: 'POST',
        body: formData
      });

      const result = await response.json();
      
      if (result.success) {
        const extractedCost = result.base_cost;
        setExtractedBaseCost(extractedCost);
        setUseExtractedCost(true);
        setBudgetParams(prev => ({ ...prev, base_cost: extractedCost }));
        alert(`Базовая стоимость успешно извлечена: ${formatCurrency(extractedCost)}`);
      } else {
        alert('Ошибка извлечения стоимости: ' + result.error);
      }
    } catch (error) {
      console.error('Error extracting base cost:', error);
      alert('Ошибка сети при извлечении стоимости: ' + error.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Start budget calculation
  const startCalculation = async () => {
    if (!budgetParams.project_name.trim()) {
      alert('Введите название проекта');
      return;
    }

    if (budgetParams.base_cost <= 0) {
      // Check if we have uploaded files that might contain the base cost
      if (uploadedFiles.length === 0) {
        alert('Базовая стоимость должна быть больше 0');
        return;
      }
      // If we have files, we'll let the backend try to extract the cost
    }

    setIsAnalyzing(true);
    setJobProgress(0);
    setAnalysisResults(null);

    try {
      // Prepare form data
      const formData = new FormData();
      
      // Add uploaded files if any
      uploadedFiles.forEach((fileData, index) => {
        formData.append(`estimate_files`, fileData.file);
      });
      
      // Add budget parameters
      formData.append('params', JSON.stringify(budgetParams));
      formData.append('tool', 'auto_budget');

      // Start calculation job
      const response = await fetch('/api/tools/calculate/budget', {
        method: 'POST',
        body: formData
      });

      const result = await response.json();
      
      if (result.success) {
        const jobId = result.job_id;
        onJobStart(jobId);
        
        // Poll for progress
        const progressInterval = setInterval(async () => {
          try {
            const progressResponse = await fetch(`/api/tools/jobs/${jobId}/status`);
            const progressData = await progressResponse.json();
            
            if (progressData.success) {
              setJobProgress(progressData.progress || 0);
              
              if (progressData.status === 'completed') {
                clearInterval(progressInterval);
                setAnalysisResults(progressData.result);
                setIsAnalyzing(false);
                onJobComplete(jobId, progressData.result);
                
                // If we extracted base cost, update our state
                if (progressData.result && progressData.result.metadata && progressData.result.metadata.base_cost) {
                  const extractedCost = progressData.result.metadata.base_cost;
                  setExtractedBaseCost(extractedCost);
                  if (!useExtractedCost) {
                    setUseExtractedCost(true);
                    setBudgetParams(prev => ({ ...prev, base_cost: extractedCost }));
                  }
                }
              } else if (progressData.status === 'failed') {
                clearInterval(progressInterval);
                setIsAnalyzing(false);
                alert('Ошибка расчета: ' + progressData.error);
              }
            }
          } catch (error) {
            console.error('Error polling job status:', error);
          }
        }, 1000);

      } else {
        setIsAnalyzing(false);
        alert('Ошибка запуска расчета: ' + result.error);
      }
    } catch (error) {
      setIsAnalyzing(false);
      console.error('Error starting calculation:', error);
      alert('Ошибка сети: ' + error.message);
    }
  };

  // Stop calculation
  const stopCalculation = () => {
    setIsAnalyzing(false);
    setJobProgress(0);
    // TODO: Send cancel request to backend
  };

  // Format file size
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Get file icon
  const getFileIcon = (fileName) => {
    const ext = fileName.substring(fileName.lastIndexOf('.')).toLowerCase();
    switch (ext) {
      case '.pdf': return <PdfIcon />;
      case '.xlsx':
      case '.xls': return <TableIcon />;
      default: return <DocIcon />;
    }
  };

  // Format currency
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: budgetParams.currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  // Render parameter input based on type
  const renderParamInput = (param) => {
    const { name, label, type, min, max, step, defaultValue } = param;
    
    switch (type) {
      case 'number':
        return (
          <TextField
            fullWidth
            label={label}
            type="number"
            value={budgetParams[name] || defaultValue || 0}
            onChange={(e) => handleParamChange(name, parseFloat(e.target.value) || 0)}
            margin="normal"
            inputProps={{ min, max, step }}
            InputProps={{
              endAdornment: param.unit ? <span>{param.unit}</span> : null
            }}
          />
        );
      
      case 'slider':
        return (
          <Box mt={2}>
            <Typography gutterBottom>{label}</Typography>
            <Slider
              value={budgetParams[name] || defaultValue || 0}
              onChange={(e, newValue) => handleParamChange(name, newValue)}
              min={min}
              max={max}
              step={step}
              valueLabelDisplay="auto"
              marks={[
                { value: min, label: min.toString() },
                { value: max, label: max.toString() }
              ]}
            />
            <Typography variant="body2" align="center">
              {budgetParams[name] || defaultValue} {param.unit}
            </Typography>
          </Box>
        );
      
      case 'enum':
        return (
          <FormControl fullWidth margin="normal">
            <InputLabel>{label}</InputLabel>
            <Select
              value={budgetParams[name] || defaultValue}
              onChange={(e) => handleParamChange(name, e.target.value)}
              label={label}
            >
              {param.options.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        );
      
      default:
        return (
          <TextField
            fullWidth
            label={label}
            value={budgetParams[name] || defaultValue || ''}
            onChange={(e) => handleParamChange(name, e.target.value)}
            margin="normal"
          />
        );
    }
  };

  // Parameter definitions
  const budgetParameters = [
    // Basic parameters
    {
      category: 'Основные параметры',
      icon: <BudgetIcon />,
      params: [
        { name: 'project_name', label: 'Название проекта', type: 'text' },
        { 
          name: 'base_cost', 
          label: 'Базовая стоимость (материалы + работы)', 
          type: 'number', 
          min: 1000, 
          max: 100000000, 
          step: 1000,
          unit: '₽'
        },
        { 
          name: 'project_type', 
          label: 'Тип проекта', 
          type: 'enum', 
          options: projectTypes,
          defaultValue: 'residential'
        },
        { 
          name: 'currency', 
          label: 'Валюта расчета', 
          type: 'enum', 
          options: currencyOptions,
          defaultValue: 'RUB'
        }
      ]
    },
    
    // Labor parameters
    {
      category: 'Параметры труда',
      icon: <WorkerIcon />,
      params: [
        { 
          name: 'worker_daily_wage', 
          label: 'Зарплата рабочего, руб/сут', 
          type: 'number', 
          min: 100, 
          max: 50000, 
          step: 100,
          unit: '₽'
        },
        { 
          name: 'total_labor_hours', 
          label: 'Общая трудоёмкость, чел.-часы', 
          type: 'number', 
          min: 100, 
          max: 1000000, 
          step: 100
        },
        { 
          name: 'project_duration_months', 
          label: 'Продолжительность проекта, мес', 
          type: 'number', 
          min: 1, 
          max: 60, 
          step: 1
        },
        { 
          name: 'shifts_per_day', 
          label: 'Количество смен в день', 
          type: 'number', 
          min: 1, 
          max: 3, 
          step: 1
        },
        { 
          name: 'hours_per_shift', 
          label: 'Часов в смене', 
          type: 'number', 
          min: 1, 
          max: 24, 
          step: 1
        },
        { 
          name: 'shifts_per_month', 
          label: 'Смен в месяце', 
          type: 'number', 
          min: 1, 
          max: 31, 
          step: 1
        },
        { 
          name: 'shift_mode_days', 
          label: 'Режим вахты, дней', 
          type: 'number', 
          min: 1, 
          max: 90, 
          step: 1
        },
        { 
          name: 'efficiency_coefficient', 
          label: 'Коэффициент выработки', 
          type: 'slider', 
          min: 0.1, 
          max: 1.0, 
          step: 0.01
        }
      ]
    },
    
    // Engineer parameters
    {
      category: 'Параметры ИТР',
      icon: <Engineering />,
      params: [
        { 
          name: 'engineer_daily_wage', 
          label: 'Зарплата ИТР, руб/сут', 
          type: 'number', 
          min: 1000, 
          max: 50000, 
          step: 100,
          unit: '₽'
        },
        { 
          name: 'engineer_ratio', 
          label: 'Доля линейного ИТР от рабочих', 
          type: 'slider', 
          min: 0.01, 
          max: 1.0, 
          step: 0.01
        },
        { 
          name: 'mandatory_engineers', 
          label: 'Обязательный ИТР (шт.)', 
          type: 'number', 
          min: 1, 
          max: 50, 
          step: 1
        }
      ]
    },
    
    // Travel and equipment parameters
    {
      category: 'Командировки и оборудование',
      icon: <TravelIcon />,
      params: [
        { 
          name: 'siz_cost', 
          label: 'Стоимость комплекта СИЗ, руб', 
          type: 'number', 
          min: 1000, 
          max: 100000, 
          step: 1000,
          unit: '₽'
        },
        { 
          name: 'ticket_cost', 
          label: 'Стоимость билета, руб', 
          type: 'number', 
          min: 1000, 
          max: 50000, 
          step: 1000,
          unit: '₽'
        },
        { 
          name: 'meal_cost', 
          label: 'Стоимость питания, руб/сут/чел', 
          type: 'number', 
          min: 100, 
          max: 5000, 
          step: 100,
          unit: '₽'
        },
        { 
          name: 'accommodation_cost', 
          label: 'Стоимость проживания, руб/сут/чел', 
          type: 'number', 
          min: 100, 
          max: 5000, 
          step: 100,
          unit: '₽'
        }
      ]
    },
    
    // Insurance parameters
    {
      category: 'Страховые взносы',
      icon: <SafetyIcon />,
      params: [
        { 
          name: 'insurance_rate', 
          label: 'Страховые взносы (0.0-1.0)', 
          type: 'slider', 
          min: 0.0, 
          max: 1.0, 
          step: 0.01
        }
      ]
    }
  ];

  return (
    <Box>
      <Grid container spacing={3}>
        {/* File Upload Section */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                📂 Загрузка смет
              </Typography>
              
              {/* Drag & Drop Zone */}
              <Box
                {...getRootProps()}
                sx={{
                  border: '2px dashed #cccccc',
                  borderRadius: 2,
                  p: 4,
                  textAlign: 'center',
                  cursor: 'pointer',
                  backgroundColor: isDragActive ? '#f5f5f5' : 'transparent',
                  '&:hover': {
                    backgroundColor: '#f8f8f8'
                  }
                }}
              >
                <input {...getInputProps()} />
                <UploadIcon sx={{ fontSize: 48, color: '#666', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  {isDragActive 
                    ? 'Отпустите файлы здесь...' 
                    : 'Перетащите файлы сюда или нажмите для выбора'
                  }
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Поддерживаются: {Object.entries(supportedTypes).map(([ext, desc]) => ext).join(', ')}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Максимальный размер файла: 50 МБ
                </Typography>
              </Box>

              {/* Uploaded Files List */}
              {uploadedFiles.length > 0 && (
                <Box mt={3}>
                  <Typography variant="subtitle1" gutterBottom>
                    Загруженные файлы ({uploadedFiles.length})
                  </Typography>
                  <List>
                    {uploadedFiles.map((fileData) => (
                      <ListItem
                        key={fileData.id}
                        secondaryAction={
                          <Box>
                            <IconButton onClick={() => previewFile(fileData)}>
                              <ViewIcon />
                            </IconButton>
                            <IconButton onClick={() => removeFile(fileData.id)} color="error">
                              <DeleteIcon />
                            </IconButton>
                          </Box>
                        }
                      >
                        <ListItemIcon>
                          {getFileIcon(fileData.name)}
                        </ListItemIcon>
                        <ListItemText
                          primary={fileData.name}
                          secondary={`${formatFileSize(fileData.size)} • ${fileData.uploadedAt.toLocaleString()}`}
                        />
                        <Chip 
                          label={fileData.status} 
                          size="small" 
                          color={fileData.status === 'ready' ? 'success' : 'default'}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}

              {/* Base Cost Extraction */}
              {uploadedFiles.length > 0 && (
                <Box mt={3}>
                  <Alert 
                    severity="info" 
                    action={
                      <Button 
                        color="inherit" 
                        size="small"
                        onClick={extractBaseCost}
                        disabled={isAnalyzing}
                        startIcon={<CalculateIcon />}
                      >
                        Извлечь стоимость
                      </Button>
                    }
                  >
                    <Typography variant="body1">
                      <strong>Файлы смет загружены:</strong> {uploadedFiles.length} шт.
                    </Typography>
                    <Typography variant="body2">
                      Нажмите "Извлечь стоимость" чтобы попытаться автоматически определить базовую стоимость из файлов
                    </Typography>
                  </Alert>
                </Box>
              )}
              
              {extractedBaseCost > 0 && (
                <Box mt={3}>
                  <Alert 
                    severity="success"
                    action={
                      <FormControlLabel
                        control={
                          <Switch
                            checked={useExtractedCost}
                            onChange={(e) => toggleUseExtractedCost(e.target.checked)}
                          />
                        }
                        label="Использовать"
                      />
                    }
                  >
                    <Typography variant="body1">
                      <strong>Извлечённая базовая стоимость:</strong> {formatCurrency(extractedBaseCost)}
                    </Typography>
                    <Typography variant="body2">
                      Из файла: {uploadedFiles[0]?.name}
                    </Typography>
                  </Alert>
                </Box>
              )}
              
              {extractedBaseCost === 0 && isAnalyzing && (
                <Box mt={3}>
                  <Alert severity="info">
                    <Typography variant="body1">
                      <strong>Анализ файлов смет...</strong>
                    </Typography>
                    <Typography variant="body2">
                      Попытка извлечь базовую стоимость из загруженных файлов
                    </Typography>
                  </Alert>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Budget Settings */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                ⚙️ Параметры бюджета
              </Typography>

              <TextField
                fullWidth
                label="Название проекта"
                value={budgetParams.project_name}
                onChange={(e) => handleParamChange('project_name', e.target.value)}
                margin="normal"
                placeholder="Введите название проекта..."
              />

              <TextField
                fullWidth
                label="Базовая стоимость (материалы + работы)"
                type="number"
                value={budgetParams.base_cost}
                onChange={(e) => handleParamChange('base_cost', parseFloat(e.target.value) || 0)}
                margin="normal"
                inputProps={{ min: 1000, max: 100000000, step: 1000 }}
                InputProps={{
                  endAdornment: <span>₽</span>
                }}
              />

              <FormControl fullWidth margin="normal">
                <InputLabel>Тип проекта</InputLabel>
                <Select
                  value={budgetParams.project_type}
                  onChange={(e) => handleParamChange('project_type', e.target.value)}
                  label="Тип проекта"
                >
                  {projectTypes.map((type) => (
                    <MenuItem key={type.value} value={type.value}>
                      {type.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <Box mt={3}>
                <Button
                  fullWidth
                  variant="contained"
                  size="large"
                  onClick={startCalculation}
                  disabled={isAnalyzing || !budgetParams.project_name.trim() || budgetParams.base_cost <= 0}
                  startIcon={isAnalyzing ? <StopIcon /> : <CalculateIcon />}
                  color={isAnalyzing ? "error" : "primary"}
                >
                  {isAnalyzing ? 'Остановить расчет' : 'Рассчитать бюджет'}
                </Button>
              </Box>

              {isAnalyzing && (
                <Box mt={2}>
                  <Typography variant="body2" gutterBottom>
                    Прогресс расчета: {jobProgress}%
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={jobProgress} 
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Detailed Parameters */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                🛠️ Детальные параметры расчета
              </Typography>
              
              <Tabs
                value={activeTab}
                onChange={(e, newValue) => setActiveTab(newValue)}
                variant="scrollable"
                scrollButtons="auto"
              >
                {budgetParameters.map((category, index) => (
                  <Tab 
                    key={index} 
                    label={category.category} 
                    icon={category.icon}
                    iconPosition="start"
                  />
                ))}
              </Tabs>
              
              <Box mt={2}>
                <Grid container spacing={2}>
                  {budgetParameters[activeTab]?.params.map((param, index) => (
                    <Grid item xs={12} sm={6} md={4} key={index}>
                      {renderParamInput(param)}
                    </Grid>
                  ))}
                </Grid>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Analysis Results */}
        {analysisResults && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  📊 Результаты расчета бюджета
                </Typography>

                <Accordion defaultExpanded>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle1">Общая информация</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Grid container spacing={2}>
                      <Grid item xs={12} md={3}>
                        <Card variant="outlined">
                          <CardContent>
                            <Typography variant="h4" color="primary">
                              {formatCurrency(analysisResults.data?.budget?.total_revenue || 0)}
                            </Typography>
                            <Typography variant="body2">
                              Базовая стоимость
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                      <Grid item xs={12} md={3}>
                        <Card variant="outlined">
                          <CardContent>
                            <Typography variant="h4" color={analysisResults.data?.budget?.net_profit >= 0 ? "success.main" : "error.main"}>
                              {formatCurrency(analysisResults.data?.budget?.net_profit || 0)}
                            </Typography>
                            <Typography variant="body2">
                              Чистая прибыль
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                      <Grid item xs={12} md={3}>
                        <Card variant="outlined">
                          <CardContent>
                            <Typography variant="h4" color={analysisResults.data?.budget?.profit_margin >= 0 ? "success.main" : "error.main"}>
                              {analysisResults.data?.budget?.profit_margin?.toFixed(2) || 0}%
                            </Typography>
                            <Typography variant="body2">
                              Рентабельность
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                      <Grid item xs={12} md={3}>
                        <Card variant="outlined">
                          <CardContent>
                            <Typography variant="h4" color="secondary">
                              {formatCurrency(analysisResults.data?.budget?.total_expenses || 0)}
                            </Typography>
                            <Typography variant="body2">
                              Общие расходы
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                    </Grid>
                  </AccordionDetails>
                </Accordion>

                {analysisResults.data?.breakdown && (
                  <Accordion>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Typography variant="subtitle1">Детализация статей</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <TableContainer component={Paper}>
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell>Статья</TableCell>
                              <TableCell align="right">Сумма</TableCell>
                              <TableCell align="right">Процент от базовой стоимости</TableCell>
                              <TableCell>Категория</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {analysisResults.data.breakdown.map((item, index) => (
                              <TableRow key={index}>
                                <TableCell>{item.item}</TableCell>
                                <TableCell align="right">{item.amount}</TableCell>
                                <TableCell align="right">{item.percentage}</TableCell>
                                <TableCell>{item.category}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    </AccordionDetails>
                  </Accordion>
                )}

                {analysisResults.data?.recommendations && (
                  <Accordion>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Typography variant="subtitle1">Рекомендации</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <List>
                        {analysisResults.data.recommendations.map((rec, index) => (
                          <ListItem key={index}>
                            <ListItemText primary={rec} />
                          </ListItem>
                        ))}
                      </List>
                    </AccordionDetails>
                  </Accordion>
                )}

                <Box mt={2} display="flex" gap={2}>
                  <Button
                    variant="outlined"
                    startIcon={<DownloadIcon />}
                    onClick={() => {
                      // Download report
                      const blob = new Blob([JSON.stringify(analysisResults, null, 2)], 
                        { type: 'application/json' });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `budget_report_${budgetParams.project_name.replace(/\s+/g, '_')}.json`;
                      a.click();
                    }}
                  >
                    Скачать отчет
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<AssessmentIcon />}
                  >
                    Экспорт в Excel
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      {/* File Preview Dialog */}
      <Dialog 
        open={previewDialogOpen} 
        onClose={() => setPreviewDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Просмотр файла: {selectedFile?.name}
        </DialogTitle>
        <DialogContent>
          {selectedFile && (
            <Box>
              <Typography variant="body1" gutterBottom>
                <strong>Имя файла:</strong> {selectedFile.name}
              </Typography>
              <Typography variant="body1" gutterBottom>
                <strong>Размер:</strong> {formatFileSize(selectedFile.size)}
              </Typography>
              <Typography variant="body1" gutterBottom>
                <strong>Тип:</strong> {selectedFile.type || 'Неизвестен'}
              </Typography>
              <Typography variant="body1" gutterBottom>
                <strong>Загружен:</strong> {selectedFile.uploadedAt?.toLocaleString()}
              </Typography>
              
              <Alert severity="info" sx={{ mt: 2 }}>
                Предварительный просмотр содержимого файла будет доступен в следующих версиях
              </Alert>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviewDialogOpen(false)}>
            Закрыть
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AutoBudget;