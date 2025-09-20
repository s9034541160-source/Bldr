/**
 * Tool Execution History Component
 * Shows history of tool executions with filtering and search
 */

import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Table, 
  Tag, 
  Space, 
  Button, 
  Input, 
  Select, 
  DatePicker, 
  Modal,
  Tooltip,
  Badge
} from 'antd';
import { 
  HistoryOutlined,
  SearchOutlined,
  EyeOutlined,
  DeleteOutlined,
  ReloadOutlined,
  FilterOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import ToolResultDisplay from './ToolResultDisplay';

const { RangePicker } = DatePicker;
const { Option } = Select;

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

interface HistoryEntry extends StandardResponse {
  id: string;
}

interface ToolExecutionHistoryProps {
  className?: string;
}

const ToolExecutionHistory: React.FC<ToolExecutionHistoryProps> = ({ className = '' }) => {
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [filteredHistory, setFilteredHistory] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [toolFilter, setToolFilter] = useState<string>('all');
  const [selectedResult, setSelectedResult] = useState<HistoryEntry | null>(null);
  const [resultModalVisible, setResultModalVisible] = useState(false);

  // Load history from localStorage on component mount
  useEffect(() => {
    loadHistory();
  }, []);

  // Filter history when filters change
  useEffect(() => {
    filterHistory();
  }, [history, searchTerm, statusFilter, toolFilter]);

  const loadHistory = () => {
    try {
      const saved = localStorage.getItem('bldr_tool_execution_history');
      if (saved) {
        const parsed = JSON.parse(saved);
        setHistory(parsed);
      }
    } catch (error) {
      console.error('Error loading history:', error);
    }
  };

  const saveHistory = (newHistory: HistoryEntry[]) => {
    try {
      // Keep only last 100 entries to prevent localStorage bloat
      const trimmed = newHistory.slice(-100);
      localStorage.setItem('bldr_tool_execution_history', JSON.stringify(trimmed));
      setHistory(trimmed);
    } catch (error) {
      console.error('Error saving history:', error);
    }
  };

  const addToHistory = (result: StandardResponse) => {
    const entry: HistoryEntry = {
      ...result,
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    };
    
    const newHistory = [...history, entry];
    saveHistory(newHistory);
  };

  const clearHistory = () => {
    localStorage.removeItem('bldr_tool_execution_history');
    setHistory([]);
  };

  const filterHistory = () => {
    let filtered = [...history];

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(entry => 
        entry.tool_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (entry.error && entry.error.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(entry => entry.status === statusFilter);
    }

    // Tool filter
    if (toolFilter !== 'all') {
      filtered = filtered.filter(entry => entry.tool_name === toolFilter);
    }

    // Sort by timestamp (newest first)
    filtered.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

    setFilteredHistory(filtered);
  };

  const showResult = (entry: HistoryEntry) => {
    setSelectedResult(entry);
    setResultModalVisible(true);
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      success: { color: 'success', text: 'Success' },
      error: { color: 'error', text: 'Error' },
      warning: { color: 'warning', text: 'Warning' }
    };
    
    const config = statusConfig[status as keyof typeof statusConfig] || { color: 'default', text: status };
    return <Badge status={config.color as any} text={config.text} />;
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    if (seconds < 1) return `${(seconds * 1000).toFixed(0)}ms`;
    return `${seconds.toFixed(2)}s`;
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString();
    } catch {
      return timestamp;
    }
  };

  // Get unique tools for filter
  const uniqueTools = Array.from(new Set(history.map(entry => entry.tool_name))).sort();

  const columns: ColumnsType<HistoryEntry> = [
    {
      title: 'Tool',
      dataIndex: 'tool_name',
      key: 'tool_name',
      render: (text) => <Tag color="blue">{text}</Tag>,
      sorter: (a, b) => a.tool_name.localeCompare(b.tool_name),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => getStatusBadge(status),
      filters: [
        { text: 'Success', value: 'success' },
        { text: 'Error', value: 'error' },
        { text: 'Warning', value: 'warning' },
      ],
      onFilter: (value, record) => record.status === value,
    },
    {
      title: 'Duration',
      dataIndex: 'execution_time',
      key: 'execution_time',
      render: (time) => formatDuration(time),
      sorter: (a, b) => (a.execution_time || 0) - (b.execution_time || 0),
    },
    {
      title: 'Timestamp',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp) => formatTimestamp(timestamp),
      sorter: (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
    },
    {
      title: 'Files',
      dataIndex: 'files',
      key: 'files',
      render: (files) => files ? <Badge count={files.length} showZero /> : <Badge count={0} />,
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Tooltip title="View Result">
            <Button
              type="text"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => showResult(record)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  // Expose addToHistory method globally for other components to use
  React.useEffect(() => {
    (window as any).addToolExecutionToHistory = addToHistory;
    return () => {
      delete (window as any).addToolExecutionToHistory;
    };
  }, [history]);

  return (
    <div className={className}>
      <Card
        title={
          <Space>
            <HistoryOutlined />
            Tool Execution History ({filteredHistory.length})
          </Space>
        }
        extra={
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={loadHistory}
              size="small"
            >
              Refresh
            </Button>
            <Button
              icon={<DeleteOutlined />}
              onClick={clearHistory}
              size="small"
              danger
            >
              Clear History
            </Button>
          </Space>
        }
      >
        {/* Filters */}
        <div style={{ marginBottom: 16 }}>
          <Space wrap>
            <Input
              placeholder="Search tools or errors..."
              prefix={<SearchOutlined />}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ width: 250 }}
              allowClear
            />
            
            <Select
              placeholder="Filter by status"
              value={statusFilter}
              onChange={setStatusFilter}
              style={{ width: 150 }}
            >
              <Option value="all">All Status</Option>
              <Option value="success">Success</Option>
              <Option value="error">Error</Option>
              <Option value="warning">Warning</Option>
            </Select>
            
            <Select
              placeholder="Filter by tool"
              value={toolFilter}
              onChange={setToolFilter}
              style={{ width: 200 }}
              showSearch
            >
              <Option value="all">All Tools</Option>
              {uniqueTools.map(tool => (
                <Option key={tool} value={tool}>{tool}</Option>
              ))}
            </Select>
          </Space>
        </div>

        {/* History Table */}
        <Table
          columns={columns}
          dataSource={filteredHistory}
          rowKey="id"
          loading={loading}
          size="small"
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} executions`,
          }}
          scroll={{ x: 800 }}
        />
      </Card>

      {/* Result Detail Modal */}
      <Modal
        title="Tool Execution Result"
        open={resultModalVisible}
        onCancel={() => setResultModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedResult && (
          <ToolResultDisplay
            result={selectedResult}
            onDownloadFile={(filePath) => {
              // Handle file download
              window.open(filePath, '_blank');
            }}
          />
        )}
      </Modal>
    </div>
  );
};

export default ToolExecutionHistory;