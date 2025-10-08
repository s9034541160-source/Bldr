import React from 'react';
import { Card, Row, Col, Badge, Space, Typography } from 'antd';
import { CategorizedTools } from '../utils/toolCategorization';

const { Title, Text } = Typography;

interface ToolCategorySectionProps {
  categorizedTools: CategorizedTools;
  renderToolCard: (tool: any) => React.ReactNode;
}

const ToolCategorySection: React.FC<ToolCategorySectionProps> = ({
  categorizedTools,
  renderToolCard
}) => {
  const { category, tools, count } = categorizedTools;

  if (count === 0) return null;

  return (
    <div style={{ marginBottom: 32 }}>
      {/* Заголовок категории */}
      <div style={{ 
        marginBottom: 20,
        padding: '16px 20px',
        background: `linear-gradient(135deg, ${category.color}15 0%, ${category.color}05 100%)`,
        borderRadius: '12px',
        border: `1px solid ${category.color}30`
      }}>
        <Space size="large" style={{ width: '100%', justifyContent: 'space-between' }}>
          <Space size="middle">
            <span style={{ fontSize: '24px' }}>{category.icon}</span>
            <div>
              <Title level={3} style={{ 
                margin: 0, 
                color: category.color,
                fontSize: '20px',
                fontWeight: 600
              }}>
                {category.title}
              </Title>
              <Text style={{ 
                color: '#8c8c8c',
                fontSize: '14px'
              }}>
                {category.description}
              </Text>
            </div>
          </Space>
          <Badge 
            count={count} 
            style={{ 
              backgroundColor: category.color,
              fontSize: '12px',
              fontWeight: 600
            }}
          />
        </Space>
      </div>

      {/* Инструменты категории */}
      <Row gutter={[16, 16]}>
        {tools.map(tool => (
          <Col key={tool.name} xs={24} sm={12} md={8} lg={6}>
            {renderToolCard(tool)}
          </Col>
        ))}
      </Row>
    </div>
  );
};

export default ToolCategorySection;
