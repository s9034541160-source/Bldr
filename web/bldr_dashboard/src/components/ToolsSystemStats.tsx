/**
 * Tools System Statistics Component
 * Shows comprehensive statistics about the unified tools system
 */

import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Row, 
  Col, 
  Statistic, 
  Progress, 
  Tag, 
  Space, 
  Tooltip,
  Button,
  Spin
} from 'antd';
import { 
  DashboardOutlined,
  ToolOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  ReloadOutlined,
  TrophyOutlined,
  FireOutlined
} from '@ant-design/icons';
import { apiService } from '../services/api';

interface SystemStats {
  totalTools: number;
  availableTools: number;
  dashboardTools: number;
  professionalTools: number;
  serviceTools: number;
  categories: Record<string, number>;
  executionStats: {
    totalExecutions: number;
    successRate: number;
    averageExecutionTime: number;
    mostUsedTool: string;
    recentExecutions: number;
  };
}

interface ToolsSystemStatsProps {
  className?: string;
}

const ToolsSystemStats: React.FC<ToolsSystemStatsProps> = ({ className = '' }) => {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      
      // Load tools discovery data
      const discovery = await apiService.discoverTools();
      const tools = Object.values(discovery.data.tools);
      
      // Load execution history from localStorage
      const historyData = localStorage.getItem('bldr_tool_execution_history');
      const usageData = localStorage.getItem('bldr_tool_usage_stats');
      
      let executionHistory: any[] = [];
      let usageStats: Record<string, number> = {};
      
      if (historyData) {
        executionHistory = JSON.parse(historyData);
      }
      
      if (usageData) {
        usageStats = JSON.parse(usageData);
      }

      // Calculate statistics
      const totalTools = tools.length;
      const availableTools = tools.filter((tool: any) => tool.available).length;
      const dashboardTools = tools.filter((tool: any) => tool.ui_placement === 'dashboard').length;
      const professionalTools = tools.filter((tool: any) => tool.ui_placement === 'tools').length;
      const serviceTools = tools.filter((tool: any) => tool.ui_placement === 'service').length;
      
      // Category statistics
      const categories: Record<string, number> = {};
      tools.forEach((tool: any) => {
        categories[tool.category] = (categories[tool.category] || 0) + 1;
      });

      // Execution statistics
      const totalExecutions = executionHistory.length;
      const successfulExecutions = executionHistory.filter(exec => exec.status === 'success').length;
      const successRate = totalExecutions > 0 ? (successfulExecutions / totalExecutions) * 100 : 0;
      
      const executionTimes = executionHistory
        .filter(exec => exec.execution_time)
        .map(exec => exec.execution_time);
      const averageExecutionTime = executionTimes.length > 0 
        ? executionTimes.reduce((a, b) => a + b, 0) / executionTimes.length 
        : 0;

      // Most used tool
      const mostUsedTool = Object.keys(usageStats).length > 0
        ? Object.entries(usageStats).sort(([,a], [,b]) => b - a)[0][0]
        : 'N/A';

      // Recent executions (last 24 hours)
      const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
      const recentExecutions = executionHistory.filter(exec => 
        new Date(exec.timestamp) > oneDayAgo
      ).length;

      setStats({
        totalTools,
        availableTools,
        dashboardTools,
        professionalTools,
        serviceTools,
        categories,
        executionStats: {
          totalExecutions,
          successRate,
          averageExecutionTime,
          mostUsedTool,
          recentExecutions
        }
      });
      
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error loading system stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const getCategoryColor = (category: string): string => {
    const colors: Record<string, string> = {
      financial: 'blue',
      advanced_analysis: 'red',
      document_generation: 'orange',
      project_management: 'purple',
      core_rag: 'green',
      data_processing: 'gray',
      other: 'default',
    };
    return colors[category] || colors.other;
  };

  const getCategoryIcon = (category: string): string => {
    const icons: Record<string, string> = {
      financial: '💰',
      advanced_analysis: '🧠',
      document_generation: '📄',
      project_management: '📅',
      core_rag: '🔍',
      data_processing: '⚙️',
      other: '🔧',
    };
    return icons[category] || icons.other;
  };

  if (loading) {
    return (
      <Card className={className}>
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <Spin size="large" />
          <p style={{ marginTop: 16 }}>Loading system statistics...</p>
        </div>
      </Card>
    );
  }

  if (!stats) {
    return (
      <Card className={className}>
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <p>Failed to load system statistics</p>
          <Button onClick={loadStats} icon={<ReloadOutlined />}>
            Retry
          </Button>
        </div>
      </Card>
    );
  }

  const availabilityRate = (stats.availableTools / stats.totalTools) * 100;

  return (
    <div className={className}>
      {/* Header */}
      <Card 
        title={
          <Space>
            <DashboardOutlined />
            System Statistics
          </Space>
        }
        extra={
          <Space>
            <span style={{ fontSize: '12px', color: '#666' }}>
              Updated: {lastUpdated.toLocaleTimeString()}
            </span>
            <Button 
              size="small" 
              icon={<ReloadOutlined />} 
              onClick={loadStats}
              loading={loading}
            >
              Refresh
            </Button>
          </Space>
        }
        style={{ marginBottom: 16 }}
      >
        {/* Main Statistics */}
        <Row gutter={16}>
          <Col span={6}>
            <Statistic
              title="Total Tools"
              value={stats.totalTools}
              prefix={<ToolOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="Available"
              value={stats.availableTools}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
              suffix={
                <Tooltip title={`${availabilityRate.toFixed(1)}% availability rate`}>
                  <Progress 
                    type="circle" 
                    size={40} 
                    percent={availabilityRate} 
                    showInfo={false}
                    strokeColor="#52c41a"
                  />
                </Tooltip>
              }
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="Success Rate"
              value={stats.executionStats.successRate}
              precision={1}
              suffix="%"
              prefix={<TrophyOutlined />}
              valueStyle={{ 
                color: stats.executionStats.successRate > 80 ? '#52c41a' : 
                       stats.executionStats.successRate > 60 ? '#faad14' : '#ff4d4f' 
              }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="Avg. Execution"
              value={stats.executionStats.averageExecutionTime}
              precision={2}
              suffix="s"
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Col>
        </Row>
      </Card>

      {/* Tool Distribution */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={8}>
          <Card size="small" title="🎯 Dashboard Tools">
            <Statistic
              value={stats.dashboardTools}
              valueStyle={{ color: '#1890ff', fontSize: '32px' }}
            />
            <p style={{ margin: 0, color: '#666', fontSize: '12px' }}>
              High-impact daily tools
            </p>
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small" title="🔧 Professional Tools">
            <Statistic
              value={stats.professionalTools}
              valueStyle={{ color: '#52c41a', fontSize: '32px' }}
            />
            <p style={{ margin: 0, color: '#666', fontSize: '12px' }}>
              Specialized expert tools
            </p>
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small" title="⚙️ Service Tools">
            <Statistic
              value={stats.serviceTools}
              valueStyle={{ color: '#666', fontSize: '32px' }}
            />
            <p style={{ margin: 0, color: '#666', fontSize: '12px' }}>
              Hidden system tools
            </p>
          </Card>
        </Col>
      </Row>

      {/* Execution Statistics */}
      <Card 
        title="📊 Execution Statistics" 
        size="small"
        style={{ marginBottom: 16 }}
      >
        <Row gutter={16}>
          <Col span={6}>
            <Statistic
              title="Total Executions"
              value={stats.executionStats.totalExecutions}
              prefix={<FireOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="Recent (24h)"
              value={stats.executionStats.recentExecutions}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Col>
          <Col span={12}>
            <div>
              <p style={{ margin: '0 0 8px 0', fontWeight: 'bold' }}>Most Used Tool:</p>
              <Tag color="gold" style={{ fontSize: '14px' }}>
                🏆 {stats.executionStats.mostUsedTool}
              </Tag>
            </div>
          </Col>
        </Row>
      </Card>

      {/* Categories */}
      <Card title="📂 Tools by Category" size="small">
        <Row gutter={[8, 8]}>
          {Object.entries(stats.categories)
            .sort(([,a], [,b]) => b - a)
            .map(([category, count]) => (
              <Col key={category} span={8}>
                <Card size="small" style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '20px', marginBottom: '4px' }}>
                    {getCategoryIcon(category)}
                  </div>
                  <div style={{ fontSize: '18px', fontWeight: 'bold', color: getCategoryColor(category) }}>
                    {count}
                  </div>
                  <div style={{ fontSize: '12px', color: '#666' }}>
                    {category.replace('_', ' ').toUpperCase()}
                  </div>
                </Card>
              </Col>
            ))}
        </Row>
      </Card>
    </div>
  );
};

export default ToolsSystemStats;