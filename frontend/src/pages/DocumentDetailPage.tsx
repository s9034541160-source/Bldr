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
} from 'antd'
import {
  ArrowLeftOutlined,
  DownloadOutlined,
  CloudUploadOutlined,
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

const getFileFromUploadFile = (file: UploadFile) => file.originFileObj as RcFile

const DocumentDetailPage = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [document, setDocument] = useState<Document | null>(null)
  const [versions, setVersions] = useState<DocumentVersion[]>([])
  const [loading, setLoading] = useState(true)
  const [previewVersion, setPreviewVersion] = useState<number | undefined>(undefined)
  const [uploadModalOpen, setUploadModalOpen] = useState(false)
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [changeDescription, setChangeDescription] = useState('')

  useEffect(() => {
    if (id) {
      fetchDocument()
      fetchVersions()
    }
  }, [id])

  const fetchDocument = async () => {
    if (!id) return
    try {
      const data = await documentsApi.getDocument(Number(id))
      setDocument(data)
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
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', document?.file_name || `document_${id}`)
      document.body.appendChild(link)
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

  if (loading) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!document) {
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
                title={document.title}
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
                  <Descriptions.Item label="ID">{document.id}</Descriptions.Item>
                  <Descriptions.Item label="Тип документа">
                    <Tag color="blue">{document.document_type}</Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="Имя файла">{document.file_name}</Descriptions.Item>
                  <Descriptions.Item label="Версия">{document.version}</Descriptions.Item>
                  <Descriptions.Item label="Статус">
                    <Tag color={statusColorMap[document.status] || 'default'}>
                      {document.status}
                    </Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="Дата создания">
                    {new Date(document.created_at).toLocaleString('ru-RU')}
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
                documentId={document.id}
                fileName={document.file_name}
                mimeType={document.mime_type}
                version={previewVersion}
              />
            </Space>
          </Tabs.TabPane>

          <Tabs.TabPane tab="История версий" key="history">
            <VersionHistory
              versions={versions}
              currentVersion={document.version}
              onDownload={handleDownload}
              onPreview={(versionNumber) => setPreviewVersion(versionNumber)}
              onRevert={handleRevert}
            />
          </Tabs.TabPane>

          <Tabs.TabPane tab="Сравнение версий" key="compare">
            <VersionCompare documentId={document.id} versions={versions} />
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

