import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Card,
  Descriptions,
  Button,
  Space,
  Tag,
  message,
  Spin,
  Tabs,
  Modal,
  Upload,
  Input,
  UploadFile,
  Form,
  Select,
  Divider,
} from 'antd'
import {
  ArrowLeftOutlined,
  DownloadOutlined,
  CloudUploadOutlined,
  PlusOutlined,
  MinusCircleOutlined,
} from '@ant-design/icons'
import type { UploadProps } from 'antd'
import { RcFile } from 'antd/es/upload'
import {
  documentsApi,
  Document,
  DocumentVersion,
} from '../api/documents'
import DocumentPreview from '../components/documents/DocumentPreview'
import VersionHistory from '../components/documents/VersionHistory'
import VersionCompare from '../components/documents/VersionCompare'

const { TextArea } = Input
const { Option } = Select

interface MetadataFormValues {
  custom?: { key: string; value: string }[]
  tags?: string[]
  linked_document_ids?: number[]
}

const getFileFromUploadFile = (file: UploadFile) => file.originFileObj as RcFile

const DocumentDetailPage = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [documentData, setDocumentData] = useState<Document | null>(null)
  const [versions, setVersions] = useState<DocumentVersion[]>([])
  const [loading, setLoading] = useState(true)
  const [previewVersion, setPreviewVersion] = useState<number | undefined>(undefined)
  const [uploadModalOpen, setUploadModalOpen] = useState(false)
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [changeDescription, setChangeDescription] = useState('')
  const [allDocuments, setAllDocuments] = useState<Document[]>([])
  const [metadataSaving, setMetadataSaving] = useState(false)
  const [metadataForm] = Form.useForm()

  useEffect(() => {
    if (id) {
      fetchDocument()
      fetchVersions()
    }
  }, [id])

  useEffect(() => {
    const loadDocuments = async () => {
      try {
        const list = await documentsApi.getDocuments({ limit: 200 })
        setAllDocuments(list.filter((doc) => doc.id !== Number(id)))
      } catch (error: any) {
        message.warning('Не удалось загрузить список документов для связей: ' + (error.response?.data?.detail || error.message))
      }
    }
    loadDocuments()
  }, [id])

  useEffect(() => {
    if (!documentData) return
    const customEntries = Object.entries((documentData.metadata?.custom as Record<string, unknown>) ?? {}).map(([key, value]) => ({
      key,
      value: typeof value === 'string' ? value : JSON.stringify(value),
    }))
    metadataForm.setFieldsValue({
      custom: customEntries.length ? customEntries : [{ key: '', value: '' }],
      tags: (documentData.metadata?.tags as string[]) || [],
      linked_document_ids: (documentData.metadata?.linked_documents as number[]) || [],
    })
  }, [documentData, metadataForm])

  const fetchDocument = async () => {
    if (!id) return
    try {
      const data = await documentsApi.getDocument(Number(id))
      setDocumentData(data)
      setPreviewVersion(data.version)
    } catch (error: any) {
      message.error('Ошибка загрузки документа: ' + (error.response?.data?.detail || error.message))
      navigate('/documents')
    } finally {
      setLoading(false)
    }
  }

  const fetchVersions = async () => {
    if (!id) return
    try {
      const data = await documentsApi.getDocumentVersions(Number(id))
      setVersions(data)
    } catch (error: any) {
      message.error('Ошибка загрузки версий: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleDownload = async (version?: number) => {
    if (!id) return
    try {
      const blob = await documentsApi.downloadDocument(Number(id), version)
      const url = window.URL.createObjectURL(blob)
      const link = window.document.createElement('a')
      link.href = url
      link.setAttribute('download', documentData?.file_name || `document_${id}`)
      window.document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      message.success('Документ скачан')
    } catch (error: any) {
      message.error('Ошибка скачивания: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleRevert = async (versionNumber: number) => {
    if (!id) return
    try {
      await documentsApi.revertToVersion(Number(id), versionNumber)
      message.success('Документ откатан к выбранной версии')
      fetchDocument()
      fetchVersions()
    } catch (error: any) {
      message.error('Ошибка отката: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleCreateVersion: UploadProps['onChange'] = ({ fileList: newFileList }) => {
    setFileList(newFileList.slice(-1))
  }

  const handleVersionUpload = async () => {
    if (!id || !fileList.length) {
      message.warning('Выберите файл для загрузки новой версии')
      return
    }
    try {
      const file = getFileFromUploadFile(fileList[0])
      await documentsApi.createVersion(Number(id), file, changeDescription)
      message.success('Создана новая версия документа')
      setUploadModalOpen(false)
      setFileList([])
      setChangeDescription('')
      fetchDocument()
      fetchVersions()
    } catch (error: any) {
      message.error('Ошибка создания версии: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleFillFromExtracted = () => {
    if (!documentData?.metadata || !('extracted' in documentData.metadata)) {
      message.info('Нет извлеченных метаданных для заполнения')
      return
    }
    const extracted = (documentData.metadata.extracted as Record<string, unknown>) || {}
    const customEntries = Object.entries(extracted).map(([key, value]) => ({
      key,
      value: typeof value === 'string' ? value : JSON.stringify(value),
    }))
    metadataForm.setFieldsValue({
      custom: customEntries.length ? customEntries : [{ key: '', value: '' }],
    })
  }

  const handleMetadataSubmit = async (values: MetadataFormValues) => {
    if (!id) return
    setMetadataSaving(true)
    try {
      const customEntries = values.custom?.filter((item) => item.key) || []
      const customObject = customEntries.reduce<Record<string, unknown>>((acc, item) => {
        acc[item.key] = item.value
        return acc
      }, {})
      const payload = {
        metadata: customObject,
        tags: values.tags || [],
        linked_document_ids: values.linked_document_ids || [],
      }
      const updated = await documentsApi.updateMetadata(Number(id), payload)
      setDocumentData(updated)
      message.success('Метаданные обновлены')
    } catch (error: any) {
      message.error('Ошибка обновления метаданных: ' + (error.response?.data?.detail || error.message))
    } finally {
      setMetadataSaving(false)
    }
  }

  if (loading) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!documentData) {
    return null
  }

  const statusColorMap: Record<string, string> = {
    draft: 'default',
    approved: 'success',
    archived: 'warning',
  }

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/documents')}>
          Назад к списку
        </Button>

        <Tabs defaultActiveKey="overview">
          <Tabs.TabPane tab="Обзор" key="overview">
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <Card
                title={documentData.title}
                extra={
                  <Space>
                    <Button icon={<DownloadOutlined />} onClick={() => handleDownload()}>
                      Скачать текущую версию
                    </Button>
                    <Button
                      icon={<CloudUploadOutlined />}
                      type="primary"
                      onClick={() => setUploadModalOpen(true)}
                    >
                      Новая версия
                    </Button>
                  </Space>
                }
              >
                <Descriptions bordered column={2} size="small">
                  <Descriptions.Item label="ID">{documentData.id}</Descriptions.Item>
                  <Descriptions.Item label="Тип документа">
                    <Tag color="blue">{documentData.document_type}</Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="Имя файла">{documentData.file_name}</Descriptions.Item>
                  <Descriptions.Item label="Версия">{documentData.version}</Descriptions.Item>
                  <Descriptions.Item label="Статус">
                    <Tag color={statusColorMap[documentData.status] || 'default'}>
                      {documentData.status}
                    </Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="Дата создания">
                    {new Date(documentData.created_at).toLocaleString('ru-RU')}
                  </Descriptions.Item>
                </Descriptions>
              </Card>
            </Space>
          </Tabs.TabPane>

          <Tabs.TabPane tab="Предпросмотр" key="preview">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Select
                value={previewVersion}
                style={{ width: 220 }}
                onChange={(value) => setPreviewVersion(value)}
                options={versions.map((version) => ({
                  label: `Версия ${version.version_number}`,
                  value: version.version_number,
                }))}
              />
              <DocumentPreview
                documentId={documentData.id}
                fileName={documentData.file_name}
                mimeType={documentData.mime_type}
                version={previewVersion}
              />
            </Space>
          </Tabs.TabPane>

          <Tabs.TabPane tab="История версий" key="history">
            <VersionHistory
              versions={versions}
              currentVersion={documentData.version}
              onDownload={handleDownload}
              onPreview={(versionNumber) => setPreviewVersion(versionNumber)}
              onRevert={handleRevert}
            />
          </Tabs.TabPane>

          <Tabs.TabPane tab="Сравнение версий" key="compare">
            <VersionCompare documentId={documentData.id} versions={versions} />
          </Tabs.TabPane>

          <Tabs.TabPane tab="Метаданные" key="metadata">
            <Card>
              <Space direction="vertical" style={{ width: '100%' }} size="large">
                <Space wrap>
                  <Button onClick={handleFillFromExtracted}>Заполнить из извлеченных данных</Button>
                </Space>
                <Form
                  layout="vertical"
                  form={metadataForm}
                  onFinish={handleMetadataSubmit}
                  initialValues={{ custom: [{ key: '', value: '' }] }}
                >
                  <Divider orientation="left">Пользовательские поля</Divider>
                  <Form.List name="custom">
                    {(fields, { add, remove }) => (
                      <>
                        {fields.map((field, index) => (
                          <Space
                            key={field.key}
                            align="baseline"
                            style={{ display: 'flex', marginBottom: 8 }}
                          >
                            <Form.Item
                              {...field}
                              name={[field.name, 'key']}
                              fieldKey={[field.fieldKey ?? field.key, 'key']}
                              label={index === 0 ? 'Ключ' : undefined}
                              rules={[{ required: index === 0, message: 'Введите ключ' }]}
                            >
                              <Input placeholder="Например, номер контракта" allowClear />
                            </Form.Item>
                            <Form.Item
                              {...field}
                              name={[field.name, 'value']}
                              fieldKey={[field.fieldKey ?? field.key, 'value']}
                              label={index === 0 ? 'Значение' : undefined}
                              rules={[{ required: index === 0, message: 'Введите значение' }]}
                            >
                              <Input placeholder="Значение" allowClear />
                            </Form.Item>
                            {fields.length > 1 && (
                              <MinusCircleOutlined onClick={() => remove(field.name)} />
                            )}
                          </Space>
                        ))}
                        <Form.Item>
                          <Button type="dashed" onClick={() => add({ key: '', value: '' })} icon={<PlusOutlined />} block>
                            Добавить поле
                          </Button>
                        </Form.Item>
                      </>
                    )}
                  </Form.List>

                  <Divider orientation="left">Теги</Divider>
                  <Form.Item name="tags">
                    <Select
                      mode="tags"
                      allowClear
                      placeholder="Добавьте теги"
                      tokenSeparators={[',']}
                    />
                  </Form.Item>

                  <Divider orientation="left">Связанные документы</Divider>
                  <Form.Item name="linked_document_ids">
                    <Select
                      mode="multiple"
                      allowClear
                      placeholder="Выберите связанные документы"
                    >
                      {allDocuments.map((doc) => (
                        <Option key={doc.id} value={doc.id}>
                          {doc.title} (#{doc.id})
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>

                  <Button type="primary" htmlType="submit" loading={metadataSaving}>
                    Сохранить метаданные
                  </Button>
                </Form>

                {documentData.metadata?.classification && (
                  <Card type="inner" title="Классификация по ГОСТ">
                    <pre style={{ whiteSpace: 'pre-wrap' }}>
                      {JSON.stringify(documentData.metadata.classification, null, 2)}
                    </pre>
                  </Card>
                )}
                {documentData.metadata?.extracted && (
                  <Card type="inner" title="Извлеченные данные">
                    <pre style={{ whiteSpace: 'pre-wrap' }}>
                      {JSON.stringify(documentData.metadata.extracted, null, 2)}
                    </pre>
                  </Card>
                )}
              </Space>
            </Card>
          </Tabs.TabPane>
        </Tabs>
      </Space>

      <Modal
        title="Загрузка новой версии"
        open={uploadModalOpen}
        onCancel={() => {
          setUploadModalOpen(false)
          setFileList([])
          setChangeDescription('')
        }}
        onOk={handleVersionUpload}
        okText="Загрузить"
        cancelText="Отмена"
      >
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Upload
            beforeUpload={() => false}
            onChange={handleCreateVersion}
            fileList={fileList}
            maxCount={1}
            accept=".pdf,.doc,.docx,.xls,.xlsx,.txt,.png,.jpg,.jpeg"
          >
            <Button icon={<CloudUploadOutlined />}>Выбрать файл</Button>
          </Upload>
          <Form layout="vertical">
            <Form.Item label="Описание изменений">
              <TextArea
                rows={4}
                value={changeDescription}
                onChange={(event) => setChangeDescription(event.target.value)}
                placeholder="Опишите, что изменилось в документе"
              />
            </Form.Item>
          </Form>
        </Space>
      </Modal>
    </div>
  )
}

export default DocumentDetailPage

