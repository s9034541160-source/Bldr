import { useEffect, useState } from 'react'
import { Card, Spin, Tabs, Alert, Empty } from 'antd'
import type { TabsProps } from 'antd'
import { documentsApi } from '../../api/documents'

interface DocumentPreviewProps {
  documentId: number
  fileName: string
  mimeType?: string
  version?: number
}

type PreviewState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; contentType: 'pdf' | 'image' | 'text' | 'unsupported'; data: string }

const DocumentPreview = ({ documentId, version, fileName, mimeType }: DocumentPreviewProps) => {
  const [state, setState] = useState<PreviewState>({ status: 'idle' })
  const [objectUrl, setObjectUrl] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    const loadPreview = async () => {
      setState({ status: 'loading' })
      try {
        const blob = await documentsApi.downloadDocument(documentId, version)
        if (!active) return

        const type = mimeType || blob.type || ''
        if (type.includes('pdf')) {
          const url = URL.createObjectURL(blob)
          setObjectUrl(url)
          setState({ status: 'ready', contentType: 'pdf', data: url })
          return
        }
        if (type.startsWith('image/')) {
          const url = URL.createObjectURL(blob)
          setObjectUrl(url)
          setState({ status: 'ready', contentType: 'image', data: url })
          return
        }
        if (type.startsWith('text/') || type.includes('json') || type.includes('xml')) {
          const text = await blob.text()
          setState({ status: 'ready', contentType: 'text', data: text })
          return
        }
        setState({ status: 'ready', contentType: 'unsupported', data: '' })
      } catch (error: any) {
        if (!active) return
        setState({ status: 'error', message: error?.message || 'Не удалось загрузить документ' })
      }
    }

    loadPreview()
    return () => {
      active = false
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl)
      }
    }
  }, [documentId, version, mimeType, objectUrl])

  const items: TabsProps['items'] = [
    {
      key: 'preview',
      label: 'Предпросмотр',
      children: renderPreview(),
    },
  ]

  function renderPreview() {
    switch (state.status) {
      case 'idle':
      case 'loading':
        return (
          <div style={{ textAlign: 'center', padding: 24 }}>
            <Spin size="large" />
          </div>
        )
      case 'error':
        return <Alert type="error" showIcon message={state.message} />
      case 'ready':
        switch (state.contentType) {
          case 'pdf':
            return (
              <iframe
                title={`preview-${fileName}`}
                src={state.data}
                style={{ width: '100%', height: 600, border: 'none' }}
              />
            )
          case 'image':
            return (
              <div style={{ textAlign: 'center' }}>
                <img src={state.data} alt={fileName} style={{ maxWidth: '100%', maxHeight: 600 }} />
              </div>
            )
          case 'text':
            return (
              <pre
                style={{
                  maxHeight: 600,
                  overflow: 'auto',
                  background: '#f5f5f5',
                  padding: 16,
                  borderRadius: 8,
                }}
              >
                {state.data}
              </pre>
            )
          default:
            return <Empty description="Предпросмотр для данного формата недоступен" />
        }
    }
  }

  return (
    <Card title="Предпросмотр">
      <Tabs items={items} />
    </Card>
  )
}

export default DocumentPreview
