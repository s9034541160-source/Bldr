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
  Paper
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
  Description as DocIcon
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';

const EstimateAnalyzer = ({ toolId, onJobStart, onJobComplete }) => {
  // State management
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [analysisParams, setAnalysisParams] = useState({
    region: 'moscow',
    analysisType: 'full',
    includeGESN: true,
    includeFER: false,
    checkCompliance: true,
    generateReport: true,
    currency: 'RUB',
    priceYear: '2024'
  });
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [jobProgress, setJobProgress] = useState(0);
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false);

  // Supported file types
  const supportedTypes = {
    '.xlsx': 'Excel файл',
    '.xls': 'Excel файл (старый формат)',
    '.pdf': 'PDF документ',
    '.csv': 'CSV файл',
    '.doc': 'Word документ',
    '.docx': 'Word документ'
  };

  // Regions configuration
  const regions = [
    { value: 'moscow', label: 'Москва' },
    { value: 'spb', label: 'Санкт-Петербург' },
    { value: 'ekaterinburg', label: 'Екатеринбург' },
    { value: 'novosibirsk', label: 'Новосибирск' },
    { value: 'kazan', label: 'Казань' }
  ];

  const analysisTypes = [
    { value: 'full', label: 'Полный анализ' },
    { value: 'quick', label: 'Быстрая проверка' },
    { value: 'compliance', label: 'Проверка соответствия' },
    { value: 'comparison', label: 'Сравнительный анализ' }
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

  // Start analysis
  const startAnalysis = async () => {
    if (uploadedFiles.length === 0) {
      alert('Загрузите файлы для анализа');
      return;
    }

    setIsAnalyzing(true);
    setJobProgress(0);
    setAnalysisResults(null);

    try {
      // Prepare form data
      const formData = new FormData();
      uploadedFiles.forEach((fileData, index) => {
        formData.append(`files`, fileData.file);
      });
      
      // Add analysis parameters
      formData.append('params', JSON.stringify(analysisParams));
      formData.append('tool', 'estimate_analyzer');

      // Start analysis job
      const response = await fetch('/api/tools/analyze/estimate', {
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
              } else if (progressData.status === 'failed') {
                clearInterval(progressInterval);
                setIsAnalyzing(false);
                alert('Ошибка анализа: ' + progressData.error);
              }
            }
          } catch (error) {
            console.error('Error polling job status:', error);
          }
        }, 1000);

      } else {
        setIsAnalyzing(false);
        alert('Ошибка запуска анализа: ' + result.error);
      }
    } catch (error) {
      setIsAnalyzing(false);
      console.error('Error starting analysis:', error);
      alert('Ошибка сети: ' + error.message);
    }
  };

  // Stop analysis
  const stopAnalysis = () => {
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

  return (
    <Box>
      <Grid container spacing={3}>
        {/* File Upload Section */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                📂 Загрузка файлов
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
            </CardContent>
          </Card>
        </Grid>

        {/* Analysis Settings */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                ⚙️ Настройки анализа
              </Typography>

              <FormControl fullWidth margin="normal">
                <InputLabel>Регион</InputLabel>
                <Select
                  value={analysisParams.region}
                  onChange={(e) => setAnalysisParams(prev => ({ ...prev, region: e.target.value }))}
                  label="Регион"
                >
                  {regions.map((region) => (
                    <MenuItem key={region.value} value={region.value}>
                      {region.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <FormControl fullWidth margin="normal">
                <InputLabel>Тип анализа</InputLabel>
                <Select
                  value={analysisParams.analysisType}
                  onChange={(e) => setAnalysisParams(prev => ({ ...prev, analysisType: e.target.value }))}
                  label="Тип анализа"
                >
                  {analysisTypes.map((type) => (
                    <MenuItem key={type.value} value={type.value}>
                      {type.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <TextField
                fullWidth
                label="Год ценообразования"
                type="number"
                value={analysisParams.priceYear}
                onChange={(e) => setAnalysisParams(prev => ({ ...prev, priceYear: e.target.value }))}
                margin="normal"
                inputProps={{ min: 2020, max: 2030 }}
              />

              <Divider sx={{ my: 2 }} />

              <Typography variant="subtitle2" gutterBottom>
                Дополнительные параметры
              </Typography>

              <FormControlLabel
                control={
                  <Switch
                    checked={analysisParams.includeGESN}
                    onChange={(e) => setAnalysisParams(prev => ({ ...prev, includeGESN: e.target.checked }))}
                  />
                }
                label="Включить ГЭСН расценки"
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={analysisParams.includeFER}
                    onChange={(e) => setAnalysisParams(prev => ({ ...prev, includeFER: e.target.checked }))}
                  />
                }
                label="Включить ФЕР расценки"
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={analysisParams.checkCompliance}
                    onChange={(e) => setAnalysisParams(prev => ({ ...prev, checkCompliance: e.target.checked }))}
                  />
                }
                label="Проверка соответствия"
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={analysisParams.generateReport}
                    onChange={(e) => setAnalysisParams(prev => ({ ...prev, generateReport: e.target.checked }))}
                  />
                }
                label="Генерировать отчет"
              />

              <Box mt={3}>
                <Button
                  fullWidth
                  variant="contained"
                  size="large"
                  onClick={startAnalysis}
                  disabled={isAnalyzing || uploadedFiles.length === 0}
                  startIcon={isAnalyzing ? <StopIcon /> : <PlayIcon />}
                  color={isAnalyzing ? "error" : "primary"}
                >
                  {isAnalyzing ? 'Остановить анализ' : 'Начать анализ'}
                </Button>
              </Box>

              {isAnalyzing && (
                <Box mt={2}>
                  <Typography variant="body2" gutterBottom>
                    Прогресс анализа: {jobProgress}%
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

        {/* Analysis Results */}
        {analysisResults && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  📊 Результаты анализа
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
                              {analysisResults.summary?.total_cost || 'N/A'}
                            </Typography>
                            <Typography variant="body2">
                              Общая стоимость
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                      <Grid item xs={12} md={3}>
                        <Card variant="outlined">
                          <CardContent>
                            <Typography variant="h4" color="secondary">
                              {analysisResults.summary?.items_count || 'N/A'}
                            </Typography>
                            <Typography variant="body2">
                              Количество позиций
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                      <Grid item xs={12} md={3}>
                        <Card variant="outlined">
                          <CardContent>
                            <Typography variant="h4" color="error">
                              {analysisResults.summary?.errors_count || '0'}
                            </Typography>
                            <Typography variant="body2">
                              Ошибки
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                      <Grid item xs={12} md={3}>
                        <Card variant="outlined">
                          <CardContent>
                            <Typography variant="h4" color="warning.main">
                              {analysisResults.summary?.warnings_count || '0'}
                            </Typography>
                            <Typography variant="body2">
                              Предупреждения
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                    </Grid>
                  </AccordionDetails>
                </Accordion>

                {analysisResults.details && (
                  <Accordion>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Typography variant="subtitle1">Детализация</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <TableContainer component={Paper}>
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell>Позиция</TableCell>
                              <TableCell>Единица измерения</TableCell>
                              <TableCell align="right">Количество</TableCell>
                              <TableCell align="right">Цена</TableCell>
                              <TableCell align="right">Сумма</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {analysisResults.details.slice(0, 10).map((item, index) => (
                              <TableRow key={index}>
                                <TableCell>{item.name || `Позиция ${index + 1}`}</TableCell>
                                <TableCell>{item.unit || 'шт'}</TableCell>
                                <TableCell align="right">{item.quantity || 0}</TableCell>
                                <TableCell align="right">{item.price || 0}</TableCell>
                                <TableCell align="right">{item.total || 0}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
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
                      a.download = 'estimate_analysis_report.json';
                      a.click();
                    }}
                  >
                    Скачать отчет
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<AssessmentIcon />}
                  >
                    Детальный анализ
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

export default EstimateAnalyzer;