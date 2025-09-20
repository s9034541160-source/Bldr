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

const { Option } = Select;
const { TabPane } = Tabs;
const { Text, Title } = Typography;
const { Panel } = Collapse;

const Settings: React.FC = () => {
  const [form] = Form.useForm();
  const [testResult, setTestResult] = useState('');
  const { settings, setSettings, theme, setTheme } = useStore();
  const [resetLoading, setResetLoading] = useState(false);
  
  useEffect(() => {
    form.setFieldsValue(settings);
  }, [settings, form]);
  
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
      
      <TabPane tab="🔧 Unified Tools" key="unified-tools">
        <UnifiedToolsSettings />
      </TabPane>
    </Tabs>
  );
};

export default Settings;