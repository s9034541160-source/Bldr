import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Chip,
  Alert,
  CircularProgress,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tab,
  Tabs,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
  Settings as SettingsIcon,
  Timeline as TimelineIcon,
  Assessment as AssessmentIcon,
  Construction as ConstructionIcon,
  Build as BuildIcon,
  AutoGraph as AutoGraphIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  Info as InfoIcon
} from '@mui/icons-material';

const MetaToolsInterface = ({ onExecute, onStatusCheck }) => {
  // State management
  const [selectedTool, setSelectedTool] = useState('');
  const [toolParams, setToolParams] = useState({});
  const [metaTools, setMetaTools] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredTools, setFilteredTools] = useState([]);
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState(null);
  const [activeTasks, setActiveTasks] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  const [taskDetails, setTaskDetails] = useState(null);
  const [detailsOpen, setDetailsOpen] = useState(false);

  // Meta-tool categories with icons
  const categoryIcons = {
    'analysis': <AssessmentIcon />,
    'planning': <TimelineIcon />,
    'reporting': <InfoIcon />,
    'automation': <BuildIcon />,
    'optimization': <AutoGraphIcon />,
    'all': <SettingsIcon />
  };

  const complexityColors = {
    'low': '#4caf50',
    'medium': '#ff9800', 
    'high': '#f44336'
  };

  // Load meta-tools on component mount
  useEffect(() => {
    loadMetaTools();
    loadActiveTasks();
    // Set up polling for active tasks
    const interval = setInterval(loadActiveTasks, 5000);
    return () => clearInterval(interval);
  }, []);

  // Filter tools based on search and category
  useEffect(() => {
    let filtered = metaTools;
    
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(tool => tool.category === selectedCategory);
    }
    
    if (searchQuery.trim()) {
      filtered = filtered.filter(tool => 
        tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        tool.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        tool.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
      );
    }
    
    setFilteredTools(filtered);
  }, [metaTools, searchQuery, selectedCategory]);

  // API calls
  const loadMetaTools = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/meta-tools/list');
      const data = await response.json();
      
      if (data.success) {
        setMetaTools(data.meta_tools || []);
      } else {
        console.error('Failed to load meta-tools:', data.error);
      }
    } catch (error) {
      console.error('Error loading meta-tools:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadActiveTasks = async () => {
    try {
      const response = await fetch('/api/meta-tools/tasks/active');
      const data = await response.json();
      
      if (data.success) {
        setActiveTasks(data.tasks || []);
      }
    } catch (error) {
      console.error('Error loading active tasks:', error);
    }
  };

  const executeMetaTool = async () => {
    if (!selectedTool) {
      alert('Выберите мета-инструмент для выполнения');
      return;
    }

    const tool = metaTools.find(t => t.name === selectedTool);
    if (!tool) return;

    // Validate required parameters
    const missingParams = tool.required_params.filter(param => !toolParams[param] || toolParams[param].trim() === '');
    if (missingParams.length > 0) {
      alert(`Не заполнены обязательные параметры: ${missingParams.join(', ')}`);
      return;
    }

    setExecuting(true);
    setExecutionResult(null);

    try {
      // For complex tools, use async execution
      const useAsync = tool.estimated_time > 5 || tool.complexity === 'high';
      
      const endpoint = useAsync ? '/api/meta-tools/execute/async' : '/api/meta-tools/execute';
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tool_name: selectedTool,
          params: toolParams,
          priority: tool.complexity === 'high' ? 8 : 5
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        if (useAsync) {
          // For async execution, show task ID and start polling
          setExecutionResult({
            type: 'async',
            task_id: data.task_id,
            message: `Задача запущена асинхронно. ID: ${data.task_id}`
          });
          loadActiveTasks(); // Refresh active tasks
        } else {
          // For sync execution, show result immediately
          setExecutionResult({
            type: 'sync',
            result: data.result,
            message: 'Выполнение завершено'
          });
        }
      } else {
        setExecutionResult({
          type: 'error',
          error: data.error,
          message: 'Ошибка выполнения'
        });
      }
    } catch (error) {
      setExecutionResult({
        type: 'error',
        error: error.message,
        message: 'Ошибка сети или сервера'
      });
    } finally {
      setExecuting(false);
    }
  };

  const cancelTask = async (taskId) => {
    try {
      const response = await fetch(`/api/meta-tools/tasks/${taskId}/cancel`, {
        method: 'POST'
      });
      
      const data = await response.json();
      if (data.success) {
        loadActiveTasks(); // Refresh active tasks
      }
    } catch (error) {
      console.error('Error canceling task:', error);
    }
  };

  const getTaskDetails = async (taskId) => {
    try {
      const response = await fetch(`/api/meta-tools/tasks/${taskId}/status`);
      const data = await response.json();
      
      if (data.success) {
        setTaskDetails(data.status);
        setDetailsOpen(true);
      }
    } catch (error) {
      console.error('Error getting task details:', error);
    }
  };

  // Handle parameter changes
  const handleParamChange = (paramName, value) => {
    setToolParams(prev => ({
      ...prev,
      [paramName]: value
    }));
  };

  // Render parameter input based on parameter name/type
  const renderParameterInput = (paramName, isRequired = false) => {
    const value = toolParams[paramName] || '';
    
    // Special handling for common parameter types
    if (paramName.includes('timeline') || paramName.includes('months')) {
      return (
        <TextField
          key={paramName}
          label={`${paramName} ${isRequired ? '*' : ''}`}
          type="number"
          value={value}
          onChange={(e) => handleParamChange(paramName, parseInt(e.target.value) || '')}
          fullWidth
          margin="normal"
          InputProps={{ inputProps: { min: 1, max: 60 } }}
          helperText="Количество месяцев"
        />
      );
    }
    
    if (paramName.includes('budget') || paramName.includes('limit')) {
      return (
        <TextField
          key={paramName}
          label={`${paramName} ${isRequired ? '*' : ''}`}
          type="number"
          value={value}
          onChange={(e) => handleParamChange(paramName, parseFloat(e.target.value) || '')}
          fullWidth
          margin="normal"
          InputProps={{ inputProps: { min: 0 } }}
          helperText="Сумма в рублях"
        />
      );
    }
    
    if (paramName.includes('type') || paramName.includes('category')) {
      const options = paramName.includes('project_type') 
        ? ['жилое строительство', 'коммерческое строительство', 'промышленное строительство', 'инфраструктура']
        : paramName.includes('building_type')
        ? ['многоэтажное', 'малоэтажное', 'высотное', 'производственное']
        : ['тип 1', 'тип 2', 'тип 3'];
        
      return (
        <FormControl key={paramName} fullWidth margin="normal">
          <InputLabel>{`${paramName} ${isRequired ? '*' : ''}`}</InputLabel>
          <Select
            value={value}
            onChange={(e) => handleParamChange(paramName, e.target.value)}
            label={`${paramName} ${isRequired ? '*' : ''}`}
          >
            {options.map(option => (
              <MenuItem key={option} value={option}>{option}</MenuItem>
            ))}
          </Select>
        </FormControl>
      );
    }
    
    if (paramName.includes('requirements') || paramName.includes('list')) {
      return (
        <TextField
          key={paramName}
          label={`${paramName} ${isRequired ? '*' : ''}`}
          value={value}
          onChange={(e) => handleParamChange(paramName, e.target.value.split(',').map(s => s.trim()).filter(s => s))}
          fullWidth
          margin="normal"
          multiline
          rows={2}
          helperText="Введите элементы через запятую"
        />
      );
    }
    
    // Default text input
    return (
      <TextField
        key={paramName}
        label={`${paramName} ${isRequired ? '*' : ''}`}
        value={value}
        onChange={(e) => handleParamChange(paramName, e.target.value)}
        fullWidth
        margin="normal"
        multiline={paramName.includes('description')}
        rows={paramName.includes('description') ? 3 : 1}
      />
    );
  };

  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'success':
      case 'completed':
        return <CheckCircleIcon style={{ color: '#4caf50' }} />;
      case 'failed':
      case 'error':
        return <ErrorIcon style={{ color: '#f44336' }} />;
      case 'running':
      case 'started':
        return <CircularProgress size={20} />;
      default:
        return <ScheduleIcon style={{ color: '#ff9800' }} />;
    }
  };

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        🔧 Meta-Tools System
      </Typography>
      
      <Typography variant="body1" color="textSecondary" paragraph>
        Система мета-инструментов для выполнения комплексных строительных анализов и автоматизации сложных процессов.
      </Typography>

      <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)} sx={{ mb: 3 }}>
        <Tab label="Выполнение" />
        <Tab label="Активные задачи" />
        <Tab label="История" />
      </Tabs>

      {/* Tab 0: Execution */}
      {tabValue === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Выбор и настройка мета-инструмента
                </Typography>
                
                {/* Search and filters */}
                <Box mb={2}>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="Поиск мета-инструментов"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        InputProps={{
                          startAdornment: <SearchIcon style={{ marginRight: 8, color: '#666' }} />
                        }}
                      />
                    </Grid>
                    <Grid item xs={12} md={4}>
                      <FormControl fullWidth>
                        <InputLabel>Категория</InputLabel>
                        <Select
                          value={selectedCategory}
                          onChange={(e) => setSelectedCategory(e.target.value)}
                          label="Категория"
                        >
                          <MenuItem value="all">Все категории</MenuItem>
                          <MenuItem value="analysis">Анализ</MenuItem>
                          <MenuItem value="planning">Планирование</MenuItem>
                          <MenuItem value="automation">Автоматизация</MenuItem>
                          <MenuItem value="optimization">Оптимизация</MenuItem>
                          <MenuItem value="reporting">Отчетность</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid item xs={12} md={2}>
                      <Button
                        fullWidth
                        variant="outlined"
                        onClick={loadMetaTools}
                        startIcon={<RefreshIcon />}
                        disabled={loading}
                      >
                        Обновить
                      </Button>
                    </Grid>
                  </Grid>
                </Box>

                {/* Meta-tools list */}
                {loading ? (
                  <Box display="flex" justifyContent="center" p={3}>
                    <CircularProgress />
                  </Box>
                ) : (
                  <Box mb={3}>
                    {filteredTools.map((tool) => (
                      <Accordion
                        key={tool.name}
                        expanded={selectedTool === tool.name}
                        onChange={() => setSelectedTool(selectedTool === tool.name ? '' : tool.name)}
                      >
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                          <Box display="flex" alignItems="center" width="100%">
                            {categoryIcons[tool.category] || <SettingsIcon />}
                            <Box ml={2} flexGrow={1}>
                              <Typography variant="subtitle1" fontWeight="bold">
                                {tool.name}
                              </Typography>
                              <Typography variant="body2" color="textSecondary">
                                {tool.description}
                              </Typography>
                            </Box>
                            <Box display="flex" alignItems="center" gap={1}>
                              <Chip
                                label={tool.category}
                                size="small"
                                color="primary"
                                variant="outlined"
                              />
                              <Chip
                                label={tool.complexity}
                                size="small"
                                style={{
                                  backgroundColor: complexityColors[tool.complexity],
                                  color: 'white'
                                }}
                              />
                              <Chip
                                label={`~${tool.estimated_time} мин`}
                                size="small"
                                variant="outlined"
                              />
                            </Box>
                          </Box>
                        </AccordionSummary>
                        <AccordionDetails>
                          <Box>
                            <Typography variant="body2" paragraph>
                              {tool.description}
                            </Typography>
                            
                            <Typography variant="subtitle2" gutterBottom>
                              Обязательные параметры:
                            </Typography>
                            {tool.required_params.map(param => renderParameterInput(param, true))}
                            
                            {tool.optional_params.length > 0 && (
                              <>
                                <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                                  Дополнительные параметры:
                                </Typography>
                                {tool.optional_params.map(param => renderParameterInput(param, false))}
                              </>
                            )}
                            
                            <Box display="flex" gap={1} flexWrap="wrap" mt={2}>
                              {tool.tags.map(tag => (
                                <Chip key={tag} label={tag} size="small" variant="outlined" />
                              ))}
                            </Box>
                          </Box>
                        </AccordionDetails>
                      </Accordion>
                    ))}
                  </Box>
                )}

                {/* Execution button */}
                <Box textAlign="center" mt={3}>
                  <Button
                    variant="contained"
                    color="primary"
                    size="large"
                    onClick={executeMetaTool}
                    disabled={!selectedTool || executing}
                    startIcon={executing ? <CircularProgress size={20} /> : <PlayIcon />}
                  >
                    {executing ? 'Выполняется...' : 'Запустить мета-инструмент'}
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Results panel */}
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Результат выполнения
                </Typography>
                
                {executionResult ? (
                  <Box>
                    {executionResult.type === 'async' && (
                      <Alert severity="info" sx={{ mb: 2 }}>
                        <Typography variant="body2">
                          Задача запущена асинхронно
                        </Typography>
                        <Typography variant="caption">
                          ID: {executionResult.task_id}
                        </Typography>
                      </Alert>
                    )}
                    
                    {executionResult.type === 'sync' && (
                      <Alert severity="success" sx={{ mb: 2 }}>
                        <Typography variant="body2">
                          Выполнение завершено успешно
                        </Typography>
                      </Alert>
                    )}
                    
                    {executionResult.type === 'error' && (
                      <Alert severity="error" sx={{ mb: 2 }}>
                        <Typography variant="body2">
                          {executionResult.message}
                        </Typography>
                        <Typography variant="caption">
                          {executionResult.error}
                        </Typography>
                      </Alert>
                    )}
                    
                    {executionResult.result && (
                      <Paper elevation={1} sx={{ p: 2, mt: 2 }}>
                        <pre style={{ whiteSpace: 'pre-wrap', fontSize: '12px' }}>
                          {JSON.stringify(executionResult.result, null, 2)}
                        </pre>
                      </Paper>
                    )}
                  </Box>
                ) : (
                  <Typography variant="body2" color="textSecondary">
                    Результаты выполнения будут отображены здесь
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Tab 1: Active Tasks */}
      {tabValue === 1 && (
        <Card>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                Активные задачи ({activeTasks.length})
              </Typography>
              <Button
                variant="outlined"
                onClick={loadActiveTasks}
                startIcon={<RefreshIcon />}
              >
                Обновить
              </Button>
            </Box>
            
            {activeTasks.length === 0 ? (
              <Typography variant="body2" color="textSecondary">
                Нет активных задач
              </Typography>
            ) : (
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Статус</TableCell>
                      <TableCell>ID задачи</TableCell>
                      <TableCell>Тип</TableCell>
                      <TableCell>Прогресс</TableCell>
                      <TableCell>Действия</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {activeTasks.map((task) => (
                      <TableRow key={task.task_id}>
                        <TableCell>
                          {getStatusIcon(task.status)}
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" fontFamily="monospace">
                            {task.task_id.substring(0, 8)}...
                          </Typography>
                        </TableCell>
                        <TableCell>{task.name || 'Unknown'}</TableCell>
                        <TableCell>
                          {task.progress && (
                            <Box>
                              <LinearProgress
                                variant="determinate"
                                value={task.progress.current / task.progress.total * 100}
                              />
                              <Typography variant="caption">
                                {task.progress.status}
                              </Typography>
                            </Box>
                          )}
                        </TableCell>
                        <TableCell>
                          <Box display="flex" gap={1}>
                            <IconButton
                              size="small"
                              onClick={() => getTaskDetails(task.task_id)}
                              title="Детали"
                            >
                              <InfoIcon />
                            </IconButton>
                            {task.status === 'STARTED' && (
                              <IconButton
                                size="small"
                                onClick={() => cancelTask(task.task_id)}
                                title="Отменить"
                                color="error"
                              >
                                <StopIcon />
                              </IconButton>
                            )}
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        </Card>
      )}

      {/* Task Details Dialog */}
      <Dialog open={detailsOpen} onClose={() => setDetailsOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Детали задачи</DialogTitle>
        <DialogContent>
          {taskDetails && (
            <Box>
              <Typography variant="body2" paragraph>
                <strong>ID:</strong> {taskDetails.task_id}
              </Typography>
              <Typography variant="body2" paragraph>
                <strong>Статус:</strong> {taskDetails.status}
              </Typography>
              {taskDetails.progress && (
                <Box mb={2}>
                  <Typography variant="body2" gutterBottom>
                    <strong>Прогресс:</strong>
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={taskDetails.progress.current / taskDetails.progress.total * 100}
                  />
                  <Typography variant="caption">
                    {taskDetails.progress.status}
                  </Typography>
                </Box>
              )}
              {taskDetails.result && (
                <Box>
                  <Typography variant="body2" gutterBottom>
                    <strong>Результат:</strong>
                  </Typography>
                  <Paper elevation={1} sx={{ p: 2 }}>
                    <pre style={{ whiteSpace: 'pre-wrap', fontSize: '12px' }}>
                      {JSON.stringify(taskDetails.result, null, 2)}
                    </pre>
                  </Paper>
                </Box>
              )}
              {taskDetails.error && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  <Typography variant="body2">
                    <strong>Ошибка:</strong> {taskDetails.error}
                  </Typography>
                </Alert>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>Закрыть</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default MetaToolsInterface;