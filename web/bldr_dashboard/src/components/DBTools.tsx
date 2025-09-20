import React, { useState } from 'react';
import { Card, Input, Button, Table, message, Row, Col, Select, Typography } from 'antd';
import { apiService, type CypherResponse } from '../services/api';
import type { ColumnsType } from 'antd/es/table';

const { TextArea } = Input;
const { Title, Text } = Typography;
const { Option } = Select;

const DBTools: React.FC = () => {
  const [cypherQuery, setCypherQuery] = useState('MATCH (n) RETURN n LIMIT 10');
  const [results, setResults] = useState<any[]>([]);
  const [columns, setColumns] = useState<ColumnsType<any>>([]);
  const [loading, setLoading] = useState(false);

  // Predefined queries for common database operations
  const predefinedQueries = [
    {
      label: "Показать все узлы (первые 10)",
      query: "MATCH (n) RETURN n LIMIT 10"
    },
    {
      label: "Показать все связи (первые 10)",
      query: "MATCH ()-[r]->() RETURN r LIMIT 10"
    },
    {
      label: "Показать структуру базы данных",
      query: "CALL db.schema.visualization()"
    },
    {
      label: "Показать все метки узлов",
      query: "CALL db.labels() YIELD label RETURN label"
    },
    {
      label: "Показать все типы связей",
      query: "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType"
    },
    {
      label: "Показать количество узлов по меткам",
      query: "MATCH (n) RETURN labels(n) as label, count(*) as count"
    },
    {
      label: "Показать проекты",
      query: "MATCH (p:Project) RETURN p.name, p.code, p.status, p.files_count LIMIT 10"
    },
    {
      label: "Показать документы",
      query: "MATCH (d:Document) RETURN d.name, d.category, d.source LIMIT 10"
    }
  ];

  const executeQuery = async () => {
    if (!cypherQuery.trim()) {
      message.warning('Пожалуйста, введите Cypher запрос');
      return;
    }
    
    try {
      setLoading(true);
      const response = await apiService.executeCypher({ cypher: cypherQuery });
      
      if (response && response.records && response.records.length > 0) {
        // Создаем колонки на основе ключей первого результата
        const keys = Object.keys(response.records[0]);
        const newColumns = keys.map(key => ({
          title: key,
          dataIndex: key,
          key: key,
          ellipsis: true,
          render: (text: any) => {
            // Format JSON objects for better readability
            if (typeof text === 'object' && text !== null) {
              return JSON.stringify(text, null, 2);
            }
            return text;
          }
        }));
        
        setColumns(newColumns);
        setResults(response.records);
        message.success(`Запрос выполнен успешно. Найдено ${response.records.length} записей.`);
      } else {
        setResults([]);
        setColumns([]);
        message.info('Запрос выполнен, но результаты отсутствуют.');
      }
    } catch (error: any) {
      console.error('Ошибка выполнения запроса:', error);
      message.error(`Не удалось выполнить Cypher запрос: ${error.response?.data?.error || error.message}`);
      setResults([]);
      setColumns([]);
    } finally {
      setLoading(false);
    }
  };

  const handlePredefinedQuery = (query: string) => {
    setCypherQuery(query);
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card title="Инструменты базы данных" bordered={false}>
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <Card title="Предопределенные запросы" size="small">
              <Text type="secondary">
                Выберите один из готовых запросов для быстрого анализа базы данных:
              </Text>
              <div style={{ marginTop: 12 }}>
                <Select
                  style={{ width: '100%' }}
                  placeholder="Выберите предопределенный запрос"
                  onSelect={handlePredefinedQuery}
                >
                  {predefinedQueries.map((item, index) => (
                    <Option key={index} value={item.query}>
                      {item.label}
                    </Option>
                  ))}
                </Select>
              </div>
            </Card>
          </Col>
          
          <Col span={24}>
            <Card title="Cypher запрос" size="small">
              <TextArea
                value={cypherQuery}
                onChange={(e) => setCypherQuery(e.target.value)}
                placeholder="Введите Cypher запрос..."
                autoSize={{ minRows: 4, maxRows: 8 }}
                disabled={loading}
              />
              <Button 
                type="primary" 
                onClick={executeQuery} 
                loading={loading}
                style={{ marginTop: 16 }}
              >
                Выполнить запрос
              </Button>
            </Card>
          </Col>
          
          <Col span={24}>
            <Card title="Результаты" size="small">
              {results && results.length > 0 ? (
                <Table
                  dataSource={results}
                  columns={columns}
                  pagination={{ pageSize: 10 }}
                  scroll={{ x: true }}
                  rowKey={(record, index) => index?.toString() || '0'}
                />
              ) : (
                <div>
                  <p>Результаты запроса будут отображаться здесь</p>
                  <Text type="secondary">
                    Подсказка: Используйте предопределенные запросы выше или введите свой собственный Cypher запрос.
                    Например: <Text code>MATCH (p:Project) RETURN p.name, p.status</Text>
                  </Text>
                </div>
              )}
            </Card>
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default DBTools;