# Frontend Integration Guide: Custom Training

## 📋 Overview

Полная инструкция по интеграции пользовательского обучения RAG системы с фронтендом.

## 🔄 Frontend Workflow

### Step 1: Directory Selection
```typescript
// Frontend: Directory picker component
interface DirectoryInfo {
  valid: boolean;
  directory?: string;
  total_files?: number;
  total_size_mb?: number;
  file_types?: Record<string, number>;
  sample_files?: FileInfo[];
  estimated_training_time?: string;
  error?: string;
}

// Local directory validation (client-side)
function validateDirectory(path: string): DirectoryInfo {
  // Client-side validation before API call
  // Check if path exists, count files, etc.
}
```

### Step 2: API Training Request
```typescript
// POST /train endpoint
interface TrainingRequest {
  custom_dir: string;
}

interface TrainingResponse {
  status: string;
  message: string;
  custom_dir: string;
}

const startTraining = async (directory: string) => {
  const response = await fetch('/api/train', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_TOKEN}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ custom_dir: directory })
  });
  
  return await response.json();
};
```

### Step 3: Progress Monitoring

#### REST API Polling
```typescript
// GET /api/training/status endpoint
interface TrainingStatus {
  status: 'success' | 'error' | 'processing';
  is_training: boolean;
  progress: number;
  current_stage: string;
  message: string;
}

const checkTrainingStatus = async (): Promise<TrainingStatus> => {
  const response = await fetch('/api/training/status', {
    headers: { 'Authorization': `Bearer ${API_TOKEN}` }
  });
  return await response.json();
};

// Poll every 15-30 seconds
const pollTrainingStatus = () => {
  const interval = setInterval(async () => {
    const status = await checkTrainingStatus();
    updateUI(status);
    
    if (!status.is_training) {
      clearInterval(interval);
    }
  }, 15000);
};
```

#### WebSocket Real-time Updates
```typescript
// WebSocket connection for real-time updates
const connectWebSocket = () => {
  const ws = new WebSocket(`ws://localhost:8000/ws?token=${API_TOKEN}`);
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'training_update') {
      updateProgressBar(data.progress);
      updateStatusText(data.message);
      updateCurrentStage(data.stage);
    }
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    // Fallback to REST polling
    pollTrainingStatus();
  };
  
  return ws;
};
```

## 🎨 Frontend Components

### Directory Picker Component
```typescript
interface DirectoryPickerProps {
  onDirectorySelected: (directory: string) => void;
}

const DirectoryPicker: React.FC<DirectoryPickerProps> = ({ onDirectorySelected }) => {
  const [selectedDir, setSelectedDir] = useState<string>('');
  const [dirInfo, setDirInfo] = useState<DirectoryInfo | null>(null);
  
  const handleDirectoryChange = async (path: string) => {
    setSelectedDir(path);
    const info = await validateDirectory(path);
    setDirInfo(info);
  };
  
  return (
    <div className="directory-picker">
      <input 
        type="text" 
        value={selectedDir}
        onChange={(e) => handleDirectoryChange(e.target.value)}
        placeholder="I:\docs\downloaded"
      />
      
      {dirInfo && dirInfo.valid && (
        <div className="directory-preview">
          <h3>📋 Preview</h3>
          <p>📄 Files: {dirInfo.total_files}</p>
          <p>💾 Size: {dirInfo.total_size_mb} MB</p>
          <p>⏱️ Estimated time: {dirInfo.estimated_training_time}</p>
          
          <button onClick={() => onDirectorySelected(selectedDir)}>
            🚀 Start Training
          </button>
        </div>
      )}
    </div>
  );
};
```

### Training Progress Component
```typescript
interface TrainingProgressProps {
  directory: string;
  onComplete: () => void;
}

const TrainingProgress: React.FC<TrainingProgressProps> = ({ directory, onComplete }) => {
  const [status, setStatus] = useState<TrainingStatus | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);
  
  useEffect(() => {
    // Start training
    startTraining(directory);
    
    // Connect WebSocket
    const websocket = connectWebSocket();
    setWs(websocket);
    
    // Cleanup on unmount
    return () => {
      websocket?.close();
    };
  }, [directory]);
  
  return (
    <div className="training-progress">
      <h2>🚀 Training in Progress</h2>
      <div className="progress-bar">
        <div 
          className="progress-fill" 
          style={{ width: `${status?.progress || 0}%` }}
        />
      </div>
      
      <p>📁 Directory: {directory}</p>
      <p>📈 Progress: {status?.progress || 0}%</p>
      <p>🔄 Stage: {status?.current_stage || 'Starting'}</p>
      <p>💬 Status: {status?.message || 'Initializing...'}</p>
      
      {status && !status.is_training && (
        <div className="training-complete">
          <h3>✅ Training Complete!</h3>
          <button onClick={onComplete}>
            🔍 Test Queries
          </button>
        </div>
      )}
    </div>
  );
};
```

### Query Testing Component
```typescript
const QueryTester: React.FC = () => {
  const [query, setQuery] = useState<string>('');
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  
  const testQuery = async () => {
    setLoading(true);
    
    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${API_TOKEN}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query, k: 5 })
      });
      
      const data = await response.json();
      setResults(data.results || []);
    } catch (error) {
      console.error('Query error:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="query-tester">
      <h2>🔍 Test Queries</h2>
      
      <div className="query-input">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter your query..."
        />
        <button onClick={testQuery} disabled={loading}>
          {loading ? '⏳' : '🔍'} Search
        </button>
      </div>
      
      <div className="query-results">
        {results.map((result, index) => (
          <div key={index} className="result-item">
            <div className="result-score">
              Score: {result.score.toFixed(3)}
            </div>
            <div className="result-content">
              {result.chunk}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
```

## 🔐 Authentication

```typescript
// API Token management
const API_TOKEN = process.env.REACT_APP_API_TOKEN;

// Add to all API requests
const apiRequest = async (endpoint: string, options: RequestInit = {}) => {
  const response = await fetch(`/api${endpoint}`, {
    ...options,
    headers: {
      'Authorization': `Bearer ${API_TOKEN}`,
      'Content-Type': 'application/json',
      ...options.headers
    }
  });
  
  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }
  
  return await response.json();
};
```

## 📊 Error Handling

```typescript
interface ApiError {
  status: number;
  message: string;
}

const handleApiError = (error: ApiError) => {
  switch (error.status) {
    case 401:
      // Redirect to login
      window.location.href = '/login';
      break;
    case 403:
      showNotification('Access denied', 'error');
      break;
    case 404:
      showNotification('Endpoint not found', 'error');
      break;
    case 500:
      showNotification('Server error. Please try again.', 'error');
      break;
    default:
      showNotification(`Error: ${error.message}`, 'error');
  }
};
```

## 🧪 Testing Scripts

Используйте созданные тестовые скрипты для проверки интеграции:

```bash
# E2E test
python test_e2e_custom_training.py

# Frontend workflow simulation
python test_frontend_training_integration.py
```

## 📋 API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/train` | POST | Start training on custom directory |
| `/api/training/status` | GET | Get training progress status |
| `/query` | POST | Query trained RAG system |
| `/health` | GET | API health check |
| `/metrics-json` | GET | System metrics for dashboard |
| `/ws` | WebSocket | Real-time updates |

## 💡 Best Practices

1. **Always validate directory** before starting training
2. **Use WebSocket + REST** for robust progress monitoring
3. **Handle authentication errors** gracefully
4. **Provide user feedback** during long-running operations
5. **Test queries immediately** after training completes
6. **Show estimated time** to set user expectations
7. **Implement retry logic** for failed API calls

## 🎯 Complete Frontend Flow

```typescript
const TrainingWorkflow: React.FC = () => {
  const [step, setStep] = useState<'select' | 'training' | 'testing'>('select');
  const [selectedDirectory, setSelectedDirectory] = useState<string>('');
  
  const handleDirectorySelected = (directory: string) => {
    setSelectedDirectory(directory);
    setStep('training');
  };
  
  const handleTrainingComplete = () => {
    setStep('testing');
  };
  
  return (
    <div className="training-workflow">
      {step === 'select' && (
        <DirectoryPicker onDirectorySelected={handleDirectorySelected} />
      )}
      
      {step === 'training' && (
        <TrainingProgress 
          directory={selectedDirectory}
          onComplete={handleTrainingComplete}
        />
      )}
      
      {step === 'testing' && (
        <QueryTester />
      )}
    </div>
  );
};
```

Этот гайд покрывает все аспекты интеграции процесса custom training с фронтендом! 🚀