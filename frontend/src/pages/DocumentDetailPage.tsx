import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Descriptions, Button, Space, Tag, Timeline, message, Spin } from 'antd'
import { ArrowLeftOutlined, DownloadOutlined, HistoryOutlined } from '@ant-design/icons'
import { documentsApi, Document, DocumentVersion } from '../api/documents'


const DocumentDetailPage = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [document, setDocument] = useState<Document | null>(null)
  const [versions, setVersions] = useState<DocumentVersion[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (id) {
      fetchDocument()
      fetchVersions()
    }
  }, [id])

  const fetchDocument = async () => {
    try {
      const data = await documentsApi.getDocument(Number(id))
      setDocument(data)
    } catch (error: any) {
      message.error('Ошибка загрузки документа: ' + (error.response?.data?.detail || error.message))
      navigate('/documents')
    } finally {
      setLoading(false)
    }
  }

  const fetchVersions = async () => {
    try {
      const data = await documentsApi.getDocumentVersions(Number(id))
      setVersions(data)
    } catch (error: any) {
      console.error('Ошибка загрузки версий:', error)
    }
  }

  const handleDownload = async (version?: number) => {
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
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/documents')}
        >
          Назад к списку
        </Button>

        <Card
          title={document.title}
          extra={
            <Space>
              <Button
                icon={<DownloadOutlined />}
                onClick={() => handleDownload()}
              >
                Скачать текущую версию
              </Button>
            </Space>
          }
        >
          <Descriptions bordered column={2}>
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

        <Card
          title={
            <Space>
              <HistoryOutlined />
              <span>История версий</span>
            </Space>
          }
        >
          <Timeline>
            {versions.map((version) => (
              <Timeline.Item key={version.id}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <strong>Версия {version.version_number}</strong>
                    <Tag style={{ marginLeft: 8 }}>
                      {new Date(version.created_at).toLocaleString('ru-RU')}
                    </Tag>
                  </div>
                  <div>{version.change_description || 'Без описания изменений'}</div>
                  <Button
                    size="small"
                    icon={<DownloadOutlined />}
                    onClick={() => handleDownload(version.version_number)}
                  >
                    Скачать эту версию
                  </Button>
                </Space>
              </Timeline.Item>
            ))}
          </Timeline>
        </Card>
      </Space>
    </div>
  )
}

export default DocumentDetailPage

