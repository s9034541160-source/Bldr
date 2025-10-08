import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Input,
  Button,
  Table,
  Spin,
  Alert,
  Typography,
  Space,
  Select,
  Tag,
  Tooltip,
  Divider,
  Row,
  Col,
  Statistic,
  message,
  Drawer,
  List,
  Badge,
  Progress,
  Empty
} from 'antd';
import {
  SearchOutlined,
  ReloadOutlined,
  LinkOutlined,
  NodeExpandOutlined,
  NodeCollapseOutlined,
  InfoCircleOutlined,
  BookOutlined,
  FileTextOutlined,
  DatabaseOutlined
} from '@ant-design/icons';
import { apiService } from '../services/api';

const { Title, Text } = Typography;
const { Option } = Select;

interface NTDNode {
  canonical_id: string;
  document_type: string;
  full_text: string;
  context: string;
  confidence: number;
  reference_count?: number;
}

interface NTDReference {
  canonical_id: string;
  document_type: string;
  confidence: number;
  context: string;
  position: number;
}

interface NTDStatistics {
  total_ntd_nodes: number;
  total_documents: number;
  total_relationships: number;
  by_type: Record<string, number>;
  high_confidence_count: number;
  average_confidence: number;
}

interface NTDNetwork {
  nodes: NTDNode[];
  relationships: Array<{
    source: string;
    target: string;
    relationship_type: string;
    created_at: string;
  }>;
}

const NTDNavigator: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [statistics, setStatistics] = useState<NTDStatistics | null>(null);
  const [searchResults, setSearchResults] = useState<NTDNode[]>([]);
  const [networkData, setNetworkData] = useState<NTDNetwork | null>(null);
  const [selectedNTD, setSelectedNTD] = useState<NTDNode | null>(null);
  const [documentReferences, setDocumentReferences] = useState<NTDReference[]>([]);
  const [referencingDocuments, setReferencingDocuments] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<string>('');
  const [minConfidence, setMinConfidence] = useState(0.0);
  const [networkDrawerVisible, setNetworkDrawerVisible] = useState(false);
  const [detailsDrawerVisible, setDetailsDrawerVisible] = useState(false);
  const [registryData, setRegistryData] = useState<any>(null);
  const [exportLoading, setExportLoading] = useState(false);

  // Загружаем статистику при монтировании
  useEffect(() => {
    loadStatistics();
  }, []);

  const loadStatistics = async () => {
    try {
      setLoading(true);
      const stats = await apiService.get('/api/ntd/statistics');
      setStatistics(stats);
    } catch (error) {
      console.error('Error loading NTD statistics:', error);
      
      // !!! ЧЕСТНАЯ ОШИБКА: НЕ ПОКАЗЫВАЕМ ФЕЙКОВЫЕ ДАННЫЕ !!!
      setStatistics(null);
      
      message.error('Ошибка загрузки статистики НТД. Проверьте подключение к Neo4j и наличие данных.');
    } finally {
      setLoading(false);
    }
  };

  const loadRegistryView = async () => {
    try {
      setLoading(true);
      const registry = await apiService.get('/api/ntd/registry/view?limit=500');
      setRegistryData(registry);
      setNetworkDrawerVisible(true);
    } catch (error) {
      console.error('Error loading NTD registry view:', error);
      message.error('Ошибка загрузки реестра НТД');
    } finally {
      setLoading(false);
    }
  };

  const exportRegistry = async (format: 'json' | 'csv') => {
    try {
      setExportLoading(true);
      const response = await apiService.post(`/api/ntd/registry/export?format=${format}&output_file=ntd_registry_export`);
      
      if (response.status === 'success') {
        if (format === 'json') {
          message.success(`Реестр НТД экспортирован в JSON: ${response.file}`);
        } else {
          message.success(`Реестр НТД экспортирован в CSV: ${response.files?.join(', ')}`);
        }
      } else {
        message.error(`Ошибка экспорта: ${response.message}`);
      }
    } catch (error) {
      console.error('Error exporting NTD registry:', error);
      message.error('Ошибка экспорта реестра НТД');
    } finally {
      setExportLoading(false);
    }
  };

  const searchNTD = async () => {
    if (!searchQuery.trim()) return;

    try {
      setLoading(true);
      const params = new URLSearchParams({
        query: searchQuery,
        ...(selectedType && { doc_type: selectedType }),
        min_confidence: minConfidence.toString(),
        limit: '50'
      });

      const results = await apiService.get(`/api/ntd/search?${params}`);
      setSearchResults(results);
    } catch (error) {
      console.error('Error searching NTD:', error);
      message.error('Ошибка поиска НТД');
    } finally {
      setLoading(false);
    }
  };

  const loadNetwork = async (canonicalId?: string) => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        depth: '2',
        limit: '100'
      });

      if (canonicalId) {
        params.append('canonical_id', canonicalId);
      }

      const network = await apiService.get(`/api/ntd/network?${params}`);
      setNetworkData(network);
      setNetworkDrawerVisible(true);
    } catch (error) {
      console.error('Error loading NTD network:', error);
      message.error('Ошибка загрузки сети НТД');
    } finally {
      setLoading(false);
    }
  };

  const loadNTDDetails = async (ntd: NTDNode) => {
    try {
      setLoading(true);
      setSelectedNTD(ntd);

      // Загружаем документы, которые ссылаются на этот НТД
      const referencingDocs = await apiService.get(`/api/ntd/ntd/${ntd.canonical_id}/documents`);
      setReferencingDocuments(referencingDocs);

      setDetailsDrawerVisible(true);
    } catch (error) {
      console.error('Error loading NTD details:', error);
      message.error('Ошибка загрузки деталей НТД');
    } finally {
      setLoading(false);
    }
  };

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      'SP': 'blue',
      'SNiP': 'green',
      'GOST': 'orange',
      'GESN': 'purple',
      'FER': 'cyan',
      'TER': 'magenta',
      'PP': 'red',
      'PRIKAZ': 'volcano',
      'FZ': 'gold'
    };
    return colors[type] || 'default';
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'success';
    if (confidence >= 0.6) return 'warning';
    return 'error';
  };

  const columns = [
    {
      title: 'НТД',
      dataIndex: 'canonical_id',
      key: 'canonical_id',
      render: (text: string, record: NTDNode) => (
        <Space direction="vertical" size="small">
          <Text strong>{text}</Text>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {record.full_text}
          </Text>
        </Space>
      ),
    },
    {
      title: 'Тип',
      dataIndex: 'document_type',
      key: 'document_type',
      render: (type: string) => (
        <Tag color={getTypeColor(type)}>{type}</Tag>
      ),
    },
    {
      title: 'Уверенность',
      dataIndex: 'confidence',
      key: 'confidence',
      render: (confidence: number) => (
        <Progress
          percent={Math.round(confidence * 100)}
          size="small"
          status={getConfidenceColor(confidence)}
          format={(percent) => `${percent}%`}
        />
      ),
    },
    {
      title: 'Ссылок',
      dataIndex: 'reference_count',
      key: 'reference_count',
      render: (count: number) => (
        <Badge count={count || 0} showZero color="blue" />
      ),
    },
    {
      title: 'Действия',
      key: 'actions',
      render: (text: any, record: NTDNode) => (
        <Space>
          <Button
            type="link"
            icon={<InfoCircleOutlined />}
            onClick={() => loadNTDDetails(record)}
          >
            Детали
          </Button>
          <Button
            type="link"
            icon={<NodeExpandOutlined />}
            onClick={() => loadNetwork(record.canonical_id)}
          >
            Сеть
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>
        <DatabaseOutlined /> Навигатор НТД
      </Title>

      {/* Статистика */}
      {statistics ? (
        <Row gutter={16} style={{ marginBottom: '24px' }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="Всего НТД"
                value={statistics.total_ntd_nodes}
                prefix={<BookOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Документов"
                value={statistics.total_documents}
                prefix={<FileTextOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Связей"
                value={statistics.total_relationships}
                prefix={<LinkOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Средняя уверенность"
                value={statistics.average_confidence}
                precision={2}
                suffix="%"
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
        </Row>
      ) : (
        <Alert
          message="Статистика НТД недоступна"
          description="Не удалось загрузить статистику НТД. Проверьте подключение к Neo4j и наличие данных в базе."
          type="error"
          showIcon
          style={{ marginBottom: '24px' }}
          action={
            <Button size="small" onClick={loadStatistics}>
              Повторить попытку
            </Button>
          }
        />
      )}

      {/* Поиск */}
      <Card title="Поиск НТД" style={{ marginBottom: '24px' }}>
        <Space.Compact style={{ width: '100%' }}>
          <Input
            placeholder="Введите запрос для поиска НТД..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onPressEnter={searchNTD}
            prefix={<SearchOutlined />}
          />
          <Select
            placeholder="Тип документа"
            value={selectedType}
            onChange={setSelectedType}
            style={{ width: '150px' }}
            allowClear
          >
            <Option value="SP">СП</Option>
            <Option value="SNiP">СНиП</Option>
            <Option value="GOST">ГОСТ</Option>
            <Option value="GESN">ГЭСН</Option>
            <Option value="FER">ФЕР</Option>
            <Option value="TER">ТЕР</Option>
            <Option value="PP">ПП</Option>
            <Option value="PRIKAZ">Приказ</Option>
            <Option value="FZ">ФЗ</Option>
          </Select>
          <Select
            placeholder="Мин. уверенность"
            value={minConfidence}
            onChange={setMinConfidence}
            style={{ width: '150px' }}
          >
            <Option value={0.0}>Любая</Option>
            <Option value={0.5}>50%</Option>
            <Option value={0.7}>70%</Option>
            <Option value={0.8}>80%</Option>
            <Option value={0.9}>90%</Option>
          </Select>
          <Button type="primary" onClick={searchNTD} loading={loading}>
            Поиск
          </Button>
          <Button icon={<ReloadOutlined />} onClick={loadStatistics}>
            Обновить
          </Button>
          <Button 
            icon={<NodeExpandOutlined />} 
            onClick={loadRegistryView}
            loading={loading}
          >
            Просмотр реестра
          </Button>
          <Button 
            icon={<DatabaseOutlined />} 
            onClick={() => exportRegistry('json')}
            loading={exportLoading}
          >
            Экспорт JSON
          </Button>
          <Button 
            icon={<DatabaseOutlined />} 
            onClick={() => exportRegistry('csv')}
            loading={exportLoading}
          >
            Экспорт CSV
          </Button>
        </Space.Compact>
      </Card>

      {/* Результаты поиска */}
      {searchResults.length > 0 && (
        <Card title={`Результаты поиска (${searchResults.length})`}>
          <Table
            columns={columns}
            dataSource={searchResults}
            rowKey="canonical_id"
            pagination={{ pageSize: 10 }}
            loading={loading}
          />
        </Card>
      )}

      {/* Сеть НТД / Реестр */}
      <Drawer
        title={registryData ? "Реестр НТД" : "Сеть связей НТД"}
        width={1000}
        open={networkDrawerVisible}
        onClose={() => {
          setNetworkDrawerVisible(false);
          setRegistryData(null);
        }}
      >
        {registryData ? (
          <div>
            {/* Метаданные реестра */}
            <Card title="Метаданные реестра" style={{ marginBottom: '16px' }}>
              <Row gutter={16}>
                <Col span={6}>
                  <Statistic title="Всего узлов" value={registryData.metadata?.node_count || 0} />
                </Col>
                <Col span={6}>
                  <Statistic title="Всего связей" value={registryData.metadata?.edge_count || 0} />
                </Col>
                <Col span={6}>
                  <Statistic title="Типов НТД" value={registryData.metadata?.type_count || 0} />
                </Col>
                <Col span={6}>
                  <Statistic 
                    title="Средняя уверенность" 
                    value={Math.round((registryData.metadata?.avg_confidence || 0) * 100)} 
                    suffix="%" 
                  />
                </Col>
              </Row>
            </Card>

            {/* Узлы реестра */}
            <Card title={`Узлы НТД (${registryData.nodes?.length || 0})`} style={{ marginBottom: '16px' }}>
              <List
                dataSource={registryData.nodes || []}
                pagination={{ pageSize: 10 }}
                renderItem={(node) => (
                  <List.Item>
                    <List.Item.Meta
                      title={node.id}
                      description={
                        <Space direction="vertical" size="small">
                          <Space>
                            <Tag color={getTypeColor(node.type)}>{node.type}</Tag>
                            <Text type="secondary">Уверенность: {Math.round(node.confidence * 100)}%</Text>
                            <Badge count={node.reference_count || 0} showZero color="blue" />
                          </Space>
                          <Text type="secondary">{node.title}</Text>
                        </Space>
                      }
                    />
                  </List.Item>
                )}
              />
            </Card>

            {/* Связи реестра */}
            <Card title={`Связи НТД (${registryData.edges?.length || 0})`}>
              <List
                dataSource={registryData.edges || []}
                pagination={{ pageSize: 10 }}
                renderItem={(edge) => (
                  <List.Item>
                    <Space>
                      <Text strong>{edge.source}</Text>
                      <Text>→</Text>
                      <Text strong>{edge.target}</Text>
                      <Tag color="blue">{edge.relationship_type}</Tag>
                      <Text type="secondary">
                        Уверенность: {Math.round(edge.confidence * 100)}%
                      </Text>
                    </Space>
                  </List.Item>
                )}
              />
            </Card>
          </div>
        ) : networkData ? (
          <div>
            <Title level={4}>Узлы сети ({networkData.nodes.length})</Title>
            <List
              dataSource={networkData.nodes}
              renderItem={(node) => (
                <List.Item>
                  <List.Item.Meta
                    title={node.canonical_id}
                    description={
                      <Space>
                        <Tag color={getTypeColor(node.document_type)}>
                          {node.document_type}
                        </Tag>
                        <Text type="secondary">
                          Уверенность: {Math.round(node.confidence * 100)}%
                        </Text>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
            
            <Divider />
            
            <Title level={4}>Связи ({networkData.relationships.length})</Title>
            <List
              dataSource={networkData.relationships}
              renderItem={(rel) => (
                <List.Item>
                  <Text>
                    <Text strong>{rel.source}</Text> → <Text strong>{rel.target}</Text>
                    <Tag style={{ marginLeft: 8 }}>{rel.relationship_type}</Tag>
                  </Text>
                </List.Item>
              )}
            />
          </div>
        ) : null}
      </Drawer>

      {/* Детали НТД */}
      <Drawer
        title={`Детали НТД: ${selectedNTD?.canonical_id}`}
        width={800}
        open={detailsDrawerVisible}
        onClose={() => setDetailsDrawerVisible(false)}
      >
        {selectedNTD && (
          <div>
            <Card title="Информация о НТД" style={{ marginBottom: '16px' }}>
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <div>
                  <Text strong>Канонический ID:</Text> {selectedNTD.canonical_id}
                </div>
                <div>
                  <Text strong>Тип документа:</Text> 
                  <Tag color={getTypeColor(selectedNTD.document_type)} style={{ marginLeft: 8 }}>
                    {selectedNTD.document_type}
                  </Tag>
                </div>
                <div>
                  <Text strong>Полный текст:</Text> {selectedNTD.full_text}
                </div>
                <div>
                  <Text strong>Контекст:</Text> {selectedNTD.context}
                </div>
                <div>
                  <Text strong>Уверенность:</Text> 
                  <Progress 
                    percent={Math.round(selectedNTD.confidence * 100)} 
                    size="small" 
                    style={{ marginLeft: 8, width: '200px' }}
                  />
                </div>
              </Space>
            </Card>

            <Card title="Документы, ссылающиеся на этот НТД">
              <List
                dataSource={referencingDocuments}
                renderItem={(doc) => (
                  <List.Item>
                    <List.Item.Meta
                      title={doc.title}
                      description={
                        <Space direction="vertical" size="small">
                          <Text type="secondary">ID: {doc.doc_id}</Text>
                          <Text type="secondary">Контекст: {doc.context}</Text>
                          <Text type="secondary">
                            Уверенность: {Math.round(doc.confidence * 100)}%
                          </Text>
                        </Space>
                      }
                    />
                  </List.Item>
                )}
              />
            </Card>
          </div>
        )}
      </Drawer>

      {!loading && searchResults.length === 0 && searchQuery && (
        <Empty description="НТД не найдены" />
      )}
    </div>
  );
};

export default NTDNavigator;