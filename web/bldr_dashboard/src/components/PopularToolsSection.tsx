import React from 'react';
import { Card, Row, Col, Space, Typography, Tag } from 'antd';
import { StarFilled, FireOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

interface PopularToolsSectionProps {
  popularTools: any[];
  renderToolCard: (tool: any) => React.ReactNode;
}

const PopularToolsSection: React.FC<PopularToolsSectionProps> = ({
  popularTools,
  renderToolCard
}) => {
  if (popularTools.length === 0) return null;

  return (
    <div style={{ marginBottom: 32 }}>
      {/* Заголовок популярных инструментов */}
      <div style={{ 
        marginBottom: 20,
        padding: '16px 20px',
        background: 'linear-gradient(135deg, #fa8c1615 0%, #fa8c1605 100%)',
        borderRadius: '12px',
        border: '1px solid #fa8c1630'
      }}>
        <Space size="large" style={{ width: '100%', justifyContent: 'space-between' }}>
          <Space size="middle">
            <FireOutlined style={{ fontSize: '24px', color: '#fa8c16' }} />
            <div>
              <Title level={3} style={{ 
                margin: 0, 
                color: '#fa8c16',
                fontSize: '20px',
                fontWeight: 600
              }}>
                Популярные инструменты
              </Title>
              <Text style={{ 
                color: '#8c8c8c',
                fontSize: '14px'
              }}>
                Часто используемые инструменты
              </Text>
            </div>
          </Space>
          <Tag color="orange" style={{ fontSize: '12px', fontWeight: 600 }}>
            {popularTools.length} инструментов
          </Tag>
        </Space>
      </div>

      {/* Популярные инструменты */}
      <Row gutter={[16, 16]}>
        {popularTools.map(tool => (
          <Col key={tool.name} xs={24} sm={12} md={8} lg={6}>
            <div style={{ position: 'relative' }}>
              {renderToolCard(tool)}
              {/* Индикатор популярности */}
              <div style={{
                position: 'absolute',
                top: '8px',
                right: '8px',
                zIndex: 10
              }}>
                <StarFilled style={{ 
                  color: '#fa8c16',
                  fontSize: '16px',
                  filter: 'drop-shadow(0 1px 2px rgba(0,0,0,0.3))'
                }} />
              </div>
            </div>
          </Col>
        ))}
      </Row>
    </div>
  );
};

export default PopularToolsSection;
