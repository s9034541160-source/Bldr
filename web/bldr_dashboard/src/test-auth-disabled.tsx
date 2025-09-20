// test-auth-disabled.tsx - Test component to verify authentication is disabled
import React, { useEffect, useState } from 'react';
import { apiService } from './services/api';
import { useStore } from './store';

const TestAuthDisabled: React.FC = () => {
  const [testResult, setTestResult] = useState<string>('');
  const [isTesting, setIsTesting] = useState<boolean>(false);
  const { user, setUser } = useStore();

  const testAuthStatus = async () => {
    setIsTesting(true);
    try {
      // Test health endpoint
      const health = await apiService.getHealth();
      console.log('Health response:', health);
      
      // Test tools list endpoint
      const tools = await apiService.discoverTools();
      console.log('Tools response:', tools);
      
      setTestResult('✅ Authentication appears to be disabled - endpoints accessible without token');
      
      // Set mock user if not already set
      if (!user) {
        setUser({
          token: "disabled_auth_token",
          role: "user",
          username: "anonymous"
        });
      }
    } catch (error) {
      console.error('Test failed:', error);
      setTestResult('❌ Authentication may still be enabled - endpoints require token');
    } finally {
      setIsTesting(false);
    }
  };

  return (
    <div style={{ padding: '20px', background: '#f0f0f0', borderRadius: '8px' }}>
      <h3>Authentication Status Test</h3>
      <button onClick={testAuthStatus} disabled={isTesting}>
        {isTesting ? 'Testing...' : 'Test Authentication Status'}
      </button>
      {testResult && (
        <div style={{ marginTop: '10px', padding: '10px', background: 'white', borderRadius: '4px' }}>
          <p>{testResult}</p>
        </div>
      )}
      {user && (
        <div style={{ marginTop: '10px', padding: '10px', background: 'white', borderRadius: '4px' }}>
          <p>Current user: {user.username} ({user.role})</p>
        </div>
      )}
    </div>
  );
};

export default TestAuthDisabled;