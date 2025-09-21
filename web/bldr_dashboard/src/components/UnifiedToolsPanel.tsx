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
  Divider
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
  HistoryOutlined
} from '@ant-design/icons';
import { apiService } from '../services/api';
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
import ToolExecutionHistory from './ToolExecutionHistory';
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
  const [activeTab, setActiveTab] = useState<'dashboard' | 'tools' | 'history'>('dashboard');
  const [favorites, setFavorites] = useState<Set<string>>(new Set());
  const [executingTool, setExecutingTool] = useState<string | null>(null);
  const [toolModalVisible, setToolModalVisible] = useState(false);
  const [selectedTool, setSelectedTool] = useState<ToolInfo | null>(null);
  const [toolParams, setToolParams] = useState<Record<string, any>>({});
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
  const [lastResults, setLastResults] = useState<Record<string, StandardResponse>>({});
  const [showHistory, setShowHistory] = useState(false);

  // Load tools on component mount
  useEffect(() => {
    loadTools();
    loadFavorites();
  }, []);

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

  const openToolModal = (tool: ToolInfo) => {
    setSelectedTool(tool);
    setToolParams({});
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
      await executeTool(selectedTool.name, toolParams);
      closeToolModal();
    } catch (error) {
      // Error already handled in executeTool
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

  // Get categories
  const categories = Array.from(new Set(Object.values(tools).map(tool => tool.category)));

  // Category colors
  const getCategoryColor = (category: string): string => {
    const colors: Record<string, string> = {
      financial: 'blue',
      advanced_analysis: 'red',
      document_generation: 'orange',
      project_management: 'purple',
      core_rag: 'green',
      data_processing: 'gray',
      audio: 'cyan',
      other: 'default',
    };
    return colors[category] || colors.other;
  };

  // Category icons
  const getCategoryIcon = (category: string): string => {
    const icons: Record<string, string> = {
      financial: '💰',
      advanced_analysis: '🧠',
      document_generation: '📄',
      project_management: '📅',
      core_rag: '🔍',
      data_processing: '⚙️',
      audio: '🔊',
      other: '🔧',
    };
    return icons[category] || icons.other;
  };

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
        onClick={() => openToolModal(tool)}
        title={
          <Space>
            <span>{categoryIcon}</span>
            <span>{tool.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
            <Tag color={categoryColor}>{tool.category}</Tag>
          </Space>
        }
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
                onClick={() => openToolModal(tool)}
              />
            </Tooltip>
          </Space>
        }
        actions={[
          <Button
            key="quick"
            type="primary"
            size="small"
            icon={<PlayCircleOutlined />}
            loading={isExecuting}
            disabled={!tool.available}
            onClick={() => executeTool(tool.name)}
          >
            Quick Run
          </Button>,
          <Button
            key="params"
            size="small"
            icon={<SettingOutlined />}
            disabled={!tool.available}
            onClick={() => openToolModal(tool)}
          >
            With Params
          </Button>
        ]}
        style={{ marginBottom: 16 }}
      >
        <div style={{ marginBottom: 8 }}>
          <p style={{ margin: 0, fontSize: '12px', color: '#666' }}>
            {tool.description}
          </p>
        </div>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Space size="small">
            <Badge 
              status={tool.available ? 'success' : 'error'} 
              text={tool.available ? 'Available' : 'Unavailable'} 
            />
            <Tag>{tool.source}</Tag>
          </Space>
          
          {lastResult && (
            <Tag 
              color={lastResult.status === 'success' ? 'green' : 'red'}
            >
              {lastResult.status === 'success' ? '✅' : '❌'} 
              {lastResult.execution_time ? `${lastResult.execution_time.toFixed(2)}s` : ''}
            </Tag>
          )}
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

  return (
    <ErrorBoundary>
    <div>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h1>🔧 Unified Tools System</h1>
        <p>
          Professional construction tools with **kwargs support - {Object.keys(tools).length} tools available
        </p>
      </div>

      {/* Controls */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Input
            placeholder="Search tools..."
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
            <Option value="all">All Categories</Option>
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
        </Col>
      </Row>

      {/* Statistics */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card size="small">
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#1890ff' }}>
                {dashboardTools.length}
              </div>
              <div>Dashboard Tools</div>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#52c41a' }}>
                {professionalTools.length}
              </div>
              <div>Professional Tools</div>
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
                {categories.length}
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
          {dashboardTools.length === 0 ? (
            <Alert
              message="No dashboard tools found"
              description="Try adjusting your search or filter criteria."
              type="info"
              showIcon
            />
          ) : (
            <Row gutter={[16, 16]}>
              {dashboardTools.map(tool => (
                <Col key={tool.name} xs={24} sm={12} md={8} lg={6}>
                  {renderToolCard(tool)}
                </Col>
              ))}
            </Row>
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
          {professionalTools.length === 0 ? (
            <Alert
              message="No professional tools found"
              description="Try adjusting your search or filter criteria."
              type="info"
              showIcon
            />
          ) : (
            <Row gutter={[16, 16]}>
              {professionalTools.map(tool => (
                <Col key={tool.name} xs={24} sm={12} md={8} lg={6}>
                  {renderToolCard(tool)}
                </Col>
              ))}
            </Row>
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
      </Tabs>

      {/* Show history overlay when button is clicked */}
      {showHistory && activeTab !== 'history' && (
        <div style={{ marginTop: 24 }}>
          <ToolExecutionHistory />
        </div>
      )}

      {/* Tool Execution Modal */}
      <Modal
        title={selectedTool ? `Execute: ${selectedTool.name}` : 'Execute Tool'}
        open={toolModalVisible}
        onCancel={closeToolModal}
        footer={[
          <Button key="cancel" onClick={closeToolModal}>
            Cancel
          </Button>,
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

            {/* Per-tool configuration */}
            {(() => {
              const Cmp = getToolConfigComponent(selectedTool.name);
              if (Cmp) {
                return <Cmp value={toolParams} onChange={setToolParams} />;
              }
              return (
                <>
                  <h4>Parameters (**kwargs)</h4>
                  <div style={{ marginBottom: 16 }}>
                    <Button onClick={addParameter} size="small">+ Add Parameter</Button>
                  </div>
                  {Object.keys(toolParams).length === 0 ? (
                    <p style={{ color: '#666', fontStyle: 'italic' }}>
                      No parameters set. Click "Add Parameter" to add **kwargs.
                    </p>
                  ) : (
                    <div>
                      {Object.entries(toolParams).map(([key, value]) => (
                        <div key={key} style={{ marginBottom: 8, display: 'flex', gap: 8 }}>
                          <Input style={{ width: '30%' }} value={key} readOnly size="small" />
                          <Input style={{ flex: 1 }} value={value as any}
                            onChange={(e) => updateParameter(key, (e.target as any).value)} placeholder="Value" size="small" />
                          <Button size="small" danger onClick={() => removeParameter(key)}>❌</Button>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              );
            })()}

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
                <Alert
                  message={lastResults[selectedTool.name].status === 'success' ? 'Success' : 'Error'}
                  description={
                    lastResults[selectedTool.name].error || 
                    `Executed successfully in ${lastResults[selectedTool.name].execution_time?.toFixed(3)}s`
                  }
                  type={lastResults[selectedTool.name].status === 'success' ? 'success' : 'error'}
                  showIcon
                />
              </>
            )}
          </div>
        )}
      </Modal>
    </div>
    </ErrorBoundary>
  );
};

export default UnifiedToolsPanel;