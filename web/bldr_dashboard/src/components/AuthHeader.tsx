import React, { useState, useEffect } from 'react';
import { Layout, Button, Modal, Form, Input, message, Switch, Avatar, Dropdown } from 'antd';
import { UserOutlined, SunOutlined, MoonOutlined } from '@ant-design/icons';
import { useStore } from '../store';
import { apiService } from '../services/api';
import { useToolTabs } from '../contexts/ToolTabsContext';
import { useTranslation } from '../contexts/LocalizationContext';
import LanguageSwitcher from './LanguageSwitcher';
import StatusPills from './StatusPills';

const { Header } = Layout;

// Function to refresh token
const refreshToken = async () => {
  try {
    const response = await fetch('/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: 'username=admin&password=admin123'  // Default credentials
    });
    
    if (response.ok) {
      const data = await response.json();
      return { success: true, token: data.access_token };
    } else {
      return { success: false, error: 'Failed to refresh token' };
    }
  } catch (error) {
    return { success: false, error: error.message };
  }
};

const AuthHeader: React.FC = () => {
  const [showLogin, setShowLogin] = useState(false);
  const [loading, setLoading] = useState(false);
  const { user, theme, setTheme, setUser, clearUser } = useStore();
  const t = useTranslation();
  
  // Используем глобальный контекст для Tool Tabs
  const { openToolInNewTab } = useToolTabs();
  
  // Check if authentication is disabled
  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        // Use dedicated endpoint to detect if auth is skipped
        const debugInfo = await apiService.getAuthDebug();
        if (debugInfo && (debugInfo.skip_auth === 'true' || debugInfo.skip_auth === true)) {
          // Re-check current user from store to avoid race conditions
          const currentUser = useStore.getState().user;
          if (!currentUser) {
            setUser({
              token: "disabled_auth_token",
              role: "admin",  // Changed from "user" to "admin" when auth is disabled
              username: "anonymous"
            });
          }
        }
      } catch (error) {
        // Auth is enabled, do nothing
      }
    };
    
    // Only check if no user is set
    if (!user) {
      checkAuthStatus();
    }
  }, [user, setUser]);
  
  // Add effect to handle token restoration from localStorage
  useEffect(() => {
    const restoreToken = async () => {
      const token = localStorage.getItem('auth-token');
      const savedUser = localStorage.getItem('auth-user');
      
      if (token && !user) {
        try {
          let userData = null;
          
          // Try to get saved user data first
          if (savedUser) {
            try {
              userData = JSON.parse(savedUser);
            } catch (e) {
              console.log('Could not parse saved user data');
            }
          }
          
          // For JWT tokens, try to parse and validate
          if (token.includes('.') && token !== "disabled_auth_token") {
            const payload = JSON.parse(atob(token.split('.')[1]));
            const exp = payload.exp;
            const now = Math.floor(Date.now() / 1000);
            
            // Check if token expires in the next 5 minutes or is already expired
            if (exp && (now >= exp || (exp - now) < 300)) {
              // Token expired or expiring soon, try to refresh it automatically
              console.log('Token expired or expiring soon, attempting to refresh...');
              try {
                const refreshResult = await refreshToken();
                if (refreshResult.success) {
                  console.log('Token refreshed successfully');
                  // Continue with the new token
                  const newToken = refreshResult.token;
                  localStorage.setItem('auth-token', newToken);
                  // Re-parse the new token
                  const newPayload = JSON.parse(atob(newToken.split('.')[1]));
                  const username = userData?.username || newPayload.sub || 'user';
                  const role = userData?.role || newPayload.role || (username === 'admin' ? 'admin' : 'user');
                  
                  setUser({
                    username,
                    role,
                    isAuthenticated: true,
                    token: newToken
                  });
                  return;
                }
              } catch (error) {
                console.log('Token refresh failed:', error);
              }
              
              // If refresh failed, remove expired token
              localStorage.removeItem('auth-token');
              localStorage.removeItem('auth-user');
              return;
            }
            
            // Token is valid, restore user with enhanced data
            const username = userData?.username || payload.sub || 'user';
            const role = userData?.role || payload.role || (username === 'admin' ? 'admin' : 'user');
            
            setUser({
              token,
              role,
              username
            });
            
            console.log(`Restored user: ${username} (${role})`);
            
          } else if (token === "disabled_auth_token") {
            // Restore mock user
            setUser({
              token,
              role: "admin",  // Changed from "user" to "admin" when auth is disabled
              username: "anonymous"
            });
            console.log('Restored anonymous user (auth disabled)');
          }
        } catch (e) {
          // Invalid token, remove it
          console.error('Error restoring token:', e);
          localStorage.removeItem('auth-token');
          localStorage.removeItem('auth-user');
        }
      }
    };
    
    restoreToken();
  }, [setUser]);
  
  // Check token expiration periodically
  useEffect(() => {
    if (user && user.token !== "disabled_auth_token") {
      const checkTokenExpiration = async () => {
        try {
          // Only check JWT tokens, not mock tokens
          if (user.token && user.token.includes('.') && user.token !== "disabled_auth_token") {
            const payload = JSON.parse(atob(user.token.split('.')[1]));
            const exp = payload.exp;
            const now = Math.floor(Date.now() / 1000);
            
            // Check if token expires in the next 5 minutes or is already expired
            if (exp && (now >= exp || (exp - now) < 300)) {
              // Try to refresh token first
              try {
                const refreshResult = await refreshToken();
                if (refreshResult.success) {
                  console.log('Token refreshed successfully in useEffect');
                  // Update user with new token
                  setUser({
                    ...user,
                    token: refreshResult.token
                  });
                  return;
                }
              } catch (error) {
                  console.log('Token refresh failed in useEffect:', error);
                }
              
              // If refresh failed, clear user
              clearUser();
              message.warning('Сессия истекла — перелогиньтесь');
            }
          }
        } catch (e) {
          // If we can't parse the token, it might be a mock token, so don't clear it
          console.log('Could not parse token, might be mock token');
        }
      };
      
      // Check immediately
      checkTokenExpiration().catch(console.error);
      
      // Check every minute
      const interval = setInterval(() => {
        checkTokenExpiration().catch(console.error);
      }, 60000);
      
      return () => clearInterval(interval);
    }
  }, [user, clearUser]);
  
  const handleLogin = async (values: any) => {
    setLoading(true);
    try {
      // Try to get a real token from the backend using the provided credentials
      const tokenResponse = await apiService.getToken(values.username, values.password);
      
      if (tokenResponse) {
        // Parse token to get role information
        let userRole = 'user';
        try {
          // Try to decode JWT to get role
          if (tokenResponse.includes('.')) {
            const payload = JSON.parse(atob(tokenResponse.split('.')[1]));
            userRole = payload.role || 'user';
            console.log('JWT payload:', payload); // Debug log
          }
        } catch (e) {
          console.error('Error parsing JWT:', e);
          // Fallback to username-based role detection
          userRole = values.username === 'admin' ? 'admin' : 'user';
        }
        
        console.log(`Login successful: ${values.username} with role: ${userRole}`); // Debug log
        
        // Create user object with token
        const user = {
          token: tokenResponse,
          role: userRole,
          username: values.username
        };
        
        // Save both token and user data to localStorage for persistence
        localStorage.setItem('auth-token', tokenResponse);
        localStorage.setItem('auth-user', JSON.stringify({
          username: values.username,
          role: userRole
        }));
        
        setUser(user);
        setShowLogin(false);
        message.success(`Добро пожаловать, ${user.username}!`);
      } else {
        throw new Error('No token received');
      }
    } catch (error: any) {
      console.error('Failed to get token:', error);
      
      // Enhanced error handling with better user feedback
      if (error.response?.status === 401) {
        message.error('Неверный логин или пароль');
      } else if (error.response?.status === 403) {
        message.error('Доступ запрещен');
      } else if (error.response?.status >= 500) {
        message.error('Ошибка сервера. Попробуйте позже.');
      } else if (!error.response) {
        message.error('Сервер недоступен. Проверьте подключение.');
      } else {
        message.error('Ошибка входа: ' + (error.response?.data?.detail || error.message || 'Неизвестная ошибка'));
      }
    } finally {
      setLoading(false);
    }
  };
  
  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
  };
  
  const handleLogout = () => {
    console.log('Logging out user:', user?.username);
    
    // Clear user state
    clearUser();
    
    // Clear all auth-related localStorage items
    localStorage.removeItem('auth-token');
    localStorage.removeItem('auth-user');
    localStorage.removeItem('bldr-empire-storage');
    
    // Clear any other potential auth storage
    const keysToRemove = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && (key.includes('auth') || key.includes('token') || key.includes('user'))) {
        keysToRemove.push(key);
      }
    }
    
    keysToRemove.forEach(key => {
      localStorage.removeItem(key);
    });
    
    message.success('Вы успешно вышли из системы');
    console.log('User logged out and localStorage cleared');
  };
  
  // Обработчик глобального поиска инструментов
  const handleGlobalSearch = async (query: string) => {
    if (!query.trim()) return;
    
    try {
      // Ищем инструмент по названию
      const response = await apiService.get(`/api/tools/discovery?search=${encodeURIComponent(query)}`);
      
      if (response.status === 'success' && response.data?.tools) {
        const tools = response.data.tools;
        const exactMatch = tools.find((tool: any) => 
          tool.name.toLowerCase() === query.toLowerCase()
        );
        const partialMatch = tools.find((tool: any) => 
          tool.name.toLowerCase().includes(query.toLowerCase())
        );
        
        const targetTool = exactMatch || partialMatch;
        
        if (targetTool) {
          // Открываем найденный инструмент в Tool Tab
          await openToolInNewTab(targetTool);
          message.success(`Инструмент "${targetTool.name}" открыт в Tool Tab`);
        } else {
          message.warning(`Инструмент "${query}" не найден`);
        }
      } else {
        message.warning(`Инструмент "${query}" не найден`);
      }
    } catch (error) {
      console.error('Error searching for tool:', error);
      message.error('Ошибка поиска инструмента');
    }
  };
  
  const menuItems = [
    { key: 'profile', label: <>Роль: {user?.role}</> },
    { key: 'logout', label: 'Выход' },
  ];
  
  return (
    <Header style={{ 
      display: 'flex', 
      alignItems: 'center',
      padding: '0 24px',
      background: theme === 'dark' ? '#141414' : '#ffffff'
    }}>
      <Input.Search 
        placeholder={t('navigation.search')} 
        style={{ width: 200, marginRight: 16 }}
        onSearch={handleGlobalSearch}
        enterButton
      />
      
      <LanguageSwitcher 
        size="small" 
        style={{ marginRight: 16 }} 
      />
      
      {user ? (
        <Dropdown 
          trigger={['click']}
          menu={{ 
            items: menuItems,
            onClick: ({ key }) => { if (key === 'logout') handleLogout(); }
          }}
        >
          <Avatar icon={<UserOutlined />} style={{ cursor: 'pointer' }} />
        </Dropdown>
      ) : (
        <Button 
          type="primary" 
          onClick={() => setShowLogin(true)}
          data-cy="login-btn"
        >
          Войти
        </Button>
      )}
      
      <StatusPills />
      <Switch
        checked={theme === 'dark'}
        onChange={toggleTheme}
        checkedChildren={<MoonOutlined />}
        unCheckedChildren={<SunOutlined />}
        style={{ marginLeft: 16 }}
      />
      
      <Modal
        open={showLogin}
        onCancel={() => setShowLogin(false)}
        footer={null}
        title="Вход в систему"
      >
        <Form onFinish={handleLogin}>
          <Form.Item
            name="username"
            label="Логин"
            rules={[{ required: true, message: 'Пожалуйста, введите логин!' }]}
          >
            <Input data-cy="username" />
          </Form.Item>
          
          <Form.Item
            name="password"
            label="Пароль"
            rules={[{ required: true, message: 'Пожалуйста, введите пароль!' }]}
          >
            <Input.Password data-cy="password" />
          </Form.Item>
          
          <Form.Item>
            <Button 
              type="primary" 
              htmlType="submit" 
              loading={loading}
              data-cy="submit-login"
            >
              Войти
            </Button>
          </Form.Item>
        </Form>
        <div style={{ marginTop: 16, fontSize: '12px', color: '#888' }}>
          <p>Для тестирования используйте любые логин/пароль</p>
          <p>Логин "admin" для получения роли администратора</p>
        </div>
      </Modal>
    </Header>
  );
};

export default AuthHeader;