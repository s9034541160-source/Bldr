/**
 * Simple Test Component
 * Простой тестовый компонент для проверки работы фронтенда
 */

import React from 'react';
import { Card, Alert, Button, Space } from 'antd';

const SimpleTest: React.FC = () => {
  const [count, setCount] = React.useState(0);

  return (
    <div style={{ padding: '24px' }}>
      <Card title="✅ Frontend Test Component">
        <Space direction="vertical" style={{ width: '100%' }}>
          <Alert
            message="Frontend is Working!"
            description="If you can see this component, the React frontend is loading and rendering correctly."
            type="success"
            showIcon
          />
          
          <div>
            <p>Counter test: {count}</p>
            <Button onClick={() => setCount(count + 1)}>
              Increment Counter
            </Button>
          </div>
          
          <Alert
            message="Next Steps"
            description={
              <ul>
                <li>Check the browser console (F12) for any JavaScript errors</li>
                <li>Verify that the backend API is running on port 8000</li>
                <li>Make sure all dependencies are installed (npm install)</li>
                <li>Try the Diagnostic panel for more detailed information</li>
              </ul>
            }
            type="info"
          />
        </Space>
      </Card>
    </div>
  );
};

export default SimpleTest;