/**
 * Quick Tools Widget Component
 * Provides quick access to most used tools on dashboard
 */

import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Button, 
  Space, 
  Tooltip, 
  Badge, 
  Row, 
  Col,
  Spin,
  message
} from 'antd';
import { 
  ThunderboltOutlined,
  FileTextOutlined,
  CalculatorOutlined,
  SearchOutlined,
  BarChartOutlined,
  ToolOutlined,
  StarFilled
} from '@ant-design/icons';
import { apiService, unwrap } from '../services/api';
import { useToolTabs } from '../contexts/ToolTabsContext';
import { useTranslation } from '../contexts/LocalizationContext';

interface QuickTool {
  name: string;
  icon: React.ReactNode;
  color: string;
  description: string;
  category: string;
}

interface QuickToolsWidgetProps {
  onToolExecute?: (toolName: string) => void;
  className?: string;
}

const QuickToolsWidget: React.FC<QuickToolsWidgetProps> = ({ 
  onToolExecute,
  className = '' 
}) => {
  const [executing, setExecuting] = useState<string | null>(null);
  const [toolStats, setToolStats] = useState<Record<string, number>>({});
  const t = useTranslation();
  
  // Используем глобальный контекст для Tool Tabs
  const { openToolInNewTab } = useToolTabs();

  // Predefined quick tools with icons and colors
  const quickTools: QuickTool[] = [
    {
      name: 'generate_letter',
      icon: <FileTextOutlined />,
      color: '#1890ff',
      description: 'Generate official letter',
      category: 'document_generation'
    },
    {
      name: 'calculate_estimate',
      icon: <CalculatorOutlined />,
      color: '#52c41a',
      description: 'Calculate construction estimate',
      category: 'financial'
    },
    {
      name: 'search_rag_database',
      icon: <SearchOutlined />,
      color: '#722ed1',
      description: 'Search knowledge base',
      category: 'core_rag'
    },
    {
      name: 'analyze_tender',
      icon: <BarChartOutlined />,
      color: '#fa8c16',
      description: 'Analyze tender documents',
      category: 'advanced_analysis'
    },
    {
      name: 'auto_budget',
      icon: <CalculatorOutlined />,
      color: '#13c2c2',
      description: 'Generate project budget',
      category: 'financial'
    },
    {
      name: 'analyze_image',
      icon: <ToolOutlined />,
      color: '#eb2f96',
      description: 'Analyze construction images',
      category: 'advanced_analysis'
    }
  ];

  useEffect(() => {
    loadToolStats();
  }, []);

  const loadToolStats = () => {
    // Load usage statistics from localStorage
    const saved = localStorage.getItem('bldr_tool_usage_stats');
    if (saved) {
      try {
        setToolStats(JSON.parse(saved));
      } catch (error) {
        console.error('Error loading tool stats:', error);
      }
    }
  };

  const updateToolStats = (toolName: string) => {
    const newStats = {
      ...toolStats,
      [toolName]: (toolStats[toolName] || 0) + 1
    };
    setToolStats(newStats);
    localStorage.setItem('bldr_tool_usage_stats', JSON.stringify(newStats));
  };

  const executeQuickTool = async (toolName: string) => {
    try {
      setExecuting(toolName);
      
      // !!! НОВАЯ ЛОГИКА: Добавляем инструмент в Tool Tab вместо прямого выполнения !!!
      const toolInfo = {
        name: toolName,
        category: 'quick_tools',
        description: `Quick access to ${toolName}`,
        ui_placement: 'dashboard' as const,
        available: true,
        source: 'quick_tools'
      };
      
      // Открываем инструмент в новой вкладке Tool Tab
      await openToolInNewTab(toolInfo);
      
      // Update usage statistics
      updateToolStats(toolName);
      
      // Notify parent component
      if (onToolExecute) {
        onToolExecute(toolName);
      }

      message.success(`${toolName} opened in Tool Tab`);
    } catch (error) {
      console.error(`Error opening ${toolName} in Tool Tab:`, error);
      message.error(`Failed to open ${toolName} in Tool Tab`);
    } finally {
      setExecuting(null);
    }
  };

  const getMostUsedTools = () => {
    return quickTools
      .map(tool => ({
        ...tool,
        usage: toolStats[tool.name] || 0
      }))
      .sort((a, b) => b.usage - a.usage)
      .slice(0, 4);
  };

  const renderQuickToolButton = (tool: QuickTool, usage?: number) => {
    const isExecuting = executing === tool.name;
    
    return (
      <Tooltip key={tool.name} title={tool.description}>
        <Button
          type="primary"
          size="large"
          icon={tool.icon}
          loading={isExecuting}
          onClick={() => executeQuickTool(tool.name)}
          style={{
            backgroundColor: tool.color,
            borderColor: tool.color,
            height: '60px',
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          <div style={{ fontSize: '12px', marginTop: '4px' }}>
            {tool.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </div>
          {usage && usage > 0 && (
            <Badge 
              count={usage} 
              size="small" 
              style={{ 
                position: 'absolute', 
                top: '-5px', 
                right: '-5px' 
              }} 
            />
          )}
        </Button>
      </Tooltip>
    );
  };

  return (
    <div className={className}>
      {/* Quick Access Tools */}
      <Card 
        title={
          <Space>
            <ThunderboltOutlined />
            Quick Tools
          </Space>
        }
        size="small"
        style={{ marginBottom: 16 }}
      >
        <Row gutter={[8, 8]}>
          {quickTools.slice(0, 6).map(tool => (
            <Col key={tool.name} span={8}>
              {renderQuickToolButton(tool)}
            </Col>
          ))}
        </Row>
      </Card>

      {/* Most Used Tools */}
      {Object.keys(toolStats).length > 0 && (
        <Card 
          title={
            <Space>
              <StarFilled style={{ color: '#faad14' }} />
              Most Used
            </Space>
          }
          size="small"
        >
          <Row gutter={[8, 8]}>
            {getMostUsedTools().map(tool => (
              <Col key={`used-${tool.name}`} span={12}>
                {renderQuickToolButton(tool, tool.usage)}
              </Col>
            ))}
          </Row>
        </Card>
      )}
    </div>
  );
};

export default QuickToolsWidget;