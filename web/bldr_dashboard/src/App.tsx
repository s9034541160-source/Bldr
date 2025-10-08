import React, { useState, useEffect, Suspense, lazy } from 'react';
import { Layout, Menu, ConfigProvider, theme, message, Button } from 'antd';
import { BrowserRouter as Router, Routes, Route, useParams, useNavigate } from 'react-router-dom';
import { 
  DashboardOutlined, 
  CodeOutlined, 
  DatabaseOutlined, 
  MessageOutlined, 
  FolderOutlined, 
  BarChartOutlined, 
  SettingOutlined,
  ClockCircleOutlined,
  ToolOutlined,
  LinkOutlined,
  CloseOutlined,
  LeftOutlined,
  RightOutlined
} from '@ant-design/icons';
import ControlPanel from './components/ControlPanel';
import AuthHeader from './components/AuthHeader';
import Queue from './components/Queue';
import Settings from './components/Settings';
import ErrorBoundary from './components/ErrorBoundary';
import ToolTabsManager from './components/ToolTabsManager';
import { ToolTabsProvider, useToolTabs } from './contexts/ToolTabsContext';
import { LocalizationProvider } from './contexts/LocalizationContext';
import { getToolIcon, getToolIconColor } from './utils/toolIcons';

const AIShell = lazy(() => import('./components/AIShell'));
const DBTools = lazy(() => import('./components/DBTools'));
const BotControl = lazy(() => import('./components/BotControl'));
const FileManager = lazy(() => import('./components/FileManager'));
const Analytics = lazy(() => import('./components/Analytics'));
const RAGModule = lazy(() => import('./components/RAGModule'));
const ProFeatures = lazy(() => import('./components/ProTools'));
const Projects = lazy(() => import('./components/Projects'));
const UnifiedToolsPanel = lazy(() => import('./components/UnifiedToolsPanel'));
const TemplateManagementSystem = lazy(() => import('./components/TemplateManagementSystem'));
const DiagnosticPanel = lazy(() => import('./components/DiagnosticPanel'));
const ToolPage = lazy(() => import('./components/ToolPage'));
const NTDNavigator = lazy(() => import('./components/NTDNavigator'));

// Removed SimpleTest import since we're hiding the Test tab
import { useStore } from './store';
import { apiService } from './services/api';

const { Content, Footer, Sider } = Layout;

// Компонент-обертка для ToolPage с параметрами из URL
const ToolPageWrapper: React.FC = () => {
  const { toolName } = useParams<{ toolName: string }>();
  const navigate = useNavigate();
  
  if (!toolName) {
    return <div>Инструмент не найден</div>;
  }

  return (
    <ToolPage 
      toolName={toolName}
      onBack={() => navigate('/')}
    />
  );
};

const AppContent: React.FC = () => {
  const [activeTab, setActiveTab] = React.useState('dashboard'); // Set dashboard as default
  const [isClient, setIsClient] = useState(false);
  const { theme: appTheme, setUser } = useStore();
  const { toolTabs, tabsDrawerVisible, setTabsDrawerVisible } = useToolTabs();
  
  // Set client-side flag and initialize token from localStorage
  useEffect(() => {
    setIsClient(true);
    
    // Initialize user from localStorage if available (preserve role and username)
    try {
      const savedToken = localStorage.getItem('auth-token');
      const savedUserStr = localStorage.getItem('auth-user');
      if (savedToken) {
        let username = 'user';
        let role = 'user';
        // Prefer saved user object
        if (savedUserStr) {
          try {
            const su = JSON.parse(savedUserStr);
            if (su && typeof su === 'object') {
              if (su.username) username = su.username;
              if (su.role) role = su.role;
            }
          } catch {}
        } else if (savedToken.includes('.')) {
          // Fallback: parse JWT payload for sub/role
          try {
            const payload = JSON.parse(atob(savedToken.split('.')[1]));
            if (payload?.sub) username = payload.sub;
            if (payload?.role) role = payload.role;
          } catch {}
        } else if (savedToken === 'disabled_auth_token') {
          username = 'anonymous';
          role = 'user';
        }
        setUser({ token: savedToken, role, username });
      }
    } catch {}
  }, [setUser]);

  // Health check on app mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await apiService.getHealth();
        // Check if any component is not connected/running
        const dbStatus = res.components?.db;
        const celeryStatus = res.components?.celery;
        
        // Show warning if any component is down (not 'connected' or 'running')
        if ((dbStatus && dbStatus !== 'connected' && dbStatus !== 'skipped') || 
            (celeryStatus && celeryStatus !== 'running')) {
          message.warning(`Сервер частично down: DB=${dbStatus || 'undefined'}, Celery=${celeryStatus || 'undefined'}`);
        }
      } catch (e: any) {
        message.error('Backend недоступен — запустите uvicorn');
      }
    };

    checkHealth();
  }, []);

  // Автоматически показывать боковую панель, если есть вкладки
  useEffect(() => {
    if (toolTabs.length > 0 && !tabsDrawerVisible) {
      setTabsDrawerVisible(true);
    }
  }, [toolTabs.length]);

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <ControlPanel />;
      // Removed 'test' case since we're hiding the Test tab
      case 'unified-tools':
        return <UnifiedToolsPanel />;
      case 'templates':
        return <TemplateManagementSystem />;
      case 'diagnostic':
        return <DiagnosticPanel />;
      case 'projects':
        return <Projects />;
      case 'ai':
        return <AIShell />;
      case 'db':
        return <DBTools />;
      case 'bot':
        return <BotControl />;
      case 'files':
        return <FileManager />;
      case 'queue':
        return <Queue />;
      case 'analytics':
        return <Analytics />;
      case 'rag':
        return <RAGModule />;
      case 'ntd':
        return <NTDNavigator />;
      case 'settings':
        return <Settings />;
      case 'pro':
        return <ProFeatures />;

      default:
        return <ControlPanel />; // Default to ControlPanel
    }
  };

  // Render nothing on server-side
  if (!isClient) {
    return null;
  }

  const themeConfig = {
    algorithm: appTheme === 'dark' ? theme.darkAlgorithm : theme.defaultAlgorithm,
    token: {
      colorBgContainer: appTheme === 'dark' ? '#141414' : '#ffffff',
      colorText: appTheme === 'dark' ? '#ffffff' : '#000000',
    }
  };

  // Обработчик клика вне Tool Tab для сворачивания
  const handleClickOutside = (event: React.MouseEvent) => {
    if (tabsDrawerVisible && !(event.target as Element).closest('.tool-tabs-sidebar')) {
      setTabsDrawerVisible(false);
    }
  };

  // Защита от ошибок при сворачивании
  const safeToolTabs = toolTabs || [];

  return (
    <Router>
      <ConfigProvider theme={themeConfig}>
        <div onClick={handleClickOutside}>
        <Routes>
          {/* Маршрут для отдельных страниц инструментов */}
          <Route path="/tools/:toolName" element={<ToolPageWrapper />} />
          
          {/* Основное приложение */}
          <Route path="/*" element={
            <Layout style={{ minHeight: '100vh' }}>
        <Sider
          breakpoint="lg"
          collapsedWidth="0"
          onBreakpoint={(broken) => {
            console.log(broken);
          }}
          onCollapse={(collapsed, type) => {
            console.log(collapsed, type);
          }}
        >
          <div className="logo" style={{ 
            margin: '16px',
            textAlign: 'center'
          }}>
            <div style={{ color: '#fff', fontWeight: 'bold', fontSize: '18px' }}>BLDR</div>
          </div>
          <Menu
            theme="dark"
            mode="inline"
            selectedKeys={[activeTab]}
            items={[
              {
                key: 'dashboard',
                icon: <DashboardOutlined />,
                label: 'Dashboard',
              },
              {
                key: 'unified-tools',
                icon: <SettingOutlined />,
                label: '🔧 Unified Tools',
              },
              {
                key: 'templates',
                icon: <FolderOutlined />,
                label: '📄 Templates',
              },
              {
                key: 'projects',
                icon: <FolderOutlined />,
                label: 'Проекты',
              },
              {
                key: 'ai',
                icon: <CodeOutlined />,
                label: 'Чат (ИИ)',
              },
              {
                key: 'db',
                icon: <DatabaseOutlined />,
                label: 'DB Tools',
              },
              {
                key: 'bot',
                icon: <MessageOutlined />,
                label: 'Bot Control',
              },
              {
                key: 'files',
                icon: <FolderOutlined />,
                label: 'File Manager',
              },
              {
                key: 'queue',
                icon: <ClockCircleOutlined />,
                label: 'Очередь',
              },
              {
                key: 'rag',
                icon: <DashboardOutlined />,
                label: 'RAG Module',
              },
              {
                key: 'ntd',
                icon: <DatabaseOutlined />,
                label: 'НТД Навигатор',
              },
              {
                key: 'pro',
                icon: <ToolOutlined />,
                label: 'Pro Tools',
              },
              {
                key: 'analytics',
                icon: <BarChartOutlined />,
                label: 'Analytics',
              },
              {
                key: 'settings',
                icon: <SettingOutlined />,
                label: 'Настройки',
              },
              {
                key: 'diagnostic',
                icon: <SettingOutlined />,
                label: '🔧 Diagnostic',
              },

            ]}
            onClick={({ key }) => setActiveTab(key)}
          />
        </Sider>
        
        <Layout>
          <AuthHeader />
          
          <Content style={{ padding: '24px' }}>
            <div
              style={{
                minHeight: 280,
                padding: 24,
              }}
            >
              <ErrorBoundary>
                <Suspense fallback={<div>Загрузка...</div>}>
                  {renderContent()}
                </Suspense>
              </ErrorBoundary>
            </div>
          </Content>
          
          <Footer style={{ textAlign: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px' }}>
              <span>🏗️ Bldr v2 ©2025 Created by BldrTeam with powerful help from Алёша</span>
            </div>
          </Footer>
        </Layout>
      </Layout>
          } />
        </Routes>
      
      {/* Глобальная боковая панель инструментов */}
      <div 
        className="tool-tabs-sidebar"
        style={{ 
          position: 'fixed', 
          right: 0, 
          top: 0, 
          height: '100vh', 
          width: tabsDrawerVisible ? '66vw' : '60px',
          background: 'linear-gradient(135deg, #001529 0%, #002140 100%)',
          borderLeft: '1px solid #1890ff',
          boxShadow: tabsDrawerVisible ? '-4px 0 20px rgba(0, 0, 0, 0.3)' : 'none',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          zIndex: 1000,
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        {/* Header с кнопкой сворачивания */}
        <div style={{ 
          padding: '16px', 
          borderBottom: '1px solid rgba(24, 144, 255, 0.2)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: tabsDrawerVisible ? 'space-between' : 'center',
          background: 'rgba(24, 144, 255, 0.05)'
        }}>
          {tabsDrawerVisible && (
            <span style={{ 
              color: 'white', 
              fontWeight: 'bold',
              fontSize: '16px',
              textShadow: '0 1px 2px rgba(0, 0, 0, 0.3)'
            }}>
              🔧 Tool Tabs ({safeToolTabs.length})
            </span>
          )}
          <Button
            type="text"
            icon={tabsDrawerVisible ? <RightOutlined /> : <LeftOutlined />}
            onClick={() => setTabsDrawerVisible(!tabsDrawerVisible)}
            style={{ 
              color: '#1890ff',
              fontSize: '16px',
              width: '32px',
              height: '32px',
              borderRadius: '6px',
              background: 'rgba(24, 144, 255, 0.1)',
              border: '1px solid rgba(24, 144, 255, 0.3)',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'rgba(24, 144, 255, 0.2)';
              e.currentTarget.style.transform = 'scale(1.05)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'rgba(24, 144, 255, 0.1)';
              e.currentTarget.style.transform = 'scale(1)';
            }}
          />
        </div>

        {/* Содержимое */}
        {tabsDrawerVisible ? (
          <div style={{ flex: 1, overflow: 'hidden' }}>
            <ToolTabsManager
              initialTabs={safeToolTabs}
              onClose={() => setTabsDrawerVisible(false)}
              onOpenInNewTab={(toolName, params) => {
                // Открыть в новой вкладке браузера
                const url = `/tools/${toolName}?${new URLSearchParams(params).toString()}`;
                window.open(url, '_blank');
              }}
            />
          </div>
        ) : (
          /* Свернутая панель с иконками инструментов */
          <div style={{ 
            flex: 1, 
            overflow: 'auto',
            padding: '16px 8px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px'
          }}>
            {safeToolTabs.map(tab => {
              const IconComponent = getToolIcon(tab.toolInfo || tab.tool);
              const iconColor = getToolIconColor(tab.toolInfo || tab.tool);
              
              return (
                <div
                  key={tab.id}
                  onClick={() => setTabsDrawerVisible(true)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '12px',
                    borderRadius: '12px',
                    background: 'rgba(24, 144, 255, 0.1)',
                    border: '1px solid rgba(24, 144, 255, 0.2)',
                    cursor: 'pointer',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    position: 'relative',
                    overflow: 'hidden'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = 'rgba(24, 144, 255, 0.2)';
                    e.currentTarget.style.borderColor = iconColor;
                    e.currentTarget.style.transform = 'translateY(-2px)';
                    e.currentTarget.style.boxShadow = `0 4px 12px rgba(24, 144, 255, 0.3)`;
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = 'rgba(24, 144, 255, 0.1)';
                    e.currentTarget.style.borderColor = 'rgba(24, 144, 255, 0.2)';
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = 'none';
                  }}
                >
                  <IconComponent
                    style={{
                      fontSize: '20px',
                      color: iconColor,
                      filter: 'drop-shadow(0 1px 2px rgba(0, 0, 0, 0.3))'
                    }}
                  />
                </div>
              );
            })}
          </div>
        )}
      </div>
        </div>
      </ConfigProvider>
    </Router>
  );
};

const App: React.FC = () => {
  return (
    <LocalizationProvider>
      <ToolTabsProvider>
        <AppContent />
      </ToolTabsProvider>
    </LocalizationProvider>
  );
};

export default App;