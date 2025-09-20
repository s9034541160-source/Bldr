import React, { useState, useEffect, useMemo } from 'react';
import { 
  Table, 
  Button, 
  Input, 
  Select, 
  Tag, 
  Progress, 
  Space, 
  Modal, 
  Timeline,
  message,
  Alert,
  Spin,
  Tabs
} from 'antd';
import { 
  SyncOutlined, 
  CloseCircleOutlined, 
  RiseOutlined,
  ClockCircleOutlined,
  InfoCircleOutlined,
  DownloadOutlined
} from '@ant-design/icons';
import { useSocket } from '../hooks/useSocket';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiService, QueueTask } from '../services/api';
import { useStore } from '../store';

const { Option } = Select;
const { TabPane } = Tabs;

const Queue: React.FC = () => {
  const [statusFilter, setStatusFilter] = useState('');
  const [search, setSearch] = useState('');
  const [activeTab, setActiveTab] = useState<'active' | 'completed'>('active');
  const [showDetail, setShowDetail] = useState(false);
  const [selectedTask, setSelectedTask] = useState<QueueTask | null>(null);
  const [detailLogs, setDetailLogs] = useState<any[]>([]);
  const { user } = useStore();
  
  const { socket, connected } = useSocket();
  const queryClient = useQueryClient();
  
  // Fetch ACTIVE jobs
  const { 
    data: activeTasks, 
    error: activeError, 
    isLoading: isLoadingActive, 
    refetch: refetchActive 
  } = useQuery<QueueTask[], any>({
    queryKey: ['queue', 'active'],
    queryFn: async () => {
      const byTool = await apiService.getActiveJobs();
      const list: QueueTask[] = [] as any;
      Object.entries(byTool).forEach(([toolType, items]: [string, any]) => {
        (items as any[]).forEach((it: any) => {
          list.push({
            id: it.job_id || it.id,
            type: toolType,
            status: it.status,
            progress: it.progress ?? 0,
            owner: it.owner || 'system',
            started_at: it.created_at,
            eta: it.eta || null,
          } as QueueTask);
        });
      });
      return list;
    },
    refetchInterval: connected ? false : 10000,
    retry: (failureCount: number, error: any) => {
      if (error?.response?.status === 403 || error?.response?.status === 401) return false;
      return failureCount < 3;
    },
    staleTime: 5*60*1000,
    enabled: !!user?.token
  });

  // Fetch COMPLETED jobs (if backend exposes it). If 404, the query returns empty and WS will fill cache.
  const { 
    data: completedTasks, 
    error: completedError, 
    isLoading: isLoadingCompleted
  } = useQuery<QueueTask[], any>({
    queryKey: ['queue', 'completed'],
    queryFn: async () => {
      const byTool = await apiService.getCompletedJobs();
      const list: QueueTask[] = [] as any;
      Object.entries(byTool).forEach(([toolType, items]: [string, any]) => {
        (items as any[]).forEach((it: any) => {
          list.push({
            id: it.job_id || it.id,
            type: toolType,
            status: it.status || 'completed',
            progress: it.progress ?? 100,
            owner: it.owner || 'system',
            started_at: it.created_at,
            eta: it.eta || null,
          } as QueueTask);
        });
      });
      return list;
    },
    refetchInterval: false,
    retry: 0,
    staleTime: 60*1000,
    enabled: !!user?.token
  });
  
  // Listen for task updates via WebSocket
  useEffect(() => {
    if (socket) {
      const handleTaskUpdate = (data: any) => {
        queryClient.setQueryData<QueueTask[]>(['queue', 'active'], (old = []) => {
          return old.map(task => task.id === data.id ? { ...task, ...data } : task);
        });
        
        if (data.progress === 100 || data.status === 'completed') {
          message.success(`Задача ${data.id} завершена!`);
          // Active will be refreshed/patched from WS; push into completed cache as well
          queryClient.setQueryData<QueueTask[]>(['queue', 'completed'], (old = []) => {
            if (old.find(t => t.id === data.id)) return old;
            return [
              ...old,
              {
                id: data.id,
                type: data.type || 'unknown',
                status: 'completed',
                progress: 100,
                owner: data.owner || 'system',
                started_at: data.started_at || new Date().toISOString(),
                eta: null,
              } as QueueTask
            ];
          });
        }
      };
      
      socket.on('task_update', handleTaskUpdate);
      
      return () => {
        socket.off('task_update', handleTaskUpdate);
      };
    }
  }, [socket, queryClient]);
  
  const retryTask = async (id: string) => {
    try {
      // In a real implementation, you would call an API endpoint to retry the task
      message.success('Задача отправлена на повторную обработку');
      refetchActive();
    } catch (error) {
      message.error('Ошибка при повторной обработке задачи');
    }
  };
  
  const cancelTask = async (id: string) => {
    try {
      await apiService.cancelJob(id);
      message.success('Задача отменена');
      refetchActive();
    } catch (error) {
      message.error('Ошибка при отмене задачи');
    }
  };
  
  const priorityUp = async (id: string) => {
    try {
      // In a real implementation, you would call an API endpoint to increase priority
      message.success('Приоритет повышен');
    } catch (error) {
      message.error('Ошибка при изменении приоритета');
    }
  };

  const downloadResult = async (id: string) => {
    try {
      const blob = await apiService.downloadJobResult(id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `job_${id}.zip`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      message.error('Не удалось скачать результат');
    }
  };
  
  const viewLogs = (taskId: string) => {
    const pool = activeTab === 'active' ? activeTasks : completedTasks;
    const task = pool?.find(t => t.id === taskId);
    setSelectedTask(task || null);
    // In a real implementation, you would fetch actual logs for the task
    setDetailLogs([
      { id: 1, time: new Date().toLocaleTimeString(), log: `Задача ${taskId} начата` },
      { id: 2, time: new Date().toLocaleTimeString(), log: 'Этап 1: Загрузка данных завершена' },
      { id: 3, time: new Date().toLocaleTimeString(), log: 'Этап 2: Предобработка данных' }
    ]);
    setShowDetail(true);
  };

  const filterTasks = (items?: QueueTask[]) => {
    const q = search.trim().toLowerCase();
    return (items || []).filter(it => {
      if (statusFilter && it.status !== statusFilter) return false;
      if (!q) return true;
      return (
        it.id.toLowerCase().includes(q) ||
        (it.owner || '').toLowerCase().includes(q) ||
        (it.type || '').toLowerCase().includes(q)
      );
    });
  };

  const activeData = useMemo(() => filterTasks(activeTasks), [activeTasks, statusFilter, search]);
  const completedData = useMemo(() => filterTasks(completedTasks), [completedTasks, statusFilter, search]);

  const activeColumns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      render: (text: string) => <a onClick={() => viewLogs(text)}>{text.substring(0, 8)}...</a>
    },
    { title: 'Тип', dataIndex: 'type', key: 'type', render: (type: string) => type || 'Неизвестно' },
    {
      title: 'Статус',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={
          status === 'running' ? 'blue' : 
          status === 'failed' ? 'red' : 
          status === 'completed' ? 'green' : 
          'orange'
        }>
          {status === 'running' ? 'Выполняется' : 
           status === 'failed' ? 'Ошибка' : 
           status === 'completed' ? 'Завершено' : 
           'В очереди'}
        </Tag>
      )
    },
    { title: 'Прогресс', dataIndex: 'progress', key: 'progress', render: (p: number) => (<Progress percent={p || 0} size="small" status="active" />) },
    { title: 'Владелец', dataIndex: 'owner', key: 'owner', render: (o: string) => o || 'Система' },
    { title: 'Начато', dataIndex: 'started_at', key: 'started_at', render: (d: string) => d ? new Date(d).toLocaleString() : 'Неизвестно' },
    { title: 'ETA', dataIndex: 'eta', key: 'eta', render: (e: string) => e || 'Расчет...' },
    {
      title: 'Действия',
      key: 'actions',
      render: (_: any, record: QueueTask) => (
        <Space size="small">
          {record.status === 'failed' && (
            <Button size="small" onClick={() => retryTask(record.id)} icon={<SyncOutlined />}>Повторить</Button>
          )}
          <Button size="small" onClick={() => cancelTask(record.id)} danger icon={<CloseCircleOutlined />}>Отменить</Button>
          <Button size="small" onClick={() => priorityUp(record.id)} icon={<RiseOutlined />}>Приоритет</Button>
        </Space>
      )
    }
  ];

  const completedColumns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      render: (text: string) => <a onClick={() => viewLogs(text)}>{text.substring(0, 8)}...</a>
    },
    { title: 'Тип', dataIndex: 'type', key: 'type' },
    { title: 'Статус', dataIndex: 'status', key: 'status', render: () => (<Tag color="green">Завершено</Tag>) },
    { title: 'Прогресс', dataIndex: 'progress', key: 'progress', render: () => (<Progress percent={100} size="small" status="normal" />) },
    { title: 'Владелец', dataIndex: 'owner', key: 'owner' },
    { title: 'Начато', dataIndex: 'started_at', key: 'started_at', render: (d: string) => d ? new Date(d).toLocaleString() : '—' },
    {
      title: 'Действия',
      key: 'actions',
      render: (_: any, record: QueueTask) => (
        <Space size="small">
          <Button size="small" onClick={() => downloadResult(record.id)} icon={<DownloadOutlined />}>Скачать</Button>
        </Space>
      )
    }
  ];

  const isLoading = activeTab === 'active' ? isLoadingActive : isLoadingCompleted;
  const error = activeTab === 'active' ? activeError : completedError;
  const tasks = activeTab === 'active' ? activeData : completedData;

  // Show loading state
  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '20px' }}>
        <Spin tip="Загрузка очереди..." />
        {!connected && (
          <Alert message="WS отключен — poll every 10s" type="warning" style={{ marginTop: '10px' }} />
        )}
      </div>
    );
  }
  
  // Show error state
  if (error) {
    return (
      <div>
        <Alert 
          message="Очередь задач" 
          description="Компонент для отслеживания активных и завершенных задач"
          type="info"
          icon={<InfoCircleOutlined />}
          style={{ marginBottom: '16px' }}
        />
        <Alert 
          message={`Ошибка: ${error.message}`} 
          type="error"
        />
      </div>
    );
  }
  
  // Show login prompt if not authenticated
  if (!user?.token) {
    return (
      <div>
        <Alert 
          message="Очередь задач" 
          description="Компонент для отслеживания активных и завершенных задач"
          type="info"
          icon={<InfoCircleOutlined />}
          style={{ marginBottom: '16px' }}
        />
        <Alert 
          message="Требуется аутентификация" 
          description={<div><p>Для просмотра очереди задач необходимо войти в систему.</p><p>Нажмите кнопку \"Войти\" в правом верхнем углу экрана.</p></div>}
          type="warning" 
        />
      </div>
    );
  }

  return (
    <div>
      <Alert 
        message="Очередь задач" 
        description="Компонент для отслеживания активных и завершенных задач"
        type="info"
        icon={<InfoCircleOutlined />}
        style={{ marginBottom: '16px' }}
      />
      {!connected && (
        <Alert message="WS отключен — poll every 10s" type="warning" style={{ marginBottom: '16px' }} />
      )}

      <div style={{ marginBottom: 16, display: 'flex', gap: 16, alignItems: 'center' }}>
        <Input.Search 
          placeholder="Поиск по ID/владельцу/типу" 
          style={{ width: 260 }} 
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          allowClear
          data-cy="queue-search"
        />
        <Select 
          value={statusFilter} 
          onChange={setStatusFilter} 
          placeholder="Фильтр статуса" 
          style={{ width: 180 }}
        >
          <Option value="">Все</Option>
          <Option value="running">Выполняется</Option>
          <Option value="queued">В очереди</Option>
          <Option value="failed">Ошибка</Option>
          <Option value="completed">Завершено</Option>
        </Select>
      </div>

      <Tabs activeKey={activeTab} onChange={(k) => setActiveTab(k as 'active' | 'completed')}>
        <TabPane tab={`Active (${activeTasks?.length || 0})`} key="active">
          <Table 
            dataSource={activeData || []} 
            columns={activeColumns} 
            rowKey="id" 
            pagination={{ pageSize: 10 }} 
            size="small" 
            locale={{ emptyText: 'Очередь пуста — запустите задачу' }}
            data-cy="queue-table-active"
          />
        </TabPane>
        <TabPane tab={`Completed (${completedTasks?.length || 0})`} key="completed">
          <Table 
            dataSource={completedData || []} 
            columns={completedColumns} 
            rowKey="id" 
            pagination={{ pageSize: 10 }} 
            size="small" 
            locale={{ emptyText: 'Завершенных задач нет' }}
            data-cy="queue-table-completed"
          />
        </TabPane>
      </Tabs>
      
      <Modal
        open={showDetail}
        title={`Детали Задачи ${selectedTask?.id}`}
        onCancel={() => setShowDetail(false)}
        footer={null}
        width={600}
      >
        <Timeline>
          {detailLogs.map(log => (
            <Timeline.Item key={log.id} color="blue">
              {log.time}: {log.log}
            </Timeline.Item>
          ))}
        </Timeline>
        <Button onClick={() => viewLogs(selectedTask?.id || '')} style={{ marginTop: 16 }}>
          Обновить Логи
        </Button>
      </Modal>
    </div>
  );
};

export default Queue;

const Queue: React.FC = () => {
  const [statusFilter, setStatusFilter] = useState('');
  const [showDetail, setShowDetail] = useState(false);
  const [selectedTask, setSelectedTask] = useState<QueueTask | null>(null);
  const [detailLogs, setDetailLogs] = useState<any[]>([]);
  const { user } = useStore();
  
  const { socket, connected } = useSocket();
  const queryClient = useQueryClient();
  
  // Fetch queue data with TanStack Query and fallback polling
  const { 
    data: tasks, 
    error, 
    isLoading, 
    refetch 
  } = useQuery<QueueTask[], Error>({
    queryKey: ['queue'],
queryFn: async () => {
      const byTool = await apiService.getActiveJobs();
      const list: QueueTask[] = [] as any;
      Object.entries(byTool).forEach(([toolType, items]: [string, any]) => {
        (items as any[]).forEach((it: any) => {
          list.push({
            id: it.job_id || it.id,
            type: toolType,
            status: it.status,
            progress: it.progress ?? 0,
            owner: it.owner || 'system',
            started_at: it.created_at,
            eta: it.eta || null,
          } as QueueTask);
        });
      });
      return list;
    },
    refetchInterval: connected ? false : 10000, // Poll every 10s if not connected
    retry: (failureCount, error: any) => {
      // No retry on 403/401 errors
      if (error.response?.status === 403 || error.response?.status === 401) {
        return false;
      }
      return failureCount < 3;
    },
    staleTime: 5*60*1000,
    enabled: !!user?.token // Only fetch if user is authenticated
  });
  
  // Listen for task updates via WebSocket
  useEffect(() => {
    if (socket) {
      const handleTaskUpdate = (data: any) => {
        queryClient.setQueryData<QueueTask[]>(['queue'], (old = []) => {
          return old.map(task => task.id === data.id ? { ...task, ...data } : task);
        });
        
        if (data.progress === 100) {
          message.success(`Задача ${data.id} завершена!`);
        }
      };
      
      socket.on('task_update', handleTaskUpdate);
      
      return () => {
        socket.off('task_update', handleTaskUpdate);
      };
    }
  }, [socket, queryClient]);
  
  const retryTask = async (id: string) => {
    try {
      // In a real implementation, you would call an API endpoint to retry the task
      message.success('Задача отправлена на повторную обработку');
      refetch();
    } catch (error) {
      message.error('Ошибка при повторной обработке задачи');
    }
  };
  
  const cancelTask = async (id: string) => {
    try {
      await apiService.cancelJob(id);
      message.success('Задача отменена');
      refetch();
    } catch (error) {
      message.error('Ошибка при отмене задачи');
    }
  };
  
  const priorityUp = async (id: string) => {
    try {
      // In a real implementation, you would call an API endpoint to increase priority
      message.success('Приоритет повышен');
    } catch (error) {
      message.error('Ошибка при изменении приоритета');
    }
  };
  
  const viewLogs = (taskId: string) => {
    const task = tasks?.find(t => t.id === taskId);
    setSelectedTask(task || null);
    // In a real implementation, you would fetch actual logs for the task
    setDetailLogs([
      { id: 1, time: new Date().toLocaleTimeString(), log: `Задача ${taskId} начата` },
      { id: 2, time: new Date().toLocaleTimeString(), log: 'Этап 1: Загрузка данных завершена' },
      { id: 3, time: new Date().toLocaleTimeString(), log: 'Этап 2: Предобработка данных' }
    ]);
    setShowDetail(true);
  };
  
  // Show loading state
  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '20px' }}>
        <Spin tip="Загрузка очереди..." />
        {!connected && (
          <Alert 
            message="WS отключен — poll every 10s" 
            type="warning" 
            style={{ marginTop: '10px' }}
          />
        )}
      </div>
    );
  }
  
  // Show error state
  if (error) {
    return (
      <div>
        <Alert 
          message="Очередь задач" 
          description="Компонент для отслеживания активных задач в системе"
          type="info"
          icon={<InfoCircleOutlined />}
          style={{ marginBottom: '16px' }}
        />
        
        <Alert 
          message={`Ошибка: ${error.message}`} 
          description={
            <div>
              <p>Возможные причины:</p>
              <ul>
                <li>Отсутствует аутентификация (войдите в систему)</li>
                <li>Проблемы с подключением к серверу</li>
                <li>Сервер не отвечает</li>
                <li>Недостаточно прав доступа</li>
              </ul>
              {error.message.includes('403') && (
                <div style={{ marginTop: '10px' }}>
                  <p><strong>Решение для ошибки 403:</strong></p>
                  <ol>
                    <li>Нажмите кнопку &quot;Войти&quot; в правом верхнем углу</li>
                    <li>Введите любые логин/пароль для получения токена</li>
                    <li>После входа обновите страницу или нажмите кнопку ниже</li>
                  </ol>
                </div>
              )}
              <div style={{ marginTop: '15px' }}>
                <Button onClick={() => refetch()} style={{ marginRight: '10px' }}>Повторить попытку</Button>
                <Button onClick={() => window.location.reload()}>Обновить страницу</Button>
              </div>
            </div>
          }
          type="error" 
        />
      </div>
    );
  }
  
  // Show login prompt if not authenticated
  if (!user?.token) {
    return (
      <div>
        <Alert 
          message="Очередь задач" 
          description="Компонент для отслеживания активных задач в системе"
          type="info"
          icon={<InfoCircleOutlined />}
          style={{ marginBottom: '16px' }}
        />
        
        <Alert 
          message="Требуется аутентификация" 
          description={
            <div>
              <p>Для просмотра очереди задач необходимо войти в систему.</p>
              <p>Нажмите кнопку "Войти" в правом верхнем углу экрана.</p>
            </div>
          }
          type="warning" 
        />
      </div>
    );
  }
  
  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      render: (text: string) => <a onClick={() => viewLogs(text)}>{text.substring(0, 8)}...</a>
    },
    {
      title: 'Тип',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => type || 'Неизвестно'
    },
    {
      title: 'Статус',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={
          status === 'running' ? 'blue' : 
          status === 'failed' ? 'red' : 
          status === 'completed' ? 'green' : 
          'orange'
        }>
          {status === 'running' ? 'Выполняется' : 
           status === 'failed' ? 'Ошибка' : 
           status === 'completed' ? 'Завершено' : 
           'В очереди'}
        </Tag>
      )
    },
    {
      title: 'Прогресс',
      dataIndex: 'progress',
      key: 'progress',
      render: (progress: number) => (
        <Progress percent={progress || 0} size="small" status="active" />
      )
    },
    {
      title: 'Владелец',
      dataIndex: 'owner',
      key: 'owner',
      render: (owner: string) => owner || 'Система'
    },
    {
      title: 'Начато',
      dataIndex: 'started_at',
      key: 'started_at',
      render: (date: string) => date ? new Date(date).toLocaleString() : 'Неизвестно'
    },
    {
      title: 'ETA',
      dataIndex: 'eta',
      key: 'eta',
      render: (eta: string) => eta || 'Расчет...'
    },
    {
      title: 'Действия',
      key: 'actions',
      render: (_: any, record: QueueTask) => (
        <Space size="small">
          {record.status === 'failed' && (
            <Button 
              size="small" 
              onClick={() => retryTask(record.id)} 
              icon={<SyncOutlined />} 
            >
              Повторить
            </Button>
          )}
          <Button 
            size="small" 
            onClick={() => cancelTask(record.id)} 
            danger 
            icon={<CloseCircleOutlined />} 
          >
            Отменить
          </Button>
          <Button 
            size="small" 
            onClick={() => priorityUp(record.id)} 
            icon={<RiseOutlined />} 
          >
            Приоритет
          </Button>
        </Space>
      )
    }
  ];
  
  return (
    <div>
      <Alert 
        message="Очередь задач" 
        description="Компонент для отслеживания активных задач в системе"
        type="info"
        icon={<InfoCircleOutlined />}
        style={{ marginBottom: '16px' }}
      />
      
      {!connected && (
        <Alert 
          message="WS отключен — poll every 10s" 
          type="warning" 
          style={{ marginBottom: '16px' }}
        />
      )}
      
      <div style={{ marginBottom: 16 }}>
        <Input.Search 
          placeholder="Поиск по ID/владельцу" 
          style={{ width: 200, marginRight: 16 }} 
          data-cy="queue-search"
        />
        <Select 
          value={statusFilter} 
          onChange={setStatusFilter} 
          placeholder="Фильтр статуса" 
          style={{ width: 150, marginLeft: 16 }}
        >
          <Option value="">Все</Option>
          <Option value="running">Выполняется</Option>
          <Option value="queued">В очереди</Option>
          <Option value="failed">Ошибка</Option>
          <Option value="completed">Завершено</Option>
        </Select>
      </div>
      
      <Table 
        dataSource={tasks || []} 
        columns={columns} 
        rowKey="id" 
        pagination={{ pageSize: 10 }} 
        size="small" 
        locale={{ emptyText: 'Очередь пуста — запустите задачу' }}
        data-cy="queue-table"
      />
      
      <Modal
        visible={showDetail}
        title={`Детали Задачи ${selectedTask?.id}`}
        onCancel={() => setShowDetail(false)}
        footer={null}
        width={600}
      >
        <Timeline>
          {detailLogs.map(log => (
            <Timeline.Item key={log.id} color="blue">
              {log.time}: {log.log}
            </Timeline.Item>
          ))}
        </Timeline>
        <Button onClick={() => viewLogs(selectedTask?.id || '')} style={{ marginTop: 16 }}>
          Обновить Логи
        </Button>
      </Modal>
    </div>
  );
};

export default Queue;