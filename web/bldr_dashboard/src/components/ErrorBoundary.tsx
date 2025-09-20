/**
 * Error Boundary Component
 * Компонент для перехвата ошибок React
 */

import React from 'react';
import { Alert, Button, Card } from 'antd';

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
}

class ErrorBoundary extends React.Component<
  React.PropsWithChildren<{}>,
  ErrorBoundaryState
> {
  constructor(props: React.PropsWithChildren<{}>) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({ error, errorInfo });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '24px' }}>
          <Card title="🚨 Application Error">
            <Alert
              message="Something went wrong"
              description="The application encountered an error and couldn't render properly."
              type="error"
              showIcon
              style={{ marginBottom: 16 }}
            />
            
            {this.state.error && (
              <Alert
                message="Error Details"
                description={
                  <div>
                    <p><strong>Error:</strong> {this.state.error.message}</p>
                    <details>
                      <summary>Stack Trace</summary>
                      <pre style={{ fontSize: '12px', overflow: 'auto' }}>
                        {this.state.error.stack}
                      </pre>
                    </details>
                  </div>
                }
                type="warning"
                style={{ marginBottom: 16 }}
              />
            )}
            
            <Button 
              type="primary" 
              onClick={() => window.location.reload()}
            >
              Reload Page
            </Button>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;