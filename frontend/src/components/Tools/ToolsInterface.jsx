import React, { useState, useEffect } from 'react';
import {
  Box,
  Tabs,
  Tab,
  Typography,
  Paper,
  Badge,
  IconButton,
  Tooltip,
  Alert,
  Snackbar
} from '@mui/material';
import {
  Description as DocumentIcon,
  Assessment as AnalysisIcon,
  Calculate as CalculateIcon,
  Image as ImageIcon,
  Business as BusinessIcon,
  Construction as ConstructionIcon,
  Timeline as TimelineIcon,
  Email as EmailIcon,
  PictureAsPdf as PdfIcon,
  TableChart as TableIcon,
  Security as SecurityIcon,
  Engineering as EngineeringIcon,
  Settings as SettingsIcon,
  Notifications as NotificationsIcon,
  AccountBalance as BudgetIcon
} from '@mui/icons-material';

// Import specialized tool components
import EstimateAnalyzer from './EstimateAnalyzer';
import DocumentAnalyzer from './DocumentAnalyzer';
import ImageAnalyzer from './ImageAnalyzer';
import NormativeChecker from './NormativeChecker';
import ProjectPlanner from './ProjectPlanner';
import ReportGenerator from './ReportGenerator';
import LetterGenerator from './LetterGenerator';
import BIMAnalyzer from './BIMAnalyzer';
import FinancialAnalyzer from './FinancialAnalyzer';
import ComplianceChecker from './ComplianceChecker';
import AutoBudget from './AutoBudget';

const ToolsInterface = () => {
  const [selectedTab, setSelectedTab] = useState(0);
  const [activeJobs, setActiveJobs] = useState({});
  const [notifications, setNotifications] = useState([]);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');

  // Конфигурация инструментов с иконками и описаниями
  const toolsConfig = [
    {
      id: 'estimate',
      name: 'Анализ смет',
      icon: <CalculateIcon />,
      description: 'Загрузка и анализ сметной документации',
      component: EstimateAnalyzer,
      color: '#2196F3'
    },
    {
      id: 'budget',
      name: 'Автобюджет',
      icon: <BudgetIcon />,
      description: 'Автоматический расчет строительного бюджета',
      component: AutoBudget,
      color: '#4CAF50'
    },
    {
      id: 'documents',
      name: 'Анализ документов',
      icon: <DocumentIcon />,
      description: 'Обработка проектной документации и извлечение данных',
      component: DocumentAnalyzer,
      color: '#4CAF50'
    },
    {
      id: 'images',
      name: 'Анализ изображений',
      icon: <ImageIcon />,
      description: 'Анализ чертежей, планов и фотографий объектов',
      component: ImageAnalyzer,
      color: '#FF9800'
    },
    {
      id: 'norms',
      name: 'Проверка норм',
      icon: <SecurityIcon />,
      description: 'Проверка соответствия СП, ГОСТ, СНиП',
      component: NormativeChecker,
      color: '#F44336'
    },
    {
      id: 'planning',
      name: 'Планирование',
      icon: <TimelineIcon />,
      description: 'Создание графиков работ и планов проектов',
      component: ProjectPlanner,
      color: '#9C27B0'
    },
    {
      id: 'reports',
      name: 'Генерация отчетов',
      icon: <TableIcon />,
      description: 'Создание отчетов и аналитических документов',
      component: ReportGenerator,
      color: '#607D8B'
    },
    {
      id: 'letters',
      name: 'Официальные письма',
      icon: <EmailIcon />,
      description: 'Создание деловой корреспонденции',
      component: LetterGenerator,
      color: '#795548'
    },
    {
      id: 'bim',
      name: 'BIM анализ',
      icon: <EngineeringIcon />,
      description: 'Анализ BIM моделей и IFC файлов',
      component: BIMAnalyzer,
      color: '#3F51B5'
    },
    {
      id: 'financial',
      name: 'Финансовый анализ',
      icon: <BusinessIcon />,
      description: 'ROI, NPV, анализ рентабельности',
      component: FinancialAnalyzer,
      color: '#009688'
    },
    {
      id: 'compliance',
      name: 'Комплаенс',
      icon: <ConstructionIcon />,
      description: 'Проверка соответствия требованиям',
      component: ComplianceChecker,
      color: '#8BC34A'
    }
  ];

  // Получение активных задач
  useEffect(() => {
    const fetchActiveJobs = async () => {
      try {
        const response = await fetch('/api/tools/jobs/active');
        const data = await response.json();
        if (data.success) {
          setActiveJobs(data.jobs || {});
        }
      } catch (error) {
        console.error('Error fetching active jobs:', error);
      }
    };

    fetchActiveJobs();
    // Обновляем каждые 5 секунд
    const interval = setInterval(fetchActiveJobs, 5000);
    return () => clearInterval(interval);
  }, []);

  // WebSocket для уведомлений о завершении задач
  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/tools-notifications`);
    
    ws.onmessage = (event) => {
      const notification = JSON.parse(event.data);
      setNotifications(prev => [notification, ...prev.slice(0, 4)]);
      setSnackbarMessage(`${notification.tool}: ${notification.message}`);
      setSnackbarOpen(true);
    };

    ws.onclose = () => {
      console.log('WebSocket connection closed');
    };

    return () => {
      ws.close();
    };
  }, []);

  const handleTabChange = (event, newValue) => {
    setSelectedTab(newValue);
  };

  const handleCloseSnackbar = () => {
    setSnackbarOpen(false);
  };

  const getJobCount = (toolId) => {
    return activeJobs[toolId] ? activeJobs[toolId].length : 0;
  };

  const CurrentToolComponent = toolsConfig[selectedTab]?.component || (() => <div>Инструмент не найден</div>);

  return (
    <Box sx={{ width: '100%', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper elevation={2} sx={{ mb: 2 }}>
        <Box p={2} display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography variant="h4" gutterBottom>
              🛠️ Инструменты SuperBuilder
            </Typography>
            <Typography variant="body1" color="textSecondary">
              Специализированные интерфейсы для работы с различными типами строительных данных
            </Typography>
          </Box>
          
          {/* Notifications icon */}
          <Tooltip title="Уведомления">
            <IconButton>
              <Badge badgeContent={notifications.length} color="error">
                <NotificationsIcon />
              </Badge>
            </IconButton>
          </Tooltip>
        </Box>
      </Paper>

      {/* Tools Tabs */}
      <Paper elevation={1} sx={{ flexShrink: 0 }}>
        <Tabs
          value={selectedTab}
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
          sx={{
            '& .MuiTab-root': {
              minHeight: 72,
              textTransform: 'none'
            }
          }}
        >
          {toolsConfig.map((tool, index) => (
            <Tab
              key={tool.id}
              label={
                <Badge badgeContent={getJobCount(tool.id)} color="secondary">
                  <Box display="flex" flexDirection="column" alignItems="center" gap={0.5}>
                    <Box sx={{ color: tool.color }}>
                      {tool.icon}
                    </Box>
                    <Typography variant="caption" sx={{ lineHeight: 1 }}>
                      {tool.name}
                    </Typography>
                  </Box>
                </Badge>
              }
              sx={{
                '&.Mui-selected': {
                  backgroundColor: `${tool.color}15`,
                  borderBottom: `3px solid ${tool.color}`
                }
              }}
            />
          ))}
        </Tabs>
      </Paper>

      {/* Tool Interface Area */}
      <Box sx={{ flexGrow: 1, overflow: 'hidden', mt: 2 }}>
        <Paper elevation={1} sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
          {/* Tool Header */}
          <Box p={2} borderBottom="1px solid #e0e0e0">
            <Box display="flex" alignItems="center" gap={2}>
              <Box sx={{ color: toolsConfig[selectedTab]?.color }}>
                {toolsConfig[selectedTab]?.icon}
              </Box>
              <Box>
                <Typography variant="h6">
                  {toolsConfig[selectedTab]?.name}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  {toolsConfig[selectedTab]?.description}
                </Typography>
              </Box>
            </Box>
          </Box>

          {/* Tool Component */}
          <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
            <CurrentToolComponent 
              toolId={toolsConfig[selectedTab]?.id}
              onJobStart={(jobId) => {
                // Handle job start
                console.log('Job started:', jobId);
              }}
              onJobComplete={(jobId, result) => {
                // Handle job completion
                console.log('Job completed:', jobId, result);
              }}
            />
          </Box>
        </Paper>
      </Box>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseSnackbar} severity="info" sx={{ width: '100%' }}>
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default ToolsInterface;