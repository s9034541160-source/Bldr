import React, { useState, useEffect, Suspense, lazy } from 'react';
import { Layout, Menu, ConfigProvider, theme, message } from 'antd';
import { 
  DashboardOutlined, 
  CodeOutlined, 
  DatabaseOutlined, 
  MessageOutlined, 
  FolderOutlined, 
  BarChartOutlined, 
  SettingOutlined,
  ClockCircleOutlined,
  ToolOutlined
} from '@ant-design/icons';
import ControlPanel from './components/ControlPanel';
import AuthHeader from './components/AuthHeader';
import Queue from './components/Queue';
import Settings from './components/Settings';
import ErrorBoundary from './components/ErrorBoundary';

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

// Removed SimpleTest import since we're hiding the Test tab
import { useStore } from './store';
import { apiService } from './services/api';

const { Content, Footer, Sider } = Layout;

const App: React.FC = () => {
  const [activeTab, setActiveTab] = React.useState('dashboard'); // Set dashboard as default
  const [isClient, setIsClient] = useState(false);
  const { theme: appTheme, setUser } = useStore();
  
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

  return (
    <ConfigProvider theme={themeConfig}>
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
                key: 'diagnostic',
                icon: <SettingOutlined />,
                label: '🔧 Diagnostic',
              },
              {
                key: 'projects',
                icon: <FolderOutlined />,
                label: 'Проекты',
              },
              {
                key: 'ai',
                icon: <CodeOutlined />,
                label: 'AI Shell',
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
                key: 'analytics',
                icon: <BarChartOutlined />,
                label: 'Analytics',
              },
              {
                key: 'rag',
                icon: <DashboardOutlined />,
                label: 'RAG Module',
              },
              {
                key: 'settings',
                icon: <SettingOutlined />,
                label: 'Настройки',
              },
              {
                key: 'pro',
                icon: <SettingOutlined />,
                label: 'Pro Tools',
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
    </ConfigProvider>
  );
};

export default App;