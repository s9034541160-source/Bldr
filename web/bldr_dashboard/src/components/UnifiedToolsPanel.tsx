/**
 * Unified Tools Panel Component
 * Displays all 55 tools with **kwargs support and UI placement optimization
 */

import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Tabs, 
  Input, 
  Select, 
  Button, 
  Space, 
  Tag, 
  Spin, 
  Alert, 
  Modal, 
  Form, 
  message,
  Row,
  Col,
  Tooltip,
  Badge,
  Divider,
  Drawer
} from 'antd';
import { 
  SearchOutlined, 
  ReloadOutlined, 
  ToolOutlined, 
  DashboardOutlined,
  SettingOutlined,
  StarOutlined,
  StarFilled,
  PlayCircleOutlined,
  InfoCircleOutlined,
  HistoryOutlined,
  DollarOutlined,
  FileTextOutlined,
  ScheduleOutlined,
  BarChartOutlined,
  EyeOutlined,
  AudioOutlined,
  PlusOutlined,
  CloseOutlined
} from '@ant-design/icons';
import { apiService } from '../services/api';
import ToolTabsManager from './ToolTabsManager';
import { useToolTabs } from '../contexts/ToolTabsContext';
import { useTranslation } from '../contexts/LocalizationContext';
import { groupToolsByCategory, getPopularTools } from '../utils/toolCategorization';
import ToolCategorySection from './ToolCategorySection';
import PopularToolsSection from './PopularToolsSection';
import { 
  ToolConfigGenerateLetter,
  ToolConfigAnalyzeTender,
  ToolConfigAnalyzeImage,
  ToolConfigCalculateEstimate,
  ToolConfigAutoBudget,
  ToolConfigSearchRAG,
  ToolConfigTextToSpeech
} from './tool-configs/Configs';
import ToolResultDisplay from './ToolResultDisplay';
import ToolManifestEditor from './ToolManifestEditor';
import DynamicToolForm from './DynamicToolForm';
import ToolExecutionHistory from './ToolExecutionHistory';
import ToolTabsManager from './ToolTabsManager';
import ErrorBoundary from './ErrorBoundary';

const { TabPane } = Tabs;
const { Option } = Select;
const { TextArea } = Input;

interface ToolInfo {
  name: string;
  category: string;
  description: string;
  ui_placement: 'dashboard' | 'tools' | 'service';
  available: boolean;
  source: string;
}

interface StandardResponse {
  status: 'success' | 'error' | 'warning';
  data?: any;
  files?: string[];
  metadata?: {
    processing_time?: number;
    parameters_used?: Record<string, any>;
    error_category?: string;
    suggestions?: string;
  };
  error?: string;
  execution_time?: number;
  tool_name: string;
  timestamp: string;
}

interface ToolsDiscoveryResponse {
  status: string;
  data: {
    tools: Record<string, ToolInfo>;
    total_count: number;
    categories: Record<string, number>;
  };
  timestamp: string;
}

const UnifiedToolsPanel: React.FC = () => {
  const [tools, setTools] = useState<Record<string, ToolInfo>>({});
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [activeTab, setActiveTab] = useState<'dashboard' | 'tools' | 'history' | 'tabs'>('dashboard');
  const t = useTranslation();
  const [favorites, setFavorites] = useState<Set<string>>(new Set());
  const [executingTool, setExecutingTool] = useState<string | null>(null);
  const [toolModalVisible, setToolModalVisible] = useState(false);
  const [selectedTool, setSelectedTool] = useState<ToolInfo | null>(null);
  const [toolParams, setToolParams] = useState<Record<string, any>>({});
  const [manifestEditorOpen, setManifestEditorOpen] = useState(false);
  const [selectedManifest, setSelectedManifest] = useState<any>(null);
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
  const [lastResults, setLastResults] = useState<Record<string, StandardResponse>>({});
  const [showHistory, setShowHistory] = useState(false);
  
  // Используем глобальный контекст для боковой панели
  const { toolTabs, tabsDrawerVisible, setTabsDrawerVisible, openToolInNewTab } = useToolTabs();

  // Load tools on component mount
  useEffect(() => {
    loadTools();
    loadFavorites();
    // Subscribe to registry SSE for live updates - FIXED (auth now supports query params)
    try {
      const token = localStorage.getItem('auth-token') || '';
      console.log('SSE Token:', token); // DEBUG
      if (!token) {
        console.warn('No token found for SSE connection');
        return;
      }
      const url = `http://localhost:8000/api/tools/registry/stream?token=${encodeURIComponent(token)}`;
      const es = new EventSource(url);
      es.onmessage = (_ev) => {
        // naive: just refresh list on any event
        loadTools();
      };
      es.onerror = () => {};
      return () => es.close();
    } catch {}
  }, []);

  // Автоматически показывать боковую панель, если есть вкладки
  useEffect(() => {
    if (toolTabs.length > 0 && !tabsDrawerVisible) {
      setTabsDrawerVisible(true);
    }
  }, [toolTabs.length]);

  const loadTools = async () => {
    try {
      setLoading(true);
      const response: ToolsDiscoveryResponse = await apiService.discoverTools();
      setTools(response.data.tools);
    } catch (error) {
      console.error('Error loading tools:', error);
      message.error('Failed to load tools');
    } finally {
      setLoading(false);
    }
  };

  const loadFavorites = () => {
    const saved = localStorage.getItem('bldr_favorite_tools');
    if (saved) {
      setFavorites(new Set(JSON.parse(saved)));
    }
  };

  const saveFavorites = (newFavorites: Set<string>) => {
    localStorage.setItem('bldr_favorite_tools', JSON.stringify([...newFavorites]));
  };

  const toggleFavorite = (toolName: string) => {
    const newFavorites = new Set(favorites);
    if (newFavorites.has(toolName)) {
      newFavorites.delete(toolName);
    } else {
      newFavorites.add(toolName);
    }
    setFavorites(newFavorites);
    saveFavorites(newFavorites);
  };

  const executeTool = async (toolName: string, params: Record<string, any> = {}) => {
    try {
      setExecutingTool(toolName);
      
      // Filter out empty parameters
      const filteredParams = Object.fromEntries(
        Object.entries(params).filter(([_, value]) => value !== null && value !== undefined && value !== '')
      );

      const result: StandardResponse = await apiService.executeUnifiedTool(toolName, filteredParams);
      
      setLastResults(prev => ({
        ...prev,
        [toolName]: result
      }));

      // Persist to local history for dashboards
      try {
        const saved = localStorage.getItem('bldr_tool_execution_history');
        const arr = saved ? JSON.parse(saved) : [];
        const entry = {
          ...result,
          id: `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
        };
        const trimmed = [...arr, entry].slice(-100);
        localStorage.setItem('bldr_tool_execution_history', JSON.stringify(trimmed));
      } catch {}

      if ((window as any).addToolExecutionToHistory) {
        (window as any).addToolExecutionToHistory(result);
      }

      if (result.status === 'success') {
        message.success(`Tool ${toolName} executed successfully`);
      } else {
        message.error(`Tool ${toolName} failed: ${result.error}`);
      }

      return result;
    } catch (error) {
      console.error(`Error executing tool ${toolName}:`, error);
      message.error(`Failed to execute ${toolName}`);
      throw error;
    } finally {
      setExecutingTool(null);
    }
  };

  // openToolInNewTab теперь в глобальном контексте

  const openToolModal = async (tool: ToolInfo) => {
    setSelectedTool(tool);
    setToolParams({});
    setSelectedManifest(null); // Clear previous manifest
    try {
      console.log('Loading tool info for:', tool.name); // DEBUG
      // Use new API endpoint for tool info
      const info = await apiService.getToolInfo(tool.name);
      console.log('Tool info response:', info); // DEBUG
      console.log('Tool info response.data:', info.data); // DEBUG
      console.log('Tool info response.data.parameters:', info.data?.parameters); // DEBUG
      if (info.status === 'success' && info.data) {
        // Convert API response to manifest format
        console.log('Raw API data:', info.data); // DEBUG
        console.log('Raw API data.data:', info.data.data); // DEBUG
        
        // !!! ИСПРАВЛЕНИЕ: Извлекаем реальные данные из двойного обертывания !!!
        const toolData = info.data.data || info.data; // <-- ГЛАВНОЕ ИСПРАВЛЕНИЕ!
        console.log('Extracted toolData:', toolData); // DEBUG
        console.log('Extracted toolData.parameters:', toolData.parameters); // DEBUG
        
        const manifest = {
          name: toolData.name,
          description: toolData.description,
          category: toolData.category,
          params: Object.entries(toolData.parameters || {}).map(([key, param]: [string, any]) => {
            console.log(`Mapping parameter ${key}:`, param); // DEBUG
            return {
              name: key,
              type: param.type,
              required: param.required,
              default: param.default,
              description: param.description,
              ui: param.ui,
              enum: param.enum
            };
          })
        };
        console.log('Converted manifest:', manifest); // DEBUG
        setSelectedManifest(manifest);
      } else {
        console.error('Tool info failed:', info);
      }
    } catch (error) {
      console.error('Error loading tool info:', error);
    }
    setToolModalVisible(true);
  };

  const closeToolModal = () => {
    setToolModalVisible(false);
    setSelectedTool(null);
    setToolParams({});
  };

  const handleToolExecution = async () => {
    if (!selectedTool) return;
    try {
      // !!! ИСПРАВЛЕНИЕ: Используем новый API вместо старого !!!
      const result = await apiService.executeUnifiedTool(selectedTool.name, toolParams);
      
      // Store result for display
      setLastResults(prev => ({
        ...prev,
        [selectedTool.name]: result
      }));
      
      if (result.status === 'success') {
        message.success(`Tool ${selectedTool.name} executed successfully`);
      } else {
        message.error(`Tool ${selectedTool.name} failed: ${result.error}`);
      }
      
      // Don't close modal immediately - let user see results
    } catch (error) {
      console.error(`Error executing tool ${selectedTool.name}:`, error);
      message.error(`Failed to execute ${selectedTool.name}`);
    }
  };

  const addParameter = () => {
    const key = prompt('Parameter name:');
    if (key && key.trim()) {
      const value = prompt('Parameter value:');
      setToolParams(prev => ({
        ...prev,
        [key.trim()]: value || ''
      }));
    }
  };

  const removeParameter = (key: string) => {
    setToolParams(prev => {
      const newParams = { ...prev };
      delete newParams[key];
      return newParams;
    });
  };

  const updateParameter = (key: string, value: any) => {
    setToolParams(prev => ({
      ...prev,
      [key]: value
    }));
  };

  // Filter tools based on search and category
  const filteredTools = Object.values(tools).filter(tool => {
    const matchesSearch = tool.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         tool.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || tool.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  // Get tools by UI placement
  const dashboardTools = filteredTools.filter(tool => tool.ui_placement === 'dashboard');
  const professionalTools = filteredTools.filter(tool => tool.ui_placement === 'tools');
  const favoriteTools = filteredTools.filter(tool => favorites.has(tool.name));

  // Category config (icon, color, title)
  const TOOL_CATEGORY_CONFIG: Record<string, { icon: JSX.Element; color: string; title: string }> = {
    financial: { icon: <DollarOutlined />, color: '#2563eb', title: 'Финансовые Инструменты' },
    document_generation: { icon: <FileTextOutlined />, color: '#ea580c', title: 'Генерация Документов' },
    project_management: { icon: <ScheduleOutlined />, color: '#9333ea', title: 'Управление Проектами' },
    core_rag: { icon: <SearchOutlined />, color: '#0d9488', title: 'База Знаний (RAG)' },
    analysis: { icon: <BarChartOutlined />, color: '#7c2d12', title: 'Анализ и Отчеты' },
    visual: { icon: <EyeOutlined />, color: '#be123c', title: 'Визуальный Анализ' },
    audio: { icon: <AudioOutlined />, color: '#0891b2', title: 'Аудио Анализ' },
    utilities: { icon: <ToolOutlined />, color: '#a16207', title: 'Утилиты' },
    service: { icon: <SettingOutlined />, color: '#6b7280', title: 'Системные' },
  };

  // Get categories (excluding service by default in UI lists)
  const categories = Array.from(new Set(Object.values(tools).map(tool => tool.category))).filter(c => c && c !== 'service');

  // Category colors
  const getCategoryColor = (category: string): string => TOOL_CATEGORY_CONFIG[category]?.color || '#999999';

  // Category icons
  const getCategoryIcon = (category: string): JSX.Element => TOOL_CATEGORY_CONFIG[category]?.icon || <ToolOutlined />;

  const getToolConfigComponent = (toolName: string) => {
    const map: Record<string, React.FC<any>> = {
      generate_letter: ToolConfigGenerateLetter,
      analyze_tender: ToolConfigAnalyzeTender,
      analyze_image: ToolConfigAnalyzeImage,
      calculate_estimate: ToolConfigCalculateEstimate,
      auto_budget: ToolConfigAutoBudget,
      search_rag_database: ToolConfigSearchRAG,
      text_to_speech: ToolConfigTextToSpeech,
    };
    return map[toolName];
  };

  const getPresets = (toolName: string) => {
    try {
      const raw = localStorage.getItem(`bldr_tool_presets_${toolName}`);
      return raw ? JSON.parse(raw) : [];
    } catch { return []; }
  };

  const savePreset = (toolName: string, name: string, params: any) => {
    const list = getPresets(toolName);
    const next = [...list.filter((p: any) => p.name !== name), { name, params }];
    localStorage.setItem(`bldr_tool_presets_${toolName}`, JSON.stringify(next));
  };

  const renderToolCard = (tool: ToolInfo) => {
    const isExecuting = executingTool === tool.name;
    const isFavorite = favorites.has(tool.name);
    const lastResult = lastResults[tool.name];
    const categoryIcon = getCategoryIcon(tool.category);
    const categoryColor = getCategoryColor(tool.category);

    return (
      <Card
        key={tool.name}
        size="small"
        hoverable
        onClick={() => openToolInNewTab(tool)}
        title={
          <Space>
            <span style={{ color: categoryColor, fontSize: '16px' }}>{categoryIcon}</span>
            <span style={{ fontWeight: 600, fontSize: '14px' }}>
              {tool.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </span>
            <Tag 
              color={categoryColor}
              style={{ 
                borderRadius: '12px',
                fontSize: '11px',
                fontWeight: 500
              }}
            >
              {TOOL_CATEGORY_CONFIG[tool.category]?.title || tool.category}
            </Tag>
          </Space>
        }
        style={{
          borderRadius: '12px',
          border: '1px solid #303030',
          background: 'linear-gradient(135deg, #1f1f1f 0%, #2a2a2a 100%)',
          transition: 'all 0.3s ease',
          cursor: 'pointer',
          marginBottom: 16,
          ':hover': {
            transform: 'translateY(-2px)',
            boxShadow: '0 8px 25px rgba(0, 0, 0, 0.3)',
            borderColor: '#1890ff'
          }
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'translateY(-2px)';
          e.currentTarget.style.boxShadow = '0 8px 25px rgba(0, 0, 0, 0.3)';
          e.currentTarget.style.borderColor = '#1890ff';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.boxShadow = 'none';
          e.currentTarget.style.borderColor = '#303030';
        }}
        bodyStyle={{
          padding: '16px'
        }}
        extra={
          <Space>
            <Tooltip title={isFavorite ? 'Remove from favorites' : 'Add to favorites'}>
              <Button
                type="text"
                size="small"
                icon={isFavorite ? <StarFilled style={{ color: '#faad14' }} /> : <StarOutlined />}
                onClick={() => toggleFavorite(tool.name)}
              />
            </Tooltip>
            <Tooltip title="Tool info">
              <Button
                type="text"
                size="small"
                icon={<InfoCircleOutlined />}
                onClick={() => openToolInNewTab(tool)}
              />
            </Tooltip>
          </Space>
        }
        actions={[
          <Button
            key="open"
            type="primary"
            size="small"
            icon={<PlayCircleOutlined />}
            loading={isExecuting}
            disabled={!tool.available}
            onClick={() => openToolInNewTab(tool)}
            style={{ 
              background: 'linear-gradient(135deg, #1890ff 0%, #40a9ff 100%)',
              border: 'none',
              boxShadow: '0 2px 8px rgba(24, 144, 255, 0.3)'
            }}
          >
            Open Tool
          </Button>
        ]}
      >
        <div style={{ marginBottom: 12 }}>
          <p style={{ 
            margin: 0, 
            fontSize: '13px', 
            color: '#bfbfbf',
            lineHeight: '1.4',
            marginBottom: '12px'
          }}>
            {tool.description}
          </p>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'space-between',
            padding: '8px 12px',
            background: 'rgba(0, 0, 0, 0.3)',
            borderRadius: '8px',
            border: '1px solid #303030'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ 
                display: 'inline-block', 
                width: '8px', 
                height: '8px', 
                borderRadius: '50%', 
                backgroundColor: tool.available ? '#52c41a' : '#ff4d4f',
                boxShadow: tool.available ? '0 0 6px rgba(82, 196, 26, 0.5)' : '0 0 6px rgba(255, 77, 79, 0.5)'
              }} />
              <span style={{ 
                fontSize: '12px', 
                color: tool.available ? '#52c41a' : '#ff4d4f',
                fontWeight: 500
              }}>
                {tool.available ? 'Ready to use' : 'Unavailable'}
              </span>
            </div>
            {lastResult && (
              <span style={{ 
                fontSize: '11px', 
                color: '#8c8c8c',
                fontStyle: 'italic'
              }}>
                Last used: {new Date(lastResult.timestamp).toLocaleTimeString()}
              </span>
            )}
          </div>
        </div>
      </Card>
    );
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <p style={{ marginTop: 16 }}>Loading unified tools system...</p>
      </div>
    );
  }

  // Получаем все инструменты с фильтрацией
  const allTools = Object.values(tools).filter(tool => 
    (searchTerm === '' || tool.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
     tool.description.toLowerCase().includes(searchTerm.toLowerCase())) &&
    (selectedCategory === 'all' || tool.category === selectedCategory)
  );

  // Группируем по категориям
  const categorizedTools = groupToolsByCategory(allTools);
  
  // Получаем популярные инструменты
  const popularTools = getPopularTools(allTools);

  return (
    <ErrorBoundary>
    <div>
      {/* Header */}
      <div style={{ 
        marginBottom: 32,
        textAlign: 'center',
        background: 'linear-gradient(135deg, #1f1f1f 0%, #2a2a2a 100%)',
        padding: '24px',
        borderRadius: '16px',
        border: '1px solid #303030'
      }}>
        <h1 style={{ 
          margin: 0, 
          fontSize: '28px', 
          fontWeight: 700,
          background: 'linear-gradient(135deg, #1890ff 0%, #40a9ff 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          marginBottom: '8px'
        }}>
          🔧 Professional Tools
        </h1>
        <p style={{ 
          margin: 0, 
          fontSize: '16px', 
          color: '#bfbfbf',
          fontWeight: 400
        }}>
          Advanced construction tools with intelligent parameter support
        </p>
        <div style={{ 
          marginTop: '16px',
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          padding: '8px 16px',
          background: 'rgba(24, 144, 255, 0.1)',
          borderRadius: '20px',
          border: '1px solid rgba(24, 144, 255, 0.2)'
        }}>
          <span style={{ color: '#1890ff', fontWeight: 600 }}>
            {Object.keys(tools).length} tools available
          </span>
        </div>
      </div>

      {/* Controls */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Input
            placeholder={t('tools.searchPlaceholder')}
            prefix={<SearchOutlined />}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </Col>
        <Col span={8}>
          <Select
            style={{ width: '100%' }}
            placeholder="Filter by category"
            value={selectedCategory}
            onChange={setSelectedCategory}
          >
            <Option value="all">{t('tools.allCategories')}</Option>
            {categories.map(category => (
              <Option key={category} value={category}>
                {getCategoryIcon(category)} {category.replace('_', ' ').toUpperCase()}
              </Option>
            ))}
          </Select>
        </Col>
        <Col span={4}>
          <Button
            icon={<ReloadOutlined />}
            onClick={loadTools}
            loading={loading}
          >
            Refresh
          </Button>
          <Button style={{ marginLeft: 8 }} onClick={() => apiService.reloadRegistry().then(()=>{message.success('Reload requested'); loadTools();})}>Reload Registry</Button>
          <Button style={{ marginLeft: 8 }} type="primary" onClick={async () => {
            const name = prompt('Название нового инструмента (a-z0-9_):') || '';
            if (!name.trim()) return;
            try {
              const res = await apiService.createRegistryTemplate(name.trim(), 'custom');
              message.success('Инструмент создан');
              await loadTools();
              // open editor for new tool
              const fakeTool = Object.values(tools).find(t => t.name === name.trim()) || { name: name.trim(), description: '', category: 'other', source: 'registry', ui_placement: 'tools', available: true } as any;
              openToolInTab(fakeTool);
              setManifestEditorOpen(true);
            } catch (e) {
              message.error('Не удалось создать инструмент');
            }
          }}>Создать инструмент</Button>
        </Col>
      </Row>

      {/* Statistics */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card size="small">
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#1890ff' }}>
                {allTools.length}
              </div>
              <div>Total Tools</div>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#52c41a' }}>
                {popularTools.length}
              </div>
              <div>Popular Tools</div>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#faad14' }}>
                {favorites.size}
              </div>
              <div>Favorites</div>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#722ed1' }}>
                {categorizedTools.length}
              </div>
              <div>Categories</div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Tools Tabs */}
      <Tabs 
        activeKey={showHistory ? 'history' : activeTab} 
        onChange={(key) => {
          if (key === 'history') {
            setShowHistory(true);
          } else {
            setShowHistory(false);
            setActiveTab(key as 'dashboard' | 'tools');
          }
        }}
        tabBarExtraContent={
          <Button
            icon={<HistoryOutlined />}
            onClick={() => setShowHistory(!showHistory)}
            type={showHistory ? 'primary' : 'default'}
          >
            History
          </Button>
        }
      >
        <TabPane 
          tab={
            <span>
              <DashboardOutlined />
              Dashboard Tools ({dashboardTools.length})
            </span>
          } 
          key="dashboard"
        >
          {favoriteTools.length > 0 && (
            <>
              <h3>⭐ Favorite Tools</h3>
              <Row gutter={[16, 16]}>
                {favoriteTools.map(tool => (
                  <Col key={`fav-${tool.name}`} xs={24} sm={12} md={8} lg={6}>
                    {renderToolCard(tool)}
                  </Col>
                ))}
              </Row>
              <Divider />
            </>
          )}
          
          <h3>🎯 High-Impact Daily Tools</h3>
          {allTools.length === 0 ? (
            <Alert
              message="No tools found"
              description="Try adjusting your search or filter criteria."
              type="info"
              showIcon
            />
          ) : (
            <>
              <PopularToolsSection 
                popularTools={popularTools}
                renderToolCard={renderToolCard}
              />
              {categorizedTools.map(categoryGroup => (
                <ToolCategorySection
                  key={categoryGroup.category.id}
                  categorizedTools={categoryGroup}
                  renderToolCard={renderToolCard}
                />
              ))}
            </>
          )}
        </TabPane>

        <TabPane 
          tab={
            <span>
              <ToolOutlined />
              Professional Tools ({professionalTools.length})
            </span>
          } 
          key="tools"
        >
          <h3>🔧 Specialized Professional Tools</h3>
          {allTools.length === 0 ? (
            <Alert
              message="No tools found"
              description="Try adjusting your search or filter criteria."
              type="info"
              showIcon
            />
          ) : (
            <>
              {categorizedTools.map(categoryGroup => (
                <ToolCategorySection
                  key={categoryGroup.category.id}
                  categorizedTools={categoryGroup}
                  renderToolCard={renderToolCard}
                />
              ))}
            </>
          )}
        </TabPane>

        <TabPane 
          tab={
            <span>
              <HistoryOutlined />
              Execution History
            </span>
          } 
          key="history"
        >
          <ToolExecutionHistory />
        </TabPane>

        <TabPane 
          tab={
            <span>
              <ToolOutlined />
              Tool Tabs
              {toolTabs.length > 0 && <Badge count={toolTabs.length} style={{ marginLeft: 8 }} />}
              {tabsDrawerVisible && <span style={{ marginLeft: 8, color: '#52c41a' }}>●</span>}
            </span>
          } 
          key="tabs"
        >
          <div style={{ marginBottom: 16 }}>
            <Button 
              type="primary" 
              icon={tabsDrawerVisible ? <CloseOutlined /> : <ToolOutlined />}
              onClick={() => setTabsDrawerVisible(!tabsDrawerVisible)}
            >
              {tabsDrawerVisible ? 'Hide Tool Tabs' : 'Show Tool Tabs'}
            </Button>
            <span style={{ marginLeft: 16, color: '#666' }}>
              Управление вкладками инструментов
            </span>
          </div>
          
          {toolTabs.length > 0 && (
            <div>
              <h4>Активные вкладки ({toolTabs.length})</h4>
              <Row gutter={[16, 16]}>
                {toolTabs.map((tab, index) => (
                  <Col key={tab.id} xs={24} sm={12} md={8}>
                    <Card size="small" title={tab.tool.name}>
                      <p>{tab.tool.description}</p>
                      <Button 
                        size="small" 
                        onClick={() => setTabsDrawerVisible(true)}
                      >
                        Открыть
                      </Button>
                    </Card>
                  </Col>
                ))}
              </Row>
            </div>
          )}
        </TabPane>
      </Tabs>

      {/* Show history overlay when button is clicked */}
      {showHistory && activeTab !== 'history' && (
        <div style={{ marginTop: 24 }}>
          <ToolExecutionHistory />
        </div>
      )}

      {/* Tool Execution Modal */}
      <Modal
        key={selectedTool?.name || 'no-tool'} // !!! ПРИНУДИТЕЛЬНЫЙ РЕСЕТ КОМПОНЕНТА !!!
        title={selectedTool ? `Execute: ${selectedTool.name}` : 'Execute Tool'}
        open={toolModalVisible}
        onCancel={closeToolModal}
        footer={[
          <Button key="cancel" onClick={closeToolModal}>
            Cancel
          </Button>,
          <Button key="editm" onClick={() => setManifestEditorOpen(true)}>Редактировать манифест</Button>,
          <Button
            key="execute"
            type="primary"
            loading={executingTool === selectedTool?.name}
            onClick={handleToolExecution}
          >
            Execute Tool
          </Button>
        ]}
        width={600}
      >
        {selectedTool && (
          <div>
            <div style={{ marginBottom: 16 }}>
              <p><strong>Description:</strong> {selectedTool.description}</p>
              <p><strong>Category:</strong> {selectedTool.category}</p>
              <p><strong>Source:</strong> {selectedTool.source}</p>
            </div>

            <Divider />

            {/* Dynamic form from manifest.params */}
            {selectedManifest && (
              <>
                {/* DEBUG: Log selectedManifest */}
                {console.log('[UnifiedToolsPanel] selectedManifest:', selectedManifest)}
                {console.log('[UnifiedToolsPanel] selectedManifest.params:', selectedManifest.params)}
                {console.log('[UnifiedToolsPanel] selectedManifest.params count:', selectedManifest.params?.length || 0)}
                <DynamicToolForm params={selectedManifest.params || []} value={toolParams} onChange={setToolParams} />
              </>
            )}

            {/* Presets */}
            <Divider />
            <h4>Presets</h4>
            <Space style={{ marginBottom: 12 }}>
              <Select placeholder="Выберите пресет" style={{ width: 220 }} allowClear
                value={selectedPreset || undefined}
                onChange={(v) => {
                  setSelectedPreset(v as string);
                  const list = getPresets(selectedTool.name);
                  const found = list.find((p: any) => p.name === v);
                  if (found) setToolParams(found.params || {});
                }}
              >
                {getPresets(selectedTool.name).map((p: any) => (
                  <Option key={p.name} value={p.name}>{p.name}</Option>
                ))}
              </Select>
              <Button size="small" onClick={() => {
                const name = prompt('Название пресета:');
                if (name && name.trim()) {
                  savePreset(selectedTool.name, name.trim(), toolParams);
                  setSelectedPreset(name.trim());
                }
              }}>Сохранить как пресет</Button>
            </Space>

            {lastResults[selectedTool.name] && (
              <>
                <Divider />
                <h4>Last Result</h4>
                <ToolResultDisplay 
                  result={lastResults[selectedTool.name]} 
                  toolName={selectedTool.name}
                />
              </>
            )}
          </div>
        )}
      </Modal>

      {/* Боковая панель теперь глобальная в App.tsx */}

      {/* Manifest Editor */}
      {selectedTool && selectedManifest && (
        <ToolManifestEditor
          open={manifestEditorOpen}
          manifest={{
            name: selectedTool.name,
            title: selectedManifest.title || selectedTool.name,
            description: selectedManifest.description || selectedTool.description,
            category: selectedManifest.category || selectedTool.category,
            ui_placement: selectedManifest.ui_placement || 'tools',
            enabled: selectedManifest.enabled !== false,
            system: selectedManifest.system || false,
            params: selectedManifest.params || []
          }}
          onCancel={() => setManifestEditorOpen(false)}
          onSave={async (patch) => {
            try {
              await apiService.updateRegistryManifest(selectedTool.name, patch);
              message.success('Манифест обновлён');
              setManifestEditorOpen(false);
              // refresh details
              const info = await apiService.getRegistryToolInfo(selectedTool.name);
              setSelectedManifest(info?.manifest || null);
              loadTools();
            } catch (e) {
              message.error('Ошибка обновления манифеста');
            }
          }}
        />
      )}
    </div>
    </ErrorBoundary>
  );
};

export default UnifiedToolsPanel;