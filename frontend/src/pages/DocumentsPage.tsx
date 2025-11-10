import { useState, useEffect, useMemo } from 'react'
import { Table, Button, Input, Select, Space, Tag, message, Upload, Modal, Card, Typography, Progress, Divider } from 'antd'
import type { UploadProps, UploadFile } from 'antd'
import { UploadOutlined, SearchOutlined, EyeOutlined, DownloadOutlined, DeleteOutlined, InboxOutlined } from '@ant-design/icons'
import { RcFile } from 'antd/es/upload'
import { useNavigate } from 'react-router-dom'
import { documentsApi, Document } from '../api/documents'
import { useAuth } from '../contexts/AuthContext'

const { Search } = Input
const { Option } = Select
const { Dragger } = Upload
const { Paragraph } = Typography

const getBase64 = (file: RcFile) =>
  new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.readAsDataURL(file)
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = (error) => reject(error)
  })

const DocumentsPage = () => {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [documentType, setDocumentType] = useState<string | undefined>(undefined)
  const [searchType, setSearchType] = useState<'fulltext' | 'semantic' | 'hybrid'>('fulltext')
  const [uploadModalVisible, setUploadModalVisible] = useState(false)
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [uploading, setUploading] = useState(false)
  const [previewImage, setPreviewImage] = useState<string | null>(null)
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({})

  const fetchDocuments = async () => {
    setLoading(true)
    try {
      const params: any = {}
      if (searchQuery) params.query = searchQuery
      if (documentType) params.document_type = documentType
      if (searchQuery && searchType !== 'fulltext') {
        params.search_type = searchType
      }

      const data = await documentsApi.getDocuments(params)
      setDocuments(data)
    } catch (error: any) {
      message.error('Ошибка загрузки документов: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDocuments()
  }, [])

  const handleSearch = () => {
    fetchDocuments()
  }

  const uploadProps: UploadProps = {
    multiple: true,
    accept: '.pdf,.doc,.docx,.xls,.xlsx,.txt,.png,.jpg,.jpeg',
    fileList,
    async customRequest(options) {
      const { file, onSuccess, onError, onProgress } = options
      try {
        await documentsApi.uploadDocument(
          file as File,
          (file as File).name,
          'document',
          undefined,
          (event) => {
            if (event.total) {
              const percent = Math.round((event.loaded / event.total) * 100)
              setUploadProgress((prev) => ({ ...prev, [file.uid]: percent }))
              onProgress?.({ percent })
            }
          }
        )
        setUploadProgress((prev) => ({ ...prev, [file.uid]: 100 }))
        onSuccess?.(true)
        fetchDocuments()
      } catch (error: any) {
        setUploadProgress((prev) => ({ ...prev, [file.uid]: 0 }))
        message.error('Ошибка загрузки: ' + (error.response?.data?.detail || error.message))
        onError?.(error)
      }
    },
    onChange(info) {
      setFileList(info.fileList)
    },
    onRemove(file) {
      setUploadProgress((prev) => {
        const copy = { ...prev }
        delete copy[file.uid]
        return copy
      })
      return true
    },
    onPreview: async (file) => {
      if (!file.originFileObj) return
      const preview = await getBase64(file.originFileObj as RcFile)
      setPreviewImage(preview)
    },
    showUploadList: true,
    maxCount: 5,
  }

  const handleUploadModalClose = () => {
    setUploadModalVisible(false)
    setFileList([])
    setPreviewImage(null)
    setUploadProgress({})
  }

  const totalProgress = useMemo(() => {
    if (!fileList.length) return 0
    const sum = fileList.reduce((acc, file) => acc + (uploadProgress[file.uid] || 0), 0)
    return Math.round(sum / fileList.length)
  }, [fileList, uploadProgress])

  const handleDownload = async (documentId: number) => {
    try {
      const blob = await documentsApi.downloadDocument(documentId)
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      const doc = documents.find(d => d.id === documentId)
      link.setAttribute('download', doc?.file_name || `document_${documentId}`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      message.success('Документ скачан')
    } catch (error: any) {
      message.error('Ошибка скачивания: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleDelete = async (documentId: number) => {
    try {
      await documentsApi.deleteDocument(documentId)
      message.success('Документ удален')
      fetchDocuments()
    } catch (error: any) {
      message.error('Ошибка удаления: ' + (error.response?.data?.detail || error.message))
    }
  }

  const columns = [
    {
      title: 'Название',
      dataIndex: 'title',
      key: 'title',
      sorter: (a: Document, b: Document) => a.title.localeCompare(b.title),
    },
    {
      title: 'Тип',
      dataIndex: 'document_type',
      key: 'document_type',
      render: (type: string) => <Tag color="blue">{type}</Tag>,
    },
    {
      title: 'Версия',
      dataIndex: 'version',
      key: 'version',
      width: 80,
    },
    {
      title: 'Статус',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colorMap: Record<string, string> = {
          draft: 'default',
          approved: 'success',
          archived: 'warning',
        }
        return <Tag color={colorMap[status] || 'default'}>{status}</Tag>
      },
    },
    {
      title: 'Дата создания',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleDateString('ru-RU'),
      sorter: (a: Document, b: Document) =>
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    },
    {
      title: 'Действия',
      key: 'actions',
      render: (_: any, record: Document) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/documents/${record.id}`)}
          >
            Просмотр
          </Button>
          <Button
            type="link"
            icon={<DownloadOutlined />}
            onClick={() => handleDownload(record.id)}
          >
            Скачать
          </Button>
          <Button
            type="link"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.id)}
          >
            Удалить
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2>Документы</h2>
            <Button
              type="primary"
              icon={<UploadOutlined />}
              onClick={() => setUploadModalVisible(true)}
            >
              Загрузить документ
            </Button>
          </div>

          <Space style={{ width: '100%' }} wrap>
            <Search
              placeholder="Поиск документов..."
              allowClear
              enterButton={<SearchOutlined />}
              size="large"
              style={{ width: 400 }}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onSearch={handleSearch}
            />
            <Select
              placeholder="Тип документа"
              allowClear
              style={{ width: 200 }}
              value={documentType}
              onChange={setDocumentType}
            >
              <Option value="project_documentation">Проектная документация</Option>
              <Option value="working_drawings">Рабочие чертежи</Option>
              <Option value="specifications">Спецификации</Option>
              <Option value="estimates">Сметы</Option>
              <Option value="contracts">Договоры</Option>
              <Option value="acts">Акты</Option>
              <Option value="reports">Отчеты</Option>
            </Select>
            {searchQuery && (
              <Select
                placeholder="Тип поиска"
                style={{ width: 150 }}
                value={searchType}
                onChange={setSearchType}
              >
                <Option value="fulltext">Полнотекстовый</Option>
                <Option value="semantic">Семантический</Option>
                <Option value="hybrid">Гибридный</Option>
              </Select>
            )}
            <Button onClick={handleSearch}>Применить фильтры</Button>
          </Space>

          <Table
            columns={columns}
            dataSource={documents}
            loading={loading}
            rowKey="id"
            pagination={{
              pageSize: 20,
              showSizeChanger: true,
              showTotal: (total) => `Всего: ${total} документов`,
            }}
          />
        </Space>
      </Card>

      <Modal
        title="Загрузка документов"
        open={uploadModalVisible}
        onCancel={handleUploadModalClose}
        footer={null}
        width={600}
      >
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Dragger {...uploadProps} disabled={uploading}>
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">Перетащите файлы или нажмите для выбора</p>
            <p className="ant-upload-hint">Поддерживаются PDF, DOCX, XLSX, изображения и текстовые файлы</p>
          </Dragger>

          {fileList.length > 0 && (
            <Card size="small" title="Информация о загрузке">
              <Paragraph>Всего файлов: {fileList.length}</Paragraph>
              <Progress percent={totalProgress} status={totalProgress === 100 ? 'success' : 'active'} />
              {previewImage && (
                <div style={{ textAlign: 'center' }}>
                  <img src={previewImage} alt="preview" style={{ maxWidth: '100%', maxHeight: 240 }} />
                </div>
              )}
              <Divider />
              <Space wrap>
                {fileList.map((file) => (
                  <Button key={file.uid} type="default" size="small">
                    {file.name} ({uploadProgress[file.uid] || 0}%)
                  </Button>
                ))}
              </Space>
            </Card>
          )}
        </Space>
      </Modal>
    </div>
  )
}

export default DocumentsPage

