/**
 * Unified Tools Settings Component
 * Configuration and preferences for the unified tools system
 */

import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Form, 
  Switch, 
  Select, 
  InputNumber, 
  Button, 
  Space, 
  Divider, 
  Alert, 
  message,
  Row,
  Col,
  Tooltip,
  Tag
} from 'antd';
import { 
  SettingOutlined,
  SaveOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
  ExperimentOutlined
} from '@ant-design/icons';

const { Option } = Select;

interface ToolsSettings {
  // Execution settings
  defaultTimeout: number;
  maxConcurrentExecutions: number;
  enableAutoRetry: boolean;
  retryAttempts: number;
  
  // UI settings
  showExecutionTime: boolean;
  showParameterHints: boolean;
  enableQuickActions: boolean;
  defaultViewMode: 'grid' | 'list';
  
  // History settings
  maxHistoryEntries: number;
  enableExecutionHistory: boolean;
  autoSaveResults: boolean;
  
  // Performance settings
  enableCaching: boolean;
  cacheTimeout: number;
  enablePreloading: boolean;
  
  // Advanced settings
  enableDebugMode: boolean;
  logLevel: 'error' | 'warn' | 'info' | 'debug';
  enableExperimentalFeatures: boolean;
}

interface UnifiedToolsSettingsProps {
  className?: string;
}

const UnifiedToolsSettings: React.FC<UnifiedToolsSettingsProps> = ({ className = '' }) => {
  const [form] = Form.useForm();
  const [settings, setSettings] = useState<ToolsSettings | null>(null);
  const [loading, setLoading] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  // Default settings
  const defaultSettings: ToolsSettings = {
    defaultTimeout: 300,
    maxConcurrentExecutions: 3,
    enableAutoRetry: true,
    retryAttempts: 2,
    showExecutionTime: true,
    showParameterHints: true,
    enableQuickActions: true,
    defaultViewMode: 'grid',
    maxHistoryEntries: 100,
    enableExecutionHistory: true,
    autoSaveResults: true,
    enableCaching: true,
    cacheTimeout: 300,
    enablePreloading: false,
    enableDebugMode: false,
    logLevel: 'info',
    enableExperimentalFeatures: false
  };

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = () => {
    try {
      const saved = localStorage.getItem('bldr_unified_tools_settings');
      if (saved) {
        const parsedSettings = { ...defaultSettings, ...JSON.parse(saved) };
        setSettings(parsedSettings);
        form.setFieldsValue(parsedSettings);
      } else {
        setSettings(defaultSettings);
        form.setFieldsValue(defaultSettings);
      }
    } catch (error) {
      console.error('Error loading settings:', error);
      setSettings(defaultSettings);
      form.setFieldsValue(defaultSettings);
    }
  };

  const saveSettings = async () => {
    try {
      setLoading(true);
      const values = await form.validateFields();
      
      localStorage.setItem('bldr_unified_tools_settings', JSON.stringify(values));
      setSettings(values);
      setHasChanges(false);
      
      message.success('Settings saved successfully');
      
      // Apply settings immediately
      applySettings(values);
    } catch (error) {
      console.error('Error saving settings:', error);
      message.error('Failed to save settings');
    } finally {
      setLoading(false);
    }
  };

  const resetSettings = () => {
    form.setFieldsValue(defaultSettings);
    setHasChanges(true);
    message.info('Settings reset to defaults');
  };

  const applySettings = (newSettings: ToolsSettings) => {
    // Apply settings to global configuration
    (window as any).bldrToolsSettings = newSettings;
    
    // Apply specific settings
    if (newSettings.enableDebugMode) {
      console.log('Debug mode enabled for unified tools system');
    }
    
    // Set global timeout for API calls
    if ((window as any).bldrApiTimeout) {
      (window as any).bldrApiTimeout = newSettings.defaultTimeout * 1000;
    }
  };

  const handleFormChange = () => {
    setHasChanges(true);
  };

  const exportSettings = () => {
    if (settings) {
      const dataStr = JSON.stringify(settings, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'bldr-tools-settings.json';
      link.click();
      URL.revokeObjectURL(url);
    }
  };

  const importSettings = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
          try {
            const imported = JSON.parse(e.target?.result as string);
            const mergedSettings = { ...defaultSettings, ...imported };
            form.setFieldsValue(mergedSettings);
            setHasChanges(true);
            message.success('Settings imported successfully');
          } catch (error) {
            message.error('Invalid settings file');
          }
        };
        reader.readAsText(file);
      }
    };
    input.click();
  };

  return (
    <div className={className}>
      <Card
        title={
          <Space>
            <SettingOutlined />
            Unified Tools Settings
          </Space>
        }
        extra={
          <Space>
            <Button size="small" onClick={exportSettings}>
              Export
            </Button>
            <Button size="small" onClick={importSettings}>
              Import
            </Button>
            <Button 
              size="small" 
              onClick={resetSettings}
              icon={<ReloadOutlined />}
            >
              Reset
            </Button>
            <Button 
              type="primary" 
              size="small"
              onClick={saveSettings}
              loading={loading}
              disabled={!hasChanges}
              icon={<SaveOutlined />}
            >
              Save Changes
            </Button>
          </Space>
        }
      >
        {hasChanges && (
          <Alert
            message="You have unsaved changes"
            type="warning"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

        <Form
          form={form}
          layout="vertical"
          onValuesChange={handleFormChange}
        >
          {/* Execution Settings */}
          <Card title="⚡ Execution Settings" size="small" style={{ marginBottom: 16 }}>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="defaultTimeout"
                  label={
                    <Space>
                      Default Timeout (seconds)
                      <Tooltip title="Maximum time to wait for tool execution">
                        <InfoCircleOutlined />
                      </Tooltip>
                    </Space>
                  }
                >
                  <InputNumber min={30} max={3600} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="maxConcurrentExecutions"
                  label={
                    <Space>
                      Max Concurrent Executions
                      <Tooltip title="Maximum number of tools that can run simultaneously">
                        <InfoCircleOutlined />
                      </Tooltip>
                    </Space>
                  }
                >
                  <InputNumber min={1} max={10} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>
            
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="enableAutoRetry" valuePropName="checked">
                  <Switch /> Enable Auto Retry on Failure
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="retryAttempts"
                  label="Retry Attempts"
                >
                  <InputNumber min={1} max={5} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>
          </Card>

          {/* UI Settings */}
          <Card title="🎨 User Interface Settings" size="small" style={{ marginBottom: 16 }}>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="showExecutionTime" valuePropName="checked">
                  <Switch /> Show Execution Time
                </Form.Item>
                <Form.Item name="showParameterHints" valuePropName="checked">
                  <Switch /> Show Parameter Hints
                </Form.Item>
                <Form.Item name="enableQuickActions" valuePropName="checked">
                  <Switch /> Enable Quick Actions
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="defaultViewMode"
                  label="Default View Mode"
                >
                  <Select style={{ width: '100%' }}>
                    <Option value="grid">Grid View</Option>
                    <Option value="list">List View</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>
          </Card>

          {/* History Settings */}
          <Card title="📚 History Settings" size="small" style={{ marginBottom: 16 }}>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="enableExecutionHistory" valuePropName="checked">
                  <Switch /> Enable Execution History
                </Form.Item>
                <Form.Item name="autoSaveResults" valuePropName="checked">
                  <Switch /> Auto Save Results
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="maxHistoryEntries"
                  label="Max History Entries"
                >
                  <InputNumber min={10} max={1000} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>
          </Card>

          {/* Performance Settings */}
          <Card title="🚀 Performance Settings" size="small" style={{ marginBottom: 16 }}>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="enableCaching" valuePropName="checked">
                  <Switch /> Enable Result Caching
                </Form.Item>
                <Form.Item name="enablePreloading" valuePropName="checked">
                  <Switch /> Enable Tool Preloading
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="cacheTimeout"
                  label="Cache Timeout (seconds)"
                >
                  <InputNumber min={60} max={3600} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>
          </Card>

          {/* Advanced Settings */}
          <Card 
            title={
              <Space>
                <ExperimentOutlined />
                Advanced Settings
                <Tag color="orange">Advanced</Tag>
              </Space>
            } 
            size="small"
          >
            <Alert
              message="Advanced Settings"
              description="These settings are for advanced users only. Changing them may affect system performance."
              type="warning"
              showIcon
              style={{ marginBottom: 16 }}
            />
            
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="enableDebugMode" valuePropName="checked">
                  <Switch /> Enable Debug Mode
                </Form.Item>
                <Form.Item name="enableExperimentalFeatures" valuePropName="checked">
                  <Switch /> Enable Experimental Features
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="logLevel"
                  label="Log Level"
                >
                  <Select style={{ width: '100%' }}>
                    <Option value="error">Error</Option>
                    <Option value="warn">Warning</Option>
                    <Option value="info">Info</Option>
                    <Option value="debug">Debug</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>
          </Card>
        </Form>
      </Card>
    </div>
  );
};

export default UnifiedToolsSettings;