import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Card,
  Row,
  Col,
  Form,
  Input,
  Select,
  Button,
  Space,
  message,
  Table,
  Tag,
  Statistic,
  Descriptions,
  Divider,
  Tooltip,
  Modal,
} from 'antd'
import { PlusOutlined, DeploymentUnitOutlined, ThunderboltOutlined, DownloadOutlined } from '@ant-design/icons'
import { documentsApi, Document } from '../api/documents'
import {
  trainingApi,
  TrainingDataset,
  TrainingJob,
  CreateDatasetPayload,
  CreateJobPayload,
} from '../api/training'
import dayjs from 'dayjs'

const { Option } = Select

const DEFAULT_PROMPT = `You are an assistant helping to create question-answer pairs for construction project documentation.
Given the context, generate {num_pairs} factual questions with detailed answers. Use Russian if the context is Russian.
Return ONLY valid JSON array of objects with fields "question" and "answer". Context:
{context}`

const statusColor = (status: string) => {
  switch (status) {
    case 'ready':
    case 'completed':
    case 'validated':
      return 'green'
    case 'building':
    case 'running':
    case 'queued':
    case 'pending':
      return 'blue'
    case 'failed':
      return 'red'
    default:
      return 'default'
  }
}

const TrainingPage = () => {
  const [datasets, setDatasets] = useState<TrainingDataset[]>([])
  const [jobs, setJobs] = useState<TrainingJob[]>([])
  const [documents, setDocuments] = useState<Document[]>([])
  const [datasetModalVisible, setDatasetModalVisible] = useState(false)
  const [jobModalVisible, setJobModalVisible] = useState(false)
  const [datasetForm] = Form.useForm()
  const [jobForm] = Form.useForm()
  const [loadingDatasets, setLoadingDatasets] = useState(false)
  const [loadingJobs, setLoadingJobs] = useState(false)
  const [downloading, setDownloading] = useState<{ jobId: number; type: 'gguf' | 'adapter' } | null>(null)

  const loadDatasets = async () => {
    setLoadingDatasets(true)
    try {
      const data = await trainingApi.listDatasets()
      setDatasets(data)
    } catch (error: any) {
      message.error('Не удалось загрузить датасеты: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoadingDatasets(false)
    }
  }

  const loadJobs = async () => {
    setLoadingJobs(true)
    try {
      const data = await trainingApi.listJobs()
      setJobs(data)
    } catch (error: any) {
      message.error('Не удалось загрузить задания дообучения: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoadingJobs(false)
    }
  }

  useEffect(() => {
    loadDatasets()
    loadJobs()
    const fetchDocuments = async () => {
      try {
        const docs = await documentsApi.getDocuments({ limit: 200 })
        setDocuments(docs)
      } catch (error: any) {
        message.error('Не удалось загрузить список документов: ' + (error.response?.data?.detail || error.message))
      }
    }
    fetchDocuments()
  }, [])

  const refreshAll = async () => {
    await Promise.all([loadDatasets(), loadJobs()])
  }

  const handleCreateDataset = async () => {
    try {
      const values = await datasetForm.validateFields()
      const payload: CreateDatasetPayload = {
        name: values.name,
        description: values.description,
        document_ids: values.document_ids,
        questions_per_chunk: values.questions_per_chunk,
        total_pairs_target: values.total_pairs_target,
        qa_model_id: values.qa_model_id,
        prompt_template: values.prompt_template,
      }
      await trainingApi.createDataset(payload)
      message.success('Датасет поставлен в очередь на генерацию')
      setDatasetModalVisible(false)
      datasetForm.resetFields()
      loadDatasets()
    } catch (error: any) {
      if (error.errorFields) {
        return
      }
      message.error('Ошибка создания датасета: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleCreateJob = async () => {
    try {
      const values = await jobForm.validateFields()
      const payload: CreateJobPayload = {
        dataset_id: values.dataset_id,
        base_model_id: values.base_model_id,
        model_id: values.model_id,
        hyperparameters: values.hyperparameters ? JSON.parse(values.hyperparameters) : undefined,
        validation_prompts: values.validation_prompts
          ? values.validation_prompts
              .split('\n')
              .map((line: string) => line.trim())
              .filter((line: string) => line.length > 0)
          : undefined,
      }
      await trainingApi.createJob(payload)
      message.success('Задача дообучения запущена')
      setJobModalVisible(false)
      jobForm.resetFields()
      loadJobs()
    } catch (error: any) {
      if (error?.name === 'SyntaxError') {
        message.error('Гиперпараметры должны быть валидным JSON')
        return
      }
      if (error.errorFields) {
        return
      }
      message.error('Ошибка запуска дообучения: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleDownloadArtifacts = useCallback(
    async (jobId: number, type: 'gguf' | 'adapter') => {
      setDownloading({ jobId, type })
      try {
        const artifacts = await trainingApi.getJobArtifacts(jobId)
        const targetUrl = type === 'gguf' ? artifacts.gguf_url : artifacts.adapter_url
        if (!targetUrl) {
          message.warning('Артефакт для скачивания пока недоступен')
          return
        }
        window.open(targetUrl, '_blank', 'noopener')
      } catch (error: any) {
        message.error('Не удалось получить ссылку на артефакты: ' + (error.response?.data?.detail || error.message))
      } finally {
        setDownloading(null)
      }
    },
    []
  )

  const readyDatasets = useMemo(
    () => datasets.filter((dataset) => dataset.status === 'ready'),
    [datasets]
  )

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Row gutter={16}>
        <Col span={8}>
          <Card bordered>
            <Statistic
              title="Датасетов"
              value={datasets.length}
              prefix={<DeploymentUnitOutlined />}
              loading={loadingDatasets}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card bordered>
            <Statistic
              title="Задач дообучения"
              value={jobs.length}
              prefix={<ThunderboltOutlined />}
              loading={loadingJobs}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card bordered style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Space>
              <Button type="primary" icon={<PlusOutlined />} onClick={() => setDatasetModalVisible(true)}>
                Новый датасет
              </Button>
              <Button
                icon={<ThunderboltOutlined />}
                disabled={readyDatasets.length === 0}
                onClick={() => setJobModalVisible(true)}
              >
                Запустить дообучение
              </Button>
              <Button onClick={refreshAll}>Обновить</Button>
            </Space>
          </Card>
        </Col>
      </Row>

      <Card title="Датасеты" loading={loadingDatasets}>
        <Table<TrainingDataset>
          dataSource={datasets}
          rowKey="id"
          pagination={{ pageSize: 5 }}
          columns={[
            {
              title: 'ID',
              dataIndex: 'id',
              width: 70,
            },
            {
              title: 'Название',
              dataIndex: 'name',
            },
            {
              title: 'Статус',
              dataIndex: 'status',
              render: (status) => <Tag color={statusColor(status)}>{status}</Tag>,
            },
            {
              title: 'Примеры',
              dataIndex: 'total_examples',
            },
            {
              title: 'Создан',
              dataIndex: 'created_at',
              render: (value) => (value ? dayjs(value).format('DD.MM.YYYY HH:mm') : '-'),
            },
            {
              title: 'Настройки',
              dataIndex: 'config',
              render: (config) =>
                config ? (
                  <Tooltip title={JSON.stringify(config, null, 2)}>
                    <Tag>Config</Tag>
                  </Tooltip>
                ) : (
                  '-'
                ),
            },
            {
              title: 'Превью',
              render: (_, record) =>
                record.sample_preview ? (
                  <Tooltip
                    title={
                      <pre style={{ margin: 0, maxWidth: 400, whiteSpace: 'pre-wrap' }}>
                        {JSON.stringify(record.sample_preview, null, 2)}
                      </pre>
                    }
                  >
                    <Tag color="blue">Просмотр</Tag>
                  </Tooltip>
                ) : (
                  '-'
                ),
            },
          ]}
        />
      </Card>

      <Card title="Задачи дообучения" loading={loadingJobs}>
        <Table<TrainingJob>
          dataSource={jobs}
          rowKey="id"
          pagination={{ pageSize: 5 }}
          columns={[
            {
              title: 'ID',
              dataIndex: 'id',
              width: 70,
            },
            {
              title: 'Датасет',
              dataIndex: 'dataset_id',
            },
            {
              title: 'Модель',
              dataIndex: 'base_model_id',
            },
            {
              title: 'Идентификатор',
              dataIndex: 'model_id',
              render: (value) => value || '-',
            },
            {
              title: 'Статус',
              dataIndex: 'status',
              render: (status) => <Tag color={statusColor(status)}>{status}</Tag>,
            },
            {
              title: 'Валидация',
              render: (_, record) => (
                <Space direction="vertical">
                  <Tag color={statusColor(record.validation_status || 'pending')}>
                    {record.validation_status || 'pending'}
                  </Tag>
                  {record.validation_metrics ? (
                    <Tooltip
                      title={
                        <pre style={{ margin: 0, maxWidth: 400, whiteSpace: 'pre-wrap' }}>
                          {JSON.stringify(record.validation_metrics, null, 2)}
                        </pre>
                      }
                    >
                      <Tag>Детали</Tag>
                    </Tooltip>
                  ) : null}
                </Space>
              ),
            },
            {
              title: 'Создан',
              dataIndex: 'created_at',
              render: (value) => (value ? dayjs(value).format('DD.MM.YYYY HH:mm') : '-'),
            },
            {
              title: 'Завершён',
              dataIndex: 'completed_at',
              render: (value) => (value ? dayjs(value).format('DD.MM.YYYY HH:mm') : '-'),
            },
            {
              title: 'Метрики',
              dataIndex: 'metrics',
              render: (metrics) =>
                metrics ? (
                  <Tooltip
                    title={
                      <pre style={{ margin: 0, maxWidth: 400, whiteSpace: 'pre-wrap' }}>
                        {JSON.stringify(metrics, null, 2)}
                      </pre>
                    }
                  >
                    <Tag>Metrics</Tag>
                  </Tooltip>
                ) : (
                  '-'
                ),
            },
            {
              title: 'Артефакты',
              render: (_, record) => (
                <Space>
                  <Button
                    size="small"
                    icon={<DownloadOutlined />}
                    onClick={() => handleDownloadArtifacts(record.id, 'gguf')}
                    loading={downloading?.jobId === record.id && downloading?.type === 'gguf'}
                    disabled={!record.gguf_path && !record.artifact_path}
                  >
                    GGUF
                  </Button>
                  <Button
                    size="small"
                    icon={<DownloadOutlined />}
                    onClick={() => handleDownloadArtifacts(record.id, 'adapter')}
                    loading={downloading?.jobId === record.id && downloading?.type === 'adapter'}
                    disabled={!record.adapter_path}
                  >
                    LoRA
                  </Button>
                </Space>
              ),
            },
          ]}
        />
      </Card>

      <Modal
        title="Создание датасета"
        open={datasetModalVisible}
        onOk={handleCreateDataset}
        onCancel={() => setDatasetModalVisible(false)}
        okText="Создать"
        cancelText="Отмена"
      >
        <Form
          layout="vertical"
          form={datasetForm}
          initialValues={{ questions_per_chunk: 5, total_pairs_target: 0, prompt_template: DEFAULT_PROMPT }}
        >
          <Form.Item
            name="name"
            label="Название датасета"
            rules={[{ required: true, message: 'Введите название' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item name="description" label="Описание">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item
            name="document_ids"
            label="Документы"
            rules={[{ required: true, message: 'Выберите хотя бы один документ' }]}
          >
            <Select
              mode="multiple"
              placeholder="Выберите документы"
              optionFilterProp="children"
              filterOption={(input, option) => (option?.children as string).toLowerCase().includes(input.toLowerCase())}
            >
              {documents.map((doc) => (
                <Option key={doc.id} value={doc.id}>
                  {doc.title} (#{doc.id})
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            name="questions_per_chunk"
            label="Количество вопросов на фрагмент"
            rules={[{ required: true }]}
          >
            <Select>
              {[1, 2, 3, 4].map((value) => (
                <Option key={value} value={value}>
                  {value}
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            name="total_pairs_target"
            label="Целевое количество Q/A (0 — без лимита)"
            tooltip="Если указать 0, будет сгенерировано столько Q/A, сколько позволит контент."
          >
            <Input type="number" min={0} />
          </Form.Item>
          <Form.Item name="qa_model_id" label="Модель для генерации Q/A (опционально)">
            <Input placeholder="Например, default или document_agent" />
          </Form.Item>
          <Form.Item name="prompt_template" label="Шаблон промпта">
            <Input.TextArea rows={4} placeholder="Используется шаблон по умолчанию" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="Запуск дообучения"
        open={jobModalVisible}
        onOk={handleCreateJob}
        onCancel={() => setJobModalVisible(false)}
        okText="Запустить"
        cancelText="Отмена"
      >
        <Form layout="vertical" form={jobForm}>
          <Form.Item
            name="dataset_id"
            label="Готовый датасет"
            rules={[{ required: true, message: 'Выберите датасет' }]}
          >
            <Select placeholder="Выберите датасет">
              {readyDatasets.map((dataset) => (
                <Option key={dataset.id} value={dataset.id}>
                  {dataset.name} (#{dataset.id})
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            name="base_model_id"
            label="Базовая модель"
            rules={[{ required: true, message: 'Укажите модель' }]}
          >
            <Input placeholder="unsloth/llama-3-8b-Instruct-bnb-4bit" />
          </Form.Item>
          <Form.Item name="model_id" label="Идентификатор новой модели">
            <Input placeholder="finetune_custom_model" />
          </Form.Item>
          <Form.Item
            name="hyperparameters"
            label="Гиперпараметры (JSON)"
            tooltip='Например: {"epochs": 3, "learning_rate": 2e-4}'
          >
            <Input.TextArea rows={4} placeholder='{"epochs": 3, "learning_rate": 2e-4}' />
          </Form.Item>
          <Form.Item
            name="validation_prompts"
            label="Промпты для валидации (по одному в строке)"
            tooltip="Если оставить пустым, будут использованы стандартные проверки."
          >
            <Input.TextArea rows={3} placeholder="Опиши ключевые выводы...\nПеречисли основные разделы..." />
          </Form.Item>
        </Form>
      </Modal>

      <Card title="Инструкция">
        <Descriptions column={1} bordered size="small">
          <Descriptions.Item label="1. Создание датасета">
            Выберите документы, укажите параметры генерации Q/A. После завершения статус изменится на <Tag color="green">ready</Tag>.
          </Descriptions.Item>
          <Descriptions.Item label="2. Запуск дообучения">
            Выберите готовый датасет и базовую модель. При необходимости передайте гиперпараметры (например, число эпох).
          </Descriptions.Item>
          <Descriptions.Item label="3. Мониторинг">
            Статусы задач обновляются автоматически после очередного запроса. Для актуализации нажмите кнопку «Обновить».
          </Descriptions.Item>
        </Descriptions>
      </Card>
    </Space>
  )
}

export default TrainingPage

