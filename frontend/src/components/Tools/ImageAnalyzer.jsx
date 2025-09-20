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
  ImageList,
  ImageListItem,
  ImageListItemBar,
  Tooltip,
  Slider,
  FormGroup
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Delete as DeleteIcon,
  ZoomIn as ZoomInIcon,
  Download as DownloadIcon,
  Visibility as ViewIcon,
  ExpandMore as ExpandMoreIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Image as ImageIcon,
  Architecture as ArchitectureIcon,
  Build as BuildIcon,
  Straighten as MeasureIcon,
  CropFree as DetectionIcon,
  Palette as ColorIcon,
  Analytics as AnalyticsIcon
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';

const ImageAnalyzer = ({ toolId, onJobStart, onJobComplete }) => {
  // State management
  const [uploadedImages, setUploadedImages] = useState([]);
  const [analysisParams, setAnalysisParams] = useState({
    analysisType: 'comprehensive',
    detectObjects: true,
    extractDimensions: true,
    recognizeText: true,
    checkCompliance: false,
    imageQuality: 'high',
    outputFormat: 'detailed',
    language: 'ru',
    confidenceThreshold: 0.7
  });
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [jobProgress, setJobProgress] = useState(0);
  const [selectedImage, setSelectedImage] = useState(null);
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false);

  // Supported image types
  const supportedTypes = {
    'image/jpeg': 'JPEG изображение',
    'image/jpg': 'JPG изображение', 
    'image/png': 'PNG изображение',
    'image/tiff': 'TIFF изображение',
    'image/bmp': 'BMP изображение',
    'application/pdf': 'PDF с изображениями'
  };

  // Analysis types configuration
  const analysisTypes = [
    { 
      value: 'comprehensive', 
      label: 'Комплексный анализ',
      description: 'Полный анализ с распознаванием объектов, размеров и текста' 
    },
    { 
      value: 'object_detection', 
      label: 'Обнаружение объектов',
      description: 'Поиск и классификация строительных элементов' 
    },
    { 
      value: 'dimension_extraction', 
      label: 'Извлечение размеров',
      description: 'Распознавание размеров и масштабов' 
    },
    { 
      value: 'text_recognition', 
      label: 'Распознавание текста',
      description: 'OCR для извлечения текстовой информации' 
    },
    { 
      value: 'plan_analysis', 
      label: 'Анализ планов',
      description: 'Специализированный анализ архитектурных планов' 
    }
  ];

  const outputFormats = [
    { value: 'detailed', label: 'Подробный отчет' },
    { value: 'summary', label: 'Краткая сводка' },
    { value: 'technical', label: 'Технический отчет' },
    { value: 'visual', label: 'Визуальная разметка' }
  ];

  // File drop handling
  const onDrop = useCallback((acceptedFiles) => {
    const newImages = acceptedFiles.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      name: file.name,
      size: file.size,
      type: file.type,
      uploadedAt: new Date(),
      status: 'ready',
      preview: URL.createObjectURL(file)
    }));
    
    setUploadedImages(prev => [...prev, ...newImages]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.tiff', '.bmp'],
      'application/pdf': ['.pdf']
    },
    maxSize: 100 * 1024 * 1024 // 100MB
  });

  // Remove image
  const removeImage = (imageId) => {
    const imageToRemove = uploadedImages.find(img => img.id === imageId);
    if (imageToRemove?.preview) {
      URL.revokeObjectURL(imageToRemove.preview);
    }
    setUploadedImages(prev => prev.filter(img => img.id !== imageId));
  };

  // Preview image
  const previewImage = (image) => {
    setSelectedImage(image);
    setPreviewDialogOpen(true);
  };

  // Start analysis
  const startAnalysis = async () => {
    if (uploadedImages.length === 0) {
      alert('Загрузите изображения для анализа');
      return;
    }

    setIsAnalyzing(true);
    setJobProgress(0);
    setAnalysisResults(null);

    try {
      // Prepare form data
      const formData = new FormData();
      uploadedImages.forEach((imageData, index) => {
        formData.append(`images`, imageData.file);
      });
      
      // Add analysis parameters
      formData.append('params', JSON.stringify(analysisParams));
      formData.append('tool', 'image_analyzer');

      // Start analysis job
      const response = await fetch('/api/tools/analyze/images', {
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

  // Format file size
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Get analysis type icon
  const getAnalysisIcon = (analysisType) => {
    switch (analysisType) {
      case 'comprehensive': return <AnalyticsIcon />;
      case 'object_detection': return <DetectionIcon />;
      case 'dimension_extraction': return <MeasureIcon />;
      case 'text_recognition': return <ArchitectureIcon />;
      case 'plan_analysis': return <BuildIcon />;
      default: return <ImageIcon />;
    }
  };

  return (
    <Box>
      <Grid container spacing={3}>
        {/* Image Upload Section */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                🖼️ Загрузка изображений
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
                    ? 'Отпустите изображения здесь...' 
                    : 'Перетащите изображения сюда или нажмите для выбора'
                  }
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Поддерживаются: JPEG, PNG, TIFF, BMP, PDF
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Максимальный размер файла: 100 МБ
                </Typography>
              </Box>

              {/* Uploaded Images Gallery */}
              {uploadedImages.length > 0 && (
                <Box mt={3}>
                  <Typography variant="subtitle1" gutterBottom>
                    Загруженные изображения ({uploadedImages.length})
                  </Typography>
                  <ImageList cols={3} rowHeight={200}>
                    {uploadedImages.map((imageData) => (
                      <ImageListItem key={imageData.id}>
                        <img
                          src={imageData.preview}
                          alt={imageData.name}
                          loading="lazy"
                          style={{ 
                            height: 200, 
                            objectFit: 'cover',
                            cursor: 'pointer'
                          }}
                          onClick={() => previewImage(imageData)}
                        />
                        <ImageListItemBar
                          title={imageData.name}
                          subtitle={formatFileSize(imageData.size)}
                          actionIcon={
                            <Box>
                              <Tooltip title="Просмотр">
                                <IconButton
                                  sx={{ color: 'rgba(255, 255, 255, 0.54)' }}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    previewImage(imageData);
                                  }}
                                >
                                  <ZoomInIcon />
                                </IconButton>
                              </Tooltip>
                              <Tooltip title="Удалить">
                                <IconButton
                                  sx={{ color: 'rgba(255, 255, 255, 0.54)' }}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    removeImage(imageData.id);
                                  }}
                                >
                                  <DeleteIcon />
                                </IconButton>
                              </Tooltip>
                            </Box>
                          }
                        />
                      </ImageListItem>
                    ))}
                  </ImageList>
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
                <InputLabel>Тип анализа</InputLabel>
                <Select
                  value={analysisParams.analysisType}
                  onChange={(e) => setAnalysisParams(prev => ({ ...prev, analysisType: e.target.value }))}
                  label="Тип анализа"
                >
                  {analysisTypes.map((type) => (
                    <MenuItem key={type.value} value={type.value}>
                      <Box display="flex" alignItems="center" gap={1}>
                        {getAnalysisIcon(type.value)}
                        <Box>
                          <Typography variant="body2">{type.label}</Typography>
                          <Typography variant="caption" color="textSecondary">
                            {type.description}
                          </Typography>
                        </Box>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <FormControl fullWidth margin="normal">
                <InputLabel>Формат вывода</InputLabel>
                <Select
                  value={analysisParams.outputFormat}
                  onChange={(e) => setAnalysisParams(prev => ({ ...prev, outputFormat: e.target.value }))}
                  label="Формат вывода"
                >
                  {outputFormats.map((format) => (
                    <MenuItem key={format.value} value={format.value}>
                      {format.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <Box mt={2}>
                <Typography variant="subtitle2" gutterBottom>
                  Порог уверенности: {Math.round(analysisParams.confidenceThreshold * 100)}%
                </Typography>
                <Slider
                  value={analysisParams.confidenceThreshold}
                  onChange={(e, value) => setAnalysisParams(prev => ({ ...prev, confidenceThreshold: value }))}
                  min={0.1}
                  max={1.0}
                  step={0.1}
                  marks={[
                    { value: 0.3, label: '30%' },
                    { value: 0.5, label: '50%' },
                    { value: 0.7, label: '70%' },
                    { value: 0.9, label: '90%' }
                  ]}
                />
              </Box>

              <Divider sx={{ my: 2 }} />

              <Typography variant="subtitle2" gutterBottom>
                Возможности анализа
              </Typography>

              <FormGroup>
                <FormControlLabel
                  control={
                    <Switch
                      checked={analysisParams.detectObjects}
                      onChange={(e) => setAnalysisParams(prev => ({ ...prev, detectObjects: e.target.checked }))}
                    />
                  }
                  label={
                    <Box display="flex" alignItems="center" gap={1}>
                      <DetectionIcon fontSize="small" />
                      Обнаружение объектов
                    </Box>
                  }
                />

                <FormControlLabel
                  control={
                    <Switch
                      checked={analysisParams.extractDimensions}
                      onChange={(e) => setAnalysisParams(prev => ({ ...prev, extractDimensions: e.target.checked }))}
                    />
                  }
                  label={
                    <Box display="flex" alignItems="center" gap={1}>
                      <MeasureIcon fontSize="small" />
                      Извлечение размеров
                    </Box>
                  }
                />

                <FormControlLabel
                  control={
                    <Switch
                      checked={analysisParams.recognizeText}
                      onChange={(e) => setAnalysisParams(prev => ({ ...prev, recognizeText: e.target.checked }))}
                    />
                  }
                  label={
                    <Box display="flex" alignItems="center" gap={1}>
                      <ArchitectureIcon fontSize="small" />
                      Распознавание текста (OCR)
                    </Box>
                  }
                />

                <FormControlLabel
                  control={
                    <Switch
                      checked={analysisParams.checkCompliance}
                      onChange={(e) => setAnalysisParams(prev => ({ ...prev, checkCompliance: e.target.checked }))}
                    />
                  }
                  label={
                    <Box display="flex" alignItems="center" gap={1}>
                      <BuildIcon fontSize="small" />
                      Проверка соответствия нормам
                    </Box>
                  }
                />
              </FormGroup>

              <Box mt={3}>
                <Button
                  fullWidth
                  variant="contained"
                  size="large"
                  onClick={startAnalysis}
                  disabled={isAnalyzing || uploadedImages.length === 0}
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
                  🔍 Результаты анализа
                </Typography>

                <Accordion defaultExpanded>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle1">Сводка по изображениям</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Grid container spacing={2}>
                      {analysisResults.summary?.images?.map((imageResult, index) => (
                        <Grid item xs={12} md={6} key={index}>
                          <Card variant="outlined">
                            <CardContent>
                              <Typography variant="h6" gutterBottom>
                                {imageResult.filename}
                              </Typography>
                              
                              {imageResult.objects_detected && (
                                <Box mb={2}>
                                  <Typography variant="subtitle2" gutterBottom>
                                    Обнаруженные объекты:
                                  </Typography>
                                  <Box display="flex" flexWrap="wrap" gap={1}>
                                    {imageResult.objects_detected.map((obj, objIndex) => (
                                      <Chip 
                                        key={objIndex}
                                        label={`${obj.type} (${Math.round(obj.confidence * 100)}%)`}
                                        size="small"
                                        color="primary"
                                        variant="outlined"
                                      />
                                    ))}
                                  </Box>
                                </Box>
                              )}

                              {imageResult.dimensions_found && (
                                <Box mb={2}>
                                  <Typography variant="subtitle2" gutterBottom>
                                    Найденные размеры:
                                  </Typography>
                                  <List dense>
                                    {imageResult.dimensions_found.slice(0, 3).map((dim, dimIndex) => (
                                      <ListItem key={dimIndex} disablePadding>
                                        <ListItemText 
                                          primary={`${dim.value} ${dim.unit}`}
                                          secondary={dim.description}
                                        />
                                      </ListItem>
                                    ))}
                                  </List>
                                </Box>
                              )}

                              {imageResult.text_recognized && (
                                <Box>
                                  <Typography variant="subtitle2" gutterBottom>
                                    Распознанный текст:
                                  </Typography>
                                  <Typography variant="body2" color="textSecondary">
                                    {imageResult.text_recognized.substring(0, 100)}
                                    {imageResult.text_recognized.length > 100 ? '...' : ''}
                                  </Typography>
                                </Box>
                              )}
                            </CardContent>
                          </Card>
                        </Grid>
                      ))}
                    </Grid>
                  </AccordionDetails>
                </Accordion>

                {analysisResults.technical_analysis && (
                  <Accordion>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Typography variant="subtitle1">Технический анализ</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Box>
                        <Typography variant="body1" paragraph>
                          {analysisResults.technical_analysis.description}
                        </Typography>
                        
                        {analysisResults.technical_analysis.recommendations && (
                          <Box>
                            <Typography variant="subtitle2" gutterBottom>
                              Рекомендации:
                            </Typography>
                            <List>
                              {analysisResults.technical_analysis.recommendations.map((rec, index) => (
                                <ListItem key={index}>
                                  <ListItemText primary={rec} />
                                </ListItem>
                              ))}
                            </List>
                          </Box>
                        )}
                      </Box>
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
                      a.download = 'image_analysis_report.json';
                      a.click();
                    }}
                  >
                    Скачать отчет
                  </Button>
                  
                  {analysisResults.annotated_images && (
                    <Button
                      variant="outlined"
                      startIcon={<ViewIcon />}
                      onClick={() => {
                        // View annotated images
                        window.open(analysisResults.annotated_images.download_url, '_blank');
                      }}
                    >
                      Размеченные изображения
                    </Button>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      {/* Image Preview Dialog */}
      <Dialog 
        open={previewDialogOpen} 
        onClose={() => setPreviewDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          Просмотр изображения: {selectedImage?.name}
        </DialogTitle>
        <DialogContent>
          {selectedImage && (
            <Box>
              <Box display="flex" justifyContent="center" mb={2}>
                <img
                  src={selectedImage.preview}
                  alt={selectedImage.name}
                  style={{ 
                    maxWidth: '100%', 
                    maxHeight: '500px', 
                    objectFit: 'contain' 
                  }}
                />
              </Box>
              
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" gutterBottom>
                    <strong>Имя файла:</strong> {selectedImage.name}
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    <strong>Размер:</strong> {formatFileSize(selectedImage.size)}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" gutterBottom>
                    <strong>Тип:</strong> {selectedImage.type}
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    <strong>Загружено:</strong> {selectedImage.uploadedAt?.toLocaleString()}
                  </Typography>
                </Grid>
              </Grid>
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

export default ImageAnalyzer;