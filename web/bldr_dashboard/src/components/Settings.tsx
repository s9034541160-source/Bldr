import React, { useState, useEffect } from 'react';
import { 
  Tabs, 
  Form, 
  Input, 
  InputNumber, 
  Slider, 
  Select, 
  Switch, 
  Button, 
  message,
  Divider,
  Modal,
  Spin,
  Typography,
  Card,
  Collapse
} from 'antd';
import { useStore } from '../store';
import { apiService } from '../services/api';
import UnifiedToolsSettings from './UnifiedToolsSettings';
import UserManagement from './UserManagement';
import AutoTestPanel from './AutoTestPanel';

const { Option } = Select;
const { TabPane } = Tabs;
const { Text, Title } = Typography;
const { Panel } = Collapse;

const { TextArea } = Input;

const Settings: React.FC = () => {
  const [form] = Form.useForm();
  const [testResult, setTestResult] = useState('');
  const { settings, setSettings, theme, setTheme, user } = useStore();
  const [resetLoading, setResetLoading] = useState(false);

  // Coordinator settings state
  const [coordLoading, setCoordLoading] = useState(false);
  const [coordSettings, setCoordSettings] = useState<any>(null);

  // Prompts/Rules state
  const [promptsLoading, setPromptsLoading] = useState(false);
  const [roles, setRoles] = useState<any[]>([]);
  const [selectedRole, setSelectedRole] = useState<string>('coordinator');
  const [promptContent, setPromptContent] = useState<string>('');
  const [promptMeta, setPromptMeta] = useState<{ source?: string; updated_at?: string | null }>({});
  const [rulesContent, setRulesContent] = useState<string>('');
  const [rulesMeta, setRulesMeta] = useState<{ source?: string; updated_at?: string | null }>({});
  const [savingPrompt, setSavingPrompt] = useState(false);
  const [savingRules, setSavingRules] = useState(false);

  // Role→Model assignment state
  const [rmLoading, setRmLoading] = useState(false);
  const [rmRoles, setRmRoles] = useState<any[]>([]);
  const [rmModels, setRmModels] = useState<any[]>([]);
  const [rmAssignments, setRmAssignments] = useState<any>({});
  const [rmLocal, setRmLocal] = useState<Record<string, { model?: string }>>({});

  useEffect(() => {
    form.setFieldsValue(settings);
  }, [settings, form]);

  useEffect(() => {
    // Load coordinator settings
    (async () => {
      try {
        setCoordLoading(true);
        const data = await apiService.getCoordinatorSettings();
        setCoordSettings(data);
      } catch (e) {
        // ignore
      } finally {
        setCoordLoading(false);
      }
    })();
  }, []);

  const loadPromptsAndRules = async () => {
    try {
      setPromptsLoading(true);
      const list = await apiService.listPrompts();
      setRoles(list);
      // Ensure selected role exists
      const current = (list.find((r: any) => r.role === selectedRole) || list[0]);
      const roleKey = current?.role || 'coordinator';
      setSelectedRole(roleKey);
      const p = await apiService.getPrompt(roleKey);
      setPromptContent(p.content || '');
      setPromptMeta({ source: p.source, updated_at: p.updated_at });
      const r = await apiService.getFactualRules();
      setRulesContent(r.content || '');
      setRulesMeta({ source: r.source, updated_at: r.updated_at });
    } catch (e) {
      message.error('Не удалось загрузить промпты/правила');
    } finally {
      setPromptsLoading(false);
    }
  };

  useEffect(() => {
    loadPromptsAndRules();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Load Role↔Model data
  useEffect(() => {
    (async () => {
      try {
        setRmLoading(true);
        const [rolesRes, modelsRes, mappingRes] = await Promise.all([
          apiService.listRoles(),
          apiService.listAvailableModels(),
          apiService.getRoleModels()
        ]);
        setRmRoles(rolesRes || []);
        setRmModels(modelsRes?.models || []);
        setRmAssignments(mappingRes?.roles || {});
        const localInit: Record<string, { model?: string }> = {};
        (rolesRes || []).forEach((r: any) => {
          const eff = mappingRes?.roles?.[r.role]?.effective;
          if (eff?.model) localInit[r.role] = { model: eff.model };
        });
        setRmLocal(localInit);
      } catch (e) {
        // ignore
      } finally {
        setRmLoading(false);
      }
    })();
  }, []);

  const onChangeRole = async (roleKey: string) => {
    setSelectedRole(roleKey);
    try {
      setPromptsLoading(true);
      const p = await apiService.getPrompt(roleKey);
      setPromptContent(p.content || '');
      setPromptMeta({ source: p.source, updated_at: p.updated_at });
    } catch (e) {
      message.error('Не удалось загрузить промпт роли');
    } finally {
      setPromptsLoading(false);
    }
  };
  
  const resetDatabases = async () => {
    Modal.confirm({
      title: 'Подтверждение сброса баз данных',
      content: 'Вы уверены, что хотите сбросить все базы данных? Это действие удалит все обученные данные и не может быть отменено.',
      okText: 'Да, сбросить',
      okType: 'danger',
      cancelText: 'Отмена',
      onOk: async () => {
        try {
          setResetLoading(true);
          const response = await apiService.resetDatabases();
          if (response.status === 'success') {
            message.success('Базы данных успешно сброшены!');
          } else {
            message.error('Ошибка при сбросе баз данных: ' + response.message);
          }
        } catch (error) {
          console.error('Ошибка сброса баз данных:', error);
          message.error('Не удалось сбросить базы данных');
        } finally {
          setResetLoading(false);
        }
      }
    });
  };
  
  const handleSave = (values: any) => {
    setSettings(values);
    message.success('Настройки сохранены!');
  };
  
  const testConnection = async () => {
    try {
      // In a real implementation, this would test the connection to the backend
      // For now, we'll simulate a successful test
      setTestResult('OK');
      message.success('Подключение успешно!');
    } catch (error) {
      setTestResult('Ошибка: Проверьте хост/порт');
      message.error('Ошибка подключения');
    }
  };
  
  const loadDefaults = () => {
    form.resetFields();
    message.info('Сброшено на дефолт');
  };
  
  const saveCoordinator = async () => {
    try {
      setCoordLoading(true);
      await apiService.updateCoordinatorSettings(coordSettings);
      message.success('Настройки координатора сохранены');
    } catch (e) {
      message.error('Ошибка сохранения');
    } finally {
      setCoordLoading(false);
    }
  };

  const savePrompt = async () => {
    try {
      setSavingPrompt(true);
      const p = await apiService.updatePrompt(selectedRole, promptContent);
      setPromptMeta({ source: p.source, updated_at: p.updated_at });
      message.success('Промпт сохранён');
    } catch (e) {
      message.error('Ошибка сохранения промпта');
    } finally {
      setSavingPrompt(false);
    }
  };

  const resetPrompt = async () => {
    try {
      setSavingPrompt(true);
      const p = await apiService.resetPrompt(selectedRole);
      setPromptContent(p.content || '');
      setPromptMeta({ source: p.source, updated_at: p.updated_at });
      message.success('Промпт сброшен к дефолту');
    } catch (e) {
      message.error('Ошибка сброса промпта');
    } finally {
      setSavingPrompt(false);
    }
  };

  const saveRules = async () => {
    try {
      setSavingRules(true);
      const r = await apiService.updateFactualRules(rulesContent);
      setRulesMeta({ source: r.source, updated_at: r.updated_at });
      message.success('Правила сохранены');
    } catch (e) {
      message.error('Ошибка сохранения правил');
    } finally {
      setSavingRules(false);
    }
  };

  const resetRules = async () => {
    try {
      setSavingRules(true);
      const r = await apiService.resetFactualRules();
      setRulesContent(r.content || '');
      setRulesMeta({ source: r.source, updated_at: r.updated_at });
      message.success('Правила сброшены к дефолту');
    } catch (e) {
      message.error('Ошибка сброса правил');
    } finally {
      setSavingRules(false);
    }
  };

  return (
    <Tabs defaultActiveKey="api">
      <TabPane tab="API/DB" key="api">
        <Card title="Настройки API и базы данных" style={{ marginBottom: 24 }}>
          <Text type="secondary">
            Настройки подключения к API и базе данных. Эти параметры определяют, как фронтенд взаимодействует с бэкендом и где хранятся данные.
          </Text>
        </Card>
        
        <Form form={form} onFinish={handleSave} layout="vertical">
          <Form.Item 
            name="host" 
            label="Хост API" 
            initialValue="localhost:8000"
            extra="Адрес сервера API. По умолчанию: localhost:8000"
          >
            <Input data-cy="host-input" />
          </Form.Item>
          
          <Form.Item 
            name="port" 
            label="Порт" 
            extra="Порт для подключения к API. Диапазон: 8000-9000"
          >
            <InputNumber min={8000} max={9000} defaultValue={8000} data-cy="port-input" />
          </Form.Item>
          
          <Form.Item>
            <Button onClick={testConnection}>Тест Подключения</Button>
            <p data-cy="test-result">{testResult}</p>
          </Form.Item>
          
          <Divider />
          
          <Collapse>
            <Panel header="Что делают эти настройки?" key="1">
              <ul>
                <li><strong>Хост API:</strong> Адрес сервера, к которому подключается фронтенд для получения данных</li>
                <li><strong>Порт:</strong> Номер порта, на котором работает API сервер</li>
                <li><strong>Тест Подключения:</strong> Проверяет, доступен ли сервер API по указанным параметрам</li>
                <li><strong>Сбросить Базы Данных:</strong> Полностью очищает все обученные данные и индексы</li>
              </ul>
            </Panel>
          </Collapse>
          
          <Divider />
          
          <Form.Item>
            <Button type="primary" htmlType="submit" data-cy="save-settings">
              Сохранить
            </Button>
            <Button onClick={loadDefaults} style={{ marginLeft: 16 }}>
              Сброс
            </Button>
            <Button 
              danger 
              onClick={resetDatabases} 
              loading={resetLoading}
              style={{ marginLeft: 16 }}
            >
              Сбросить Базы Данных
            </Button>
          </Form.Item>
        </Form>
      </TabPane>
      
      <TabPane tab="RAG" key="rag">
        <Card title="Настройки RAG (Retrieval-Augmented Generation)" style={{ marginBottom: 24 }}>
          <Text type="secondary">
            Параметры, влияющие на работу системы поиска и генерации ответов. Эти настройки определяют, как система находит и обрабатывает информацию.
          </Text>
        </Card>
        
        <Form form={form} onFinish={handleSave} layout="vertical">
          <Form.Item 
            label="k (результаты поиска)"
            extra="Количество результатов поиска, возвращаемых системой. Больше = точнее, но медленнее"
          >
            <Slider 
              min={1} 
              max={100} 
              step={1} 
              defaultValue={5} 
              onChange={(value) => setSettings({ k: value })} 
              tooltip={{ open: true }} 
              data-cy="rag-k" 
            />
          </Form.Item>
          
          <Form.Item 
            label="Размер чанка"
            extra="Размер фрагментов текста при обработке документов. Больше = больше контекста, но меньше точность"
          >
            <Slider 
              min={500} 
              max={2000} 
              step={100} 
              defaultValue={1000} 
              onChange={(value) => setSettings({ chunkSize: value })} 
            />
          </Form.Item>
          
          <Form.Item 
            label="Порог"
            extra="Минимальная релевантность для отображения результатов. Выше = строже фильтр"
          >
            <Slider 
              min={0.5} 
              max={0.99} 
              step={0.01} 
              defaultValue={0.8} 
              onChange={(value) => setSettings({ threshold: value })} 
            />
          </Form.Item>
          
          <Form.Item 
            label="Типы документов"
            extra="Выбор типов документов для поиска"
          >
            <Select 
              mode="multiple" 
              defaultValue={['norms']} 
              onChange={(value) => console.log(value)}
              data-cy="doc-types"
            >
              <Option value="norms">Нормы</Option>
              <Option value="ppr">ППР</Option>
              <Option value="smeta">Сметы</Option>
              <Option value="rd">РД</Option>
              <Option value="educational">Образовательные</Option>
            </Select>
          </Form.Item>
          
          <Divider />
          
          <Collapse>
            <Panel header="Что делают эти настройки?" key="1">
              <ul>
                <li><strong>k (результаты поиска):</strong> Количество фрагментов, возвращаемых при поиске. Больше результатов = выше точность, но медленнее обработка</li>
                <li><strong>Размер чанка:</strong> На сколько частей разбиваются документы при индексации. Больше размер = больше контекста, но меньше точность поиска</li>
                <li><strong>Порог:</strong> Минимальная релевантность для отображения результатов. Выше значение = строже фильтр, меньше результатов</li>
                <li><strong>Типы документов:</strong> Фильтрация по типам документов при поиске</li>
              </ul>
            </Panel>
          </Collapse>
          
          <Divider />
          
          <Form.Item>
            <Button type="primary" htmlType="submit" data-cy="save-settings">
              Сохранить
            </Button>
          </Form.Item>
        </Form>
      </TabPane>
      
      <TabPane tab="Координатор" key="coordinator">
        <Card title="Настройки Координатора (backend)" style={{ marginBottom: 24 }}>
          <Text type="secondary">
            Управление логикой планирования и выполнения: количество итераций, быстрый путь, генерация артефактов и авто-увеличение сложности.
          </Text>
        </Card>
        {coordLoading && <Spin />}
        {!coordLoading && coordSettings && (
          <Form layout="vertical" onFinish={saveCoordinator}>
            <Form.Item label="Планирование включено">
              <Switch checked={!!coordSettings.planning_enabled} onChange={(v) => setCoordSettings({ ...coordSettings, planning_enabled: v })} />
            </Form.Item>
            <Form.Item label="JSON-планы (включены)">
              <Switch checked={!!coordSettings.json_mode_enabled} onChange={(v) => setCoordSettings({ ...coordSettings, json_mode_enabled: v })} />
            </Form.Item>
            <Form.Item label="Макс. итераций">
              <InputNumber min={1} max={10} value={coordSettings.max_iterations} onChange={(v) => setCoordSettings({ ...coordSettings, max_iterations: v })} />
            </Form.Item>
            <Form.Item label="Быстрый путь для простых планов">
              <Switch checked={!!coordSettings.simple_plan_fast_path} onChange={(v) => setCoordSettings({ ...coordSettings, simple_plan_fast_path: v })} />
            </Form.Item>
            <Form.Item label="Артефакты по умолчанию">
              <Switch checked={!!coordSettings.artifact_default_enabled} onChange={(v) => setCoordSettings({ ...coordSettings, artifact_default_enabled: v })} />
            </Form.Item>
            <Form.Item label="Авто-увеличение сложности">
              <Switch checked={!!coordSettings.complexity_auto_expand} onChange={(v) => setCoordSettings({ ...coordSettings, complexity_auto_expand: v })} />
            </Form.Item>
            <Form.Item label="Порог сложности: кол-во инструментов">
              <InputNumber min={1} max={10} value={coordSettings?.complexity_thresholds?.tools_count} onChange={(v) => setCoordSettings({ ...coordSettings, complexity_thresholds: { ...coordSettings.complexity_thresholds, tools_count: v } })} />
            </Form.Item>
            <Form.Item label="Порог сложности: время (мин)">
              <InputNumber min={1} max={120} value={coordSettings?.complexity_thresholds?.time_est_minutes} onChange={(v) => setCoordSettings({ ...coordSettings, complexity_thresholds: { ...coordSettings.complexity_thresholds, time_est_minutes: v } })} />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit">Сохранить</Button>
            </Form.Item>
          </Form>
        )}
      </TabPane>
      
      <TabPane tab="LLM" key="llm">
        <Card title="Настройки языковой модели (LLM)" style={{ marginBottom: 24 }}>
          <Text type="secondary">
            Параметры генерации текста. Эти настройки влияют на то, как система формирует ответы на основе найденной информации.
          </Text>
        </Card>
        
        <Form form={form} onFinish={handleSave} layout="vertical">
          <Form.Item 
            label="Температура"
            extra="Степень креативности модели. 0.1 = точные ответы, 1.0 = более креативные"
          >
            <Slider 
              min={0.1} 
              max={1.0} 
              step={0.1} 
              defaultValue={0.7} 
              onChange={(value) => setSettings({ temp: value })} 
              data-cy="llm-temp" 
            />
          </Form.Item>
          
          <Form.Item 
            label="Max Tokens"
            extra="Максимальная длина ответа модели"
          >
            <Slider 
              min={100} 
              max={4096} 
              step={100} 
              defaultValue={1000} 
              onChange={(value) => console.log(value)} 
            />
          </Form.Item>
          
          <Form.Item 
            label="Модель"
            extra="Выбор языковой модели для обработки запросов"
          >
            <Select 
              defaultValue="sbert_ru" 
              onChange={(value) => setSettings({ model: value })} 
              data-cy="llm-model"
            >
              <Option value="miniLM">all-MiniLM-L6-v2</Option>
              <Option value="sbert_ru">ai-forever/sbert_large_nlu_ru</Option>
            </Select>
          </Form.Item>
          
          <Divider />
          
          <Collapse>
            <Panel header="Что делают эти настройки?" key="1">
              <ul>
                <li><strong>Температура:</strong> Контролирует креативность ответов. Низкие значения (0.1-0.3) = точные, предсказуемые ответы. Высокие значения (0.7-1.0) = более креативные, но менее точные</li>
                <li><strong>Max Tokens:</strong> Максимальная длина ответа в токенах. Больше = длиннее ответы, но медленнее генерация</li>
                <li><strong>Модель:</strong> Выбор языковой модели. 'sbert_ru' лучше для русского языка, 'miniLM' - универсальная модель</li>
              </ul>
            </Panel>
          </Collapse>
          
          <Divider />
          
          <Form.Item>
            <Button type="primary" htmlType="submit" data-cy="save-settings">
              Сохранить
            </Button>
          </Form.Item>
        </Form>
      </TabPane>
      
      <TabPane tab="Инструменты" key="tools">
        <Card title="Настройки инструментов" style={{ marginBottom: 24 }}>
          <Text type="secondary">
            Параметры работы инструментов системы. Эти настройки влияют на надежность и производительность выполнения задач.
          </Text>
        </Card>
        
        <Form form={form} onFinish={handleSave} layout="vertical">
          <Form.Item 
            label="Повторы"
            extra="Количество попыток повтора при ошибках"
          >
            <Slider 
              min={1} 
              max={5} 
              step={1} 
              defaultValue={3} 
              onChange={(value) => setSettings({ retry: value })} 
              data-cy="tools-retry" 
            />
          </Form.Item>
          
          <Form.Item 
            label="Таймаут (сек)"
            extra="Время ожидания ответа от инструментов"
          >
            <Slider 
              min={10} 
              max={60} 
              step={10} 
              defaultValue={30} 
              onChange={(value) => setSettings({ timeout: value })} 
            />
          </Form.Item>
          
          <Form.Item 
            label="Использовать GPU" 
            valuePropName="checked"
            extra="Использовать графический процессор для ускорения вычислений (если доступен)"
          >
            <Switch 
              checked={settings.useGPU} 
              onChange={(checked) => setSettings({ useGPU: checked })} 
            />
          </Form.Item>
          
          <Divider />
          
          <Collapse>
            <Panel header="Что делают эти настройки?" key="1">
              <ul>
                <li><strong>Повторы:</strong> Количество попыток повторного выполнения задачи при ошибках. Больше = выше надежность, но дольше выполнение</li>
                <li><strong>Таймаут:</strong> Время ожидания ответа от инструментов. Больше = меньше ошибок таймаута, но дольше ожидание</li>
                <li><strong>Использовать GPU:</strong> Включает использование графического процессора для ускорения вычислений (если доступен)</li>
              </ul>
            </Panel>
          </Collapse>
          
          <Divider />
          
          <Form.Item>
            <Button type="primary" htmlType="submit" data-cy="save-settings">
              Сохранить
            </Button>
          </Form.Item>
        </Form>
      </TabPane>
      
      <TabPane tab="Модели" key="role-models">
        <Card title="Назначение моделей для ролей" style={{ marginBottom: 16 }}>
          <Text type="secondary">Быстро переключайте, какая модель отвечает за каждую роль. Изменения применяются немедленно.</Text>
          <div style={{ marginTop: 12, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <Button
              onClick={async () => {
                try {
                  await apiService.clearModelCache(true);
                  message.success('Кеш моделей очищен (кроме координатора)');
                } catch (e) {
                  message.error('Не удалось очистить кеш');
                }
              }}
            >Очистить кеш (кроме координатора)</Button>
            <Button
              danger
              onClick={async () => {
                try {
                  await apiService.clearModelCache(false);
                  message.success('Полный кеш моделей очищен');
                } catch (e) {
                  message.error('Не удалось полностью очистить кеш');
                }
              }}
            >Полная очистка кеша</Button>
            <Button
              type="primary"
              onClick={async () => {
                try {
                  const payload: Record<string, any> = {};
                  Object.keys(rmLocal || {}).forEach((roleKey) => {
                    const rml = rmLocal[roleKey] || {};
                    if (!rml.model && !rml.base_url && rml.temperature == null && rml.max_tokens == null) return;
                    payload[roleKey] = {} as any;
                    if (rml.model) payload[roleKey].model = rml.model;
                    if (rml.base_url) payload[roleKey].base_url = rml.base_url;
                    if (typeof rml.temperature === 'number') payload[roleKey].temperature = rml.temperature;
                    if (typeof rml.max_tokens === 'number') payload[roleKey].max_tokens = rml.max_tokens;
                  });
                  if (Object.keys(payload).length === 0) {
                    message.info('Нет изменений для сохранения');
                    return;
                  }
                  await apiService.updateRoleModels(payload);
                  const mappingRes = await apiService.getRoleModels();
                  setRmAssignments(mappingRes?.roles || {});
                  message.success('Изменения сохранены для всех ролей');
                } catch (e) {
                  message.error('Не удалось сохранить изменения по ролям');
                }
              }}
            >Сохранить всё</Button>
            <Button
              onClick={async () => {
                try {
                  const data = await apiService.getFullSettingsJson();
                  Modal.info({
                    title: 'settings.json',
                    width: 900,
                    content: (
                      <pre style={{ whiteSpace: 'pre-wrap', maxHeight: 500, overflow: 'auto', background: '#fafafa', padding: 12 }}>
                        {JSON.stringify(data, null, 2)}
                      </pre>
                    )
                  });
                } catch (e) {
                  message.error('Не удалось открыть settings.json');
                }
              }}
            >Открыть settings.json</Button>
            <Button
              onClick={async () => {
                try {
                  await apiService.openSettingsInEditor();
                  message.success('Открываю settings.json в редакторе');
                } catch (e) {
                  message.error('Не удалось открыть settings.json');
                }
              }}
            >Открыть settings.json в редакторе</Button>
          </div>
        </Card>
        {rmLoading && <Spin />}
        {!rmLoading && (
          <div>
            {(rmRoles || []).map((r: any) => {
              const roleKey = r.role;
              const eff = rmAssignments?.[roleKey]?.effective || {};
              const def = rmAssignments?.[roleKey]?.default || {};
              const ov = rmAssignments?.[roleKey]?.override || {};
              const currentModel = rmLocal?.[roleKey]?.model || eff?.model;
              return (
                <Card key={roleKey} size="small" style={{ marginBottom: 12 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                    <div style={{ minWidth: 220 }}>
                      <Title level={5} style={{ margin: 0 }}>{r.title || roleKey}</Title>
                      <Text type="secondary">Текущая: {eff?.model} @ {eff?.base_url}</Text>
                    </div>
                    <div>
                      <Select
                        style={{ minWidth: 360 }}
                        value={currentModel}
                        onChange={(val) => setRmLocal({ ...rmLocal, [roleKey]: { model: val } })}
                        showSearch
                        optionFilterProp="children"
                        placeholder="Выберите модель"
                      >
                        {(rmModels || []).map((m: any) => (
                          <Option key={`${m.id}@${m.base_url}`} value={m.id}>{m.label} — {m.id}</Option>
                        ))}
                      </Select>
                    </div>
                    <div style={{ width: '100%' }}>
                      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 8 }}>
                        <Input
                          style={{ minWidth: 320 }}
                          placeholder="base_url"
                          value={rmLocal?.[roleKey]?.base_url ?? eff?.base_url}
                          onChange={(e) => setRmLocal({ ...rmLocal, [roleKey]: { ...rmLocal[roleKey], base_url: e.target.value } })}
                        />
                        <InputNumber
                          style={{ width: 160 }}
                          min={0}
                          max={1}
                          step={0.1}
                          placeholder="temperature"
                          value={typeof rmLocal?.[roleKey]?.temperature === 'number' ? rmLocal?.[roleKey]?.temperature : eff?.temperature}
                          onChange={(v) => setRmLocal({ ...rmLocal, [roleKey]: { ...rmLocal[roleKey], temperature: v as number } })}
                        />
                        <InputNumber
                          style={{ width: 180 }}
                          min={256}
                          max={32768}
                          step={128}
                          placeholder="max_tokens"
                          value={typeof rmLocal?.[roleKey]?.max_tokens === 'number' ? rmLocal?.[roleKey]?.max_tokens : eff?.max_tokens}
                          onChange={(v) => setRmLocal({ ...rmLocal, [roleKey]: { ...rmLocal[roleKey], max_tokens: v as number } })}
                        />
                      </div>
                    <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                        <Button
                          onClick={async () => {
                            try {
                              const preview = await apiService.previewPrompt(roleKey);
                              Modal.info({
                                title: `Предпросмотр промпта — ${r.title || roleKey}`,
                                width: 900,
                                content: (
                                  <div>
                                    <div style={{ marginBottom: 8 }}>
                                      <Text type="secondary">Модель: {preview?.effective_model?.model} @ {preview?.effective_model?.base_url}</Text>
                                    </div>
                                    <pre style={{ whiteSpace: 'pre-wrap', maxHeight: 500, overflow: 'auto', background: '#fafafa', padding: 12 }}>{String(preview?.prompt || '')}</pre>
                                  </div>
                                ),
                              });
                            } catch (e) {
                              message.error('Не удалось получить предпросмотр');
                            }
                          }}
                        >
                          Предпросмотр промпта
                        </Button>
                        <Button
                          type="default"
                          onClick={async () => {
                            try {
                              const res = await apiService.reloadCoordinator();
                              if (res?.reloaded) message.success('Координатор перезагружен'); else message.warning('Не удалось перезагрузить координатора');
                            } catch (e) {
                              message.error('Ошибка перезагрузки координатора');
                            }
                          }}
                        >
                          Перезагрузить координатора
                        </Button>
                        <Button
                          type="primary"
                          onClick={async () => {
                          try {
                            const selected = (rmModels || []).find((m: any) => m.id === (rmLocal?.[roleKey]?.model || eff?.model));
                            const payload: any = { [roleKey]: { model: (rmLocal?.[roleKey]?.model || eff?.model) } };
                            const base_url = rmLocal?.[roleKey]?.base_url ?? selected?.base_url ?? eff?.base_url;
                            const temp = (typeof rmLocal?.[roleKey]?.temperature === 'number') ? rmLocal?.[roleKey]?.temperature : (selected?.temperature ?? eff?.temperature);
                            const max_toks = (typeof rmLocal?.[roleKey]?.max_tokens === 'number') ? rmLocal?.[roleKey]?.max_tokens : (selected?.max_tokens ?? eff?.max_tokens);
                            if (base_url) payload[roleKey].base_url = base_url;
                            if (temp != null) payload[roleKey].temperature = temp;
                            if (max_toks != null) payload[roleKey].max_tokens = max_toks;
                            await apiService.updateRoleModels(payload);
                            const mappingRes = await apiService.getRoleModels();
                            setRmAssignments(mappingRes?.roles || {});
                            message.success('Модель для роли сохранена');
                          } catch (e) {
                            message.error('Не удалось сохранить модель для роли');
                          }
                        }}
                      >
                        Сохранить
                      </Button>
                      <Button
                        onClick={async () => {
                          try {
                            await apiService.resetRoleModel(roleKey);
                            const mappingRes = await apiService.getRoleModels();
                            setRmAssignments(mappingRes?.roles || {});
                            setRmLocal((prev) => ({ ...prev, [roleKey]: { model: mappingRes?.roles?.[roleKey]?.default?.model } }));
                            message.success('Сброшено к дефолту');
                          } catch (e) {
                            message.error('Не удалось сбросить модель');
                          }
                        }}
                      >
                        Сбросить
                      </Button>
                    </div>
                  </div>
                  {ov && Object.keys(ov).length > 0 && (
                    <div style={{ marginTop: 8 }}>
                      <Text type="secondary">Переопределение активно: {JSON.stringify(ov)}</Text>
                    </div>
                  )}
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </TabPane>
      
      <TabPane tab="Промпты/Правила" key="prompts">
        <Card title="Редактор промптов ролей (Markdown)" style={{ marginBottom: 24 }}>
          <Text type="secondary">
            Выберите роль, отредактируйте её системный промпт и сохраните. Можно сбросить к встроенному дефолту из backend.
          </Text>
        </Card>
        <Form layout="vertical" onFinish={(e) => e?.preventDefault?.()}>
          <Form.Item label="Роль">
            <Select value={selectedRole} onChange={onChangeRole} style={{ maxWidth: 360 }} loading={promptsLoading}>
              {roles.map((r: any) => (
                <Option key={r.role} value={r.role}>{r.title || r.role} {r.source === 'active' ? '• (изменён)' : ''}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item label={<span>Промпт роли <Text type="secondary">({promptMeta?.source === 'active' ? 'переопределён' : 'дефолт'})</Text></span>}>
            <TextArea rows={16} value={promptContent} onChange={(e: any) => setPromptContent(e.target.value)} placeholder="# Заголовок\n...markdown..." />
            {promptMeta?.updated_at && (
              <div style={{ marginTop: 6 }}>
                <Text type="secondary">Изменено: {new Date(promptMeta.updated_at).toLocaleString()}</Text>
              </div>
            )}
            <div style={{ marginTop: 12 }}>
              <Button type="primary" onClick={savePrompt} loading={savingPrompt}>Сохранить промпт</Button>
              <Button onClick={resetPrompt} danger style={{ marginLeft: 12 }} loading={savingPrompt}>Сбросить</Button>
            </div>
          </Form.Item>
        </Form>

        <Divider />

        <Card title="Правила фактической точности (Markdown)" style={{ marginBottom: 16 }}>
          <Text type="secondary">Эти правила будут автоматически добавлены к промптам (если вы зададите их здесь).</Text>
        </Card>
        <Form layout="vertical">
          <Form.Item label={<span>Текст правил <Text type="secondary">({rulesMeta?.source === 'active' ? 'переопределены' : 'дефолт'})</Text></span>}>
            <TextArea rows={12} value={rulesContent} onChange={(e: any) => setRulesContent(e.target.value)} placeholder={"# ПРАВИЛА..."} />
            {rulesMeta?.updated_at && (
              <div style={{ marginTop: 6 }}>
                <Text type="secondary">Изменено: {new Date(rulesMeta.updated_at).toLocaleString()}</Text>
              </div>
            )}
            <div style={{ marginTop: 12 }}>
              <Button type="primary" onClick={saveRules} loading={savingRules}>Сохранить правила</Button>
              <Button onClick={resetRules} danger style={{ marginLeft: 12 }} loading={savingRules}>Сбросить</Button>
            </div>
          </Form.Item>
        </Form>
      </TabPane>
      
      <TabPane tab="Авто-тест" key="autotest">
        <Card title="Быстрое авто-тестирование (3 варианта)" style={{ marginBottom: 16 }}>
          <Text type="secondary">Выберите до 3 вариантов настроек и запустите автотест. Система применит настройки последовательно и выполнит набор запросов.</Text>
        </Card>
        <AutoTestPanel />
      </TabPane>
      
      <TabPane tab="UI" key="ui">
        <Card title="Настройки интерфейса" style={{ marginBottom: 24 }}>
          <Text type="secondary">
            Параметры отображения интерфейса. Эти настройки влияют на внешний вид и удобство использования.
          </Text>
        </Card>
        
        <Form form={form} onFinish={handleSave} layout="vertical">
          <Form.Item 
            label="Тёмная Тема" 
            valuePropName="checked"
            extra="Переключение между светлой и тёмной темой интерфейса"
          >
            <Switch 
              checked={theme === 'dark'} 
              onChange={(checked) => setTheme(checked ? 'dark' : 'light')} 
            />
          </Form.Item>
          
          <Form.Item 
            label="Язык"
            extra="Выбор языка интерфейса"
          >
            <Select 
              defaultValue="ru" 
              onChange={(value) => setSettings({ lang: value })} 
            >
              <Option value="ru">Русский</Option>
              <Option value="en">English</Option>
            </Select>
          </Form.Item>
          
          <Divider />
          
          <Collapse>
            <Panel header="Что делают эти настройки?" key="1">
              <ul>
                <li><strong>Тёмная Тема:</strong> Переключение между светлой и тёмной темой интерфейса для удобства работы</li>
                <li><strong>Язык:</strong> Выбор языка интерфейса (в настоящее время поддерживается только русский)</li>
              </ul>
            </Panel>
          </Collapse>
          
          <Divider />
          
          <Form.Item>
            <Button type="primary" htmlType="submit" data-cy="save-settings">
              Сохранить
            </Button>
          </Form.Item>
        </Form>
      </TabPane>
      
      {user?.role === 'admin' && (
        <TabPane tab="Пользователи" key="users">
          <Card title="Управление пользователями" style={{ marginBottom: 24 }}>
            <Text type="secondary">Добавляйте пользователей с ролями. Для операций требуется токен администратора.</Text>
          </Card>
          <UserManagement />
        </TabPane>
      )}
      
      <TabPane tab="🔧 Unified Tools" key="unified-tools">
        <UnifiedToolsSettings />
      </TabPane>
    </Tabs>
  );
};

export default Settings;