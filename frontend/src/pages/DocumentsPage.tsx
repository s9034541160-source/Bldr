import { useState, useEffect } from 'react'
import { Table, Button, Input, Select, Space, Tag, message, Upload, Modal, Card } from 'antd'
import { UploadOutlined, SearchOutlined, EyeOutlined, DownloadOutlined, DeleteOutlined } from '@ant-design/icons'
import type { UploadProps } from 'antd'
import { documentsApi, Document } from '../api/documents'
import { useAuth } from '../contexts/AuthContext'

const { Search } = Input
const { Option } = Select


const DocumentsPage = () => {
  const { user } = useAuth()
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [documentType, setDocumentType] = useState<string | undefined>(undefined)
  const [searchType, setSearchType] = useState<'fulltext' | 'semantic' | 'hybrid'>('fulltext')
  const [uploadModalVisible, setUploadModalVisible] = useState(false)

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

  const handleUpload: UploadProps['customRequest'] = async (options) => {
    const { file, onSuccess, onError } = options

    try {
      await documentsApi.uploadDocument(
        file as File,
        (file as File).name,
        'document'
      )
      message.success('Документ успешно загружен')
      setUploadModalVisible(false)
      fetchDocuments()
      onSuccess?.(true)
    } catch (error: any) {
      message.error('Ошибка загрузки: ' + (error.response?.data?.detail || error.message))
      onError?.(error as Error)
    }
  }

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
            onClick={() => window.location.href = `/documents/${record.id}`}
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
        title="Загрузка документа"
        open={uploadModalVisible}
        onCancel={() => setUploadModalVisible(false)}
        footer={null}
      >
        <Upload
          customRequest={handleUpload}
          maxCount={1}
          accept=".pdf,.doc,.docx,.xls,.xlsx,.txt"
        >
          <Button icon={<UploadOutlined />}>Выбрать файл</Button>
        </Upload>
      </Modal>
    </div>
  )
}

export default DocumentsPage

