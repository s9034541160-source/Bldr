import React, { useEffect, useMemo, useState } from 'react';
import { Card, Row, Col, Input, Select, Tag, Space, Button, Badge, Tooltip, Empty, message } from 'antd';
import { AppstoreOutlined, PlayCircleOutlined, InfoCircleOutlined, ReloadOutlined } from '@ant-design/icons';
import { apiService } from '../services/api';

const { Option } = Select;

interface ToolInfo {
  name: string;
  category: string;
  description: string;
  ui_placement: 'dashboard' | 'tools' | 'service';
  available: boolean;
  source?: string;
}

const ToolsCatalogWidget: React.FC = () => {
  const [tools, setTools] = useState<Record<string, ToolInfo>>({});
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState<string>('all');
  const [executing, setExecuting] = useState<string | null>(null);

  const load = async () => {
    try {
      setLoading(true);
      const resp = await apiService.discoverTools();
      setTools(resp.data.tools || {});
    } catch (e) {
      message.error('Не удалось загрузить каталог инструментов');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const categories = useMemo(() => {
    const set = new Set<string>(['all']);
    Object.values(tools).forEach(t => set.add(t.category));
    return Array.from(set);
  }, [tools]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return Object.values(tools).filter(t => {
      if (category !== 'all' && t.category !== category) return false;
      if (!q) return true;
      return t.name.toLowerCase().includes(q) || t.description.toLowerCase().includes(q);
    });
  }, [tools, category, search]);

  const execute = async (toolName: string) => {
    try {
      setExecuting(toolName);
      const result = await apiService.executeUnifiedTool(toolName, {});
      if (result.status === 'success') message.success(`${toolName} выполнен`);
      else message.error(`Ошибка: ${result.error || 'неизвестно'}`);
    } catch (e: any) {
      message.error(`Сбой выполнения ${toolName}`);
    } finally {
      setExecuting(null);
    }
  };

  return (
    <Card
      title={<Space><AppstoreOutlined /> Каталог инструментов</Space>}
      extra={<Button icon={<ReloadOutlined />} onClick={load} loading={loading}>Обновить</Button>}
      style={{ marginTop: 16 }}
    >
      <Space style={{ marginBottom: 12 }} wrap>
        <Input.Search
          placeholder="Поиск инструмента..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ width: 260 }}
          allowClear
        />
        <Select value={category} onChange={setCategory} style={{ width: 220 }}>
          {categories.map(c => (
            <Option key={c} value={c}>{c === 'all' ? 'Все категории' : c.replace('_',' ').toUpperCase()}</Option>
          ))}
        </Select>
      </Space>

      {filtered.length === 0 && !loading && (
        <Empty description="Инструменты не найдены" />
      )}

      <Row gutter={[12, 12]}>
        {filtered.map(tool => (
          <Col key={tool.name} xs={24} sm={12} md={8} lg={6}>
            <Card size="small" title={tool.name.replace(/_/g, ' ')} actions={[
              <Tooltip key="run" title="Быстрый запуск">
                <Button 
                  type="primary" 
                  icon={<PlayCircleOutlined />} 
                  onClick={() => execute(tool.name)}
                  loading={executing === tool.name}
                >
                  Запустить
                </Button>
              </Tooltip>
            ]}>
              <Space direction="vertical" size={6} style={{ width: '100%' }}>
                <div style={{ minHeight: 36, color: '#555' }}>{tool.description}</div>
                <Space>
                  <Tag color="blue">{tool.category}</Tag>
                  <Badge status={tool.available ? 'success' : 'error'} text={tool.available ? 'Доступен' : 'Недоступен'} />
                </Space>
              </Space>
            </Card>
          </Col>
        ))}
      </Row>
    </Card>
  );
};

export default ToolsCatalogWidget;
