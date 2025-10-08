/**
 * Tool Tabs Manager Component
 * Управляет вкладками для инструментов вместо модальных окон
 */

import React, { useState, useEffect } from 'react';
import { Tabs, Button, Space, Tooltip, Badge, Modal, message } from 'antd';
import { 
  CloseOutlined, 
  ReloadOutlined, 
  FullscreenOutlined,
  LinkOutlined,
  SettingOutlined,
  PlayCircleOutlined,
  LeftOutlined,
  RightOutlined
} from '@ant-design/icons';
import DynamicToolForm from './DynamicToolForm';
import ToolResultDisplay from './ToolResultDisplay';
import { apiService } from '../services/api';
import { getToolIcon, getToolIconColor } from '../utils/toolIcons';
import { useTranslation } from '../contexts/LocalizationContext';

const { TabPane } = Tabs;

interface ToolTab {
  id: string;
  toolName: string;
  toolInfo: any;
  params: Record<string, any>;
  result?: any;
  loading?: boolean;
  error?: string;
  timestamp: number;
}

interface ToolTabsManagerProps {
  onClose?: () => void;
  onOpenInNewTab?: (toolName: string, params: Record<string, any>) => void;
  initialTabs?: any[];
}

const ToolTabsManager: React.FC<ToolTabsManagerProps> = ({ 
  onClose, 
  onOpenInNewTab,
  initialTabs = []
}) => {
  const [tabs, setTabs] = useState<ToolTab[]>([]);
  const t = useTranslation();
  const [activeTab, setActiveTab] = useState<string>('');
  const [newTabCounter, setNewTabCounter] = useState(0);

  // Инициализация вкладок из props
  useEffect(() => {
    if (initialTabs && Array.isArray(initialTabs) && initialTabs.length > 0) {
      const convertedTabs: ToolTab[] = initialTabs.map((tab, index) => ({
        id: `tool-${Date.now()}-${index}`,
        toolName: tab.tool?.name || tab.toolInfo?.name || 'Unknown Tool',
        toolInfo: tab.toolInfo || tab.tool,
        params: tab.params || {},
        timestamp: Date.now()
      }));
      setTabs(convertedTabs);
      if (convertedTabs.length > 0) {
        setActiveTab(convertedTabs[0].id);
      }
    }
  }, [initialTabs]);

  // Добавить новую вкладку
  const addTab = async (toolInfo: any, params: Record<string, any> = {}) => {
    const tabId = `tool-${Date.now()}-${newTabCounter}`;
    
    // Загружаем полную информацию об инструменте
    let fullToolInfo = toolInfo;
    try {
      console.log('Loading full tool info for:', toolInfo.name);
      const info = await apiService.getToolInfo(toolInfo.name);
      if (info.status === 'success' && info.data) {
        const toolData = info.data.data || info.data;
        fullToolInfo = {
          ...toolInfo,
          parameters: Object.entries(toolData.parameters || {}).map(([key, param]: [string, any]) => ({
            name: key,
            type: param.type,
            required: param.required,
            default: param.default,
            description: param.description,
            ui: param.ui,
            enum: param.enum
          }))
        };
        console.log('Loaded full tool info:', fullToolInfo);
      }
    } catch (error) {
      console.error('Failed to load tool info:', error);
    }
    
    const newTab: ToolTab = {
      id: tabId,
      toolName: toolInfo.name,
      toolInfo: fullToolInfo,
      params,
      timestamp: Date.now()
    };
    
    setTabs(prev => [...prev, newTab]);
    setActiveTab(tabId);
    setNewTabCounter(prev => prev + 1);
  };

  // Закрыть вкладку
  const closeTab = (tabId: string) => {
    setTabs(prev => {
      const newTabs = prev.filter(tab => tab.id !== tabId);
      if (activeTab === tabId && newTabs.length > 0) {
        setActiveTab(newTabs[newTabs.length - 1].id);
      } else if (newTabs.length === 0) {
        setActiveTab('');
      }
      return newTabs;
    });
  };

  // Закрыть все вкладки
  const closeAllTabs = () => {
    setTabs([]);
    setActiveTab('');
  };

  // Обновить результат вкладки
  const updateTabResult = (tabId: string, result: any, loading: boolean = false, error?: string) => {
    setTabs(prev => prev.map(tab => 
      tab.id === tabId 
        ? { ...tab, result, loading, error }
        : tab
    ));
  };

  // Выполнить инструмент
  const executeTool = async (tab: ToolTab) => {
    updateTabResult(tab.id, null, true);
    
    try {
      // !!! УНИВЕРСАЛЬНОСТЬ: Используем apiService.executeUnifiedTool для всех инструментов !!!
      const { apiService } = await import('../services/api');
      const result = await apiService.executeUnifiedTool(tab.toolName, tab.params);
      
      updateTabResult(tab.id, result, false);
      
      if (result.status === 'error') {
        updateTabResult(tab.id, null, false, result.error);
        message.error(`Ошибка выполнения ${tab.toolName}: ${result.error}`);
      } else {
        message.success(`${tab.toolName} выполнен успешно`);
      }
    } catch (error: any) {
      updateTabResult(tab.id, null, false, error.message);
      message.error(`Ошибка выполнения ${tab.toolName}: ${error.message}`);
    }
  };

  // Открыть в новой вкладке браузера
  const openInBrowserTab = (tab: ToolTab) => {
    if (onOpenInNewTab) {
      onOpenInNewTab(tab.toolName, tab.params);
    } else {
      // Fallback: открыть в новом окне браузера
      const url = `/tools/${tab.toolName}?${new URLSearchParams(tab.params).toString()}`;
      window.open(url, '_blank');
    }
  };

  // Получить активную вкладку
  const activeTabData = tabs.find(tab => tab.id === activeTab);

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Заголовок с кнопками управления */}
      <div style={{ 
        padding: '12px 16px', 
        borderBottom: '1px solid #f0f0f0',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: '#fafafa'
      }}>
        <div>
          <strong>Инструменты</strong>
          <Badge count={tabs.length} style={{ marginLeft: 8 }} />
        </div>
        <Space>
          <Tooltip title="Обновить все вкладки">
            <Button 
              size="small" 
              icon={<ReloadOutlined />}
              onClick={() => {
                tabs.forEach(tab => {
                  if (!tab.loading) {
                    executeTool(tab);
                  }
                });
              }}
            />
          </Tooltip>
          <Tooltip title="Открыть в новой вкладке браузера">
            <Button 
              size="small" 
              icon={<LinkOutlined />}
              disabled={!activeTabData}
              onClick={() => activeTabData && openInBrowserTab(activeTabData)}
            />
          </Tooltip>
          <Tooltip title="Закрыть все вкладки">
            <Button 
              size="small" 
              icon={<CloseOutlined />}
              onClick={closeAllTabs}
              disabled={tabs.length === 0}
            />
          </Tooltip>
        </Space>
      </div>

      {/* Вкладки */}
      {tabs.length > 0 ? (
        <Tabs
          type="editable-card"
          activeKey={activeTab}
          onChange={setActiveTab}
          onEdit={(targetKey, action) => {
            if (action === 'remove') {
              closeTab(targetKey as string);
            }
          }}
          style={{ 
            flex: 1, 
            overflow: 'hidden',
            background: 'linear-gradient(135deg, #001529 0%, #002140 100%)',
            color: 'white'
          }}
          tabBarStyle={{ 
            margin: 0, 
            padding: '0 16px',
            background: 'rgba(24, 144, 255, 0.05)',
            borderBottom: '1px solid rgba(24, 144, 255, 0.2)',
            borderRadius: '0'
          }}
          tabBarGutter={8}
        >
          {tabs.map(tab => {
            const IconComponent = getToolIcon(tab.toolInfo || tab);
            const iconColor = getToolIconColor(tab.toolInfo || tab);
            
            return (
              <TabPane
                key={tab.id}
                tab={
                  <span style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '8px',
                    color: 'white',
                    fontWeight: '500'
                  }}>
                    <IconComponent style={{ color: iconColor, fontSize: '14px' }} />
                    <span>{tab.toolName.replace(/_/g, ' ')}</span>
                    {tab.loading && <Badge status="processing" />}
                    {tab.error && <Badge status="error" />}
                  </span>
                }
                closable
                closeIcon={<LeftOutlined style={{ color: '#1890ff' }} />}
              >
              <div style={{ 
                height: 'calc(100vh - 200px)', 
                overflow: 'auto',
                padding: '20px',
                background: 'linear-gradient(135deg, #001529 0%, #002140 100%)',
                color: 'white',
                borderRadius: '0 0 8px 8px'
              }}>
                {/* Форма параметров */}
                <div style={{ marginBottom: 16 }}>
                  {/* Отладочная информация */}
                  <div style={{ color: '#666', fontSize: '12px', marginBottom: '8px' }}>
                    Debug: toolInfo={JSON.stringify(tab.toolInfo?.name)}, 
                    parameters={JSON.stringify(tab.toolInfo?.parameters?.length || 0)}
                  </div>
                  <DynamicToolForm
                    params={tab.toolInfo?.parameters || []}
                    value={tab.params || {}}
                    onChange={(values) => {
                      setTabs(prev => prev.map(t => 
                        t.id === tab.id ? { ...t, params: values } : t
                      ));
                    }}
                  />
                </div>

                {/* Кнопка выполнения */}
                <div style={{ marginBottom: 16 }}>
                  <Button
                    type="primary"
                    icon={<PlayCircleOutlined />}
                    loading={tab.loading}
                    onClick={() => executeTool(tab)}
                    disabled={!tab.toolInfo}
                    size="large"
                    block
                    style={{
                      background: 'linear-gradient(135deg, #1890ff 0%, #40a9ff 100%)',
                      border: 'none',
                      borderRadius: '8px',
                      height: '48px',
                      fontSize: '16px',
                      fontWeight: '600',
                      boxShadow: '0 4px 12px rgba(24, 144, 255, 0.3)',
                      transition: 'all 0.3s ease'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.transform = 'translateY(-2px)';
                      e.currentTarget.style.boxShadow = '0 6px 16px rgba(24, 144, 255, 0.4)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.transform = 'translateY(0)';
                      e.currentTarget.style.boxShadow = '0 4px 12px rgba(24, 144, 255, 0.3)';
                    }}
                  >
                    🚀 {t('toolTabs.executeTool')}
                  </Button>
                </div>

                {/* Результаты */}
                {tab.result && (
                  <div style={{ marginTop: 16 }}>
                    <ToolResultDisplay 
                      result={tab.result}
                      toolName={tab.toolName}
                    />
                  </div>
                )}

                {/* Ошибка */}
                {tab.error && (
                  <div style={{ 
                    marginTop: 16, 
                    padding: 12, 
                    background: '#fff2f0', 
                    border: '1px solid #ffccc7',
                    borderRadius: 6
                  }}>
                    <strong>Ошибка:</strong> {tab.error}
                  </div>
                )}
              </div>
            </TabPane>
            );
          })}
        </Tabs>
      ) : (
        <div style={{ 
          flex: 1, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          color: '#999',
          fontSize: 16
        }}>
          Выберите инструмент для работы
        </div>
      )}
    </div>
  );
};

export default ToolTabsManager;

