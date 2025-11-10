import { Timeline, Space, Tag, Button, Popconfirm, Tooltip } from 'antd'
import { DownloadOutlined, EyeOutlined, RollbackOutlined } from '@ant-design/icons'
import type { DocumentVersion } from '../../api/documents'

interface VersionHistoryProps {
  versions: DocumentVersion[]
  onDownload: (versionNumber: number) => void
  onPreview?: (versionNumber: number) => void
  onRevert?: (versionNumber: number) => void
  currentVersion?: number
}

const VersionHistory = ({ versions, onDownload, onPreview, onRevert, currentVersion }: VersionHistoryProps) => {
  return (
    <Timeline>
      {versions.map((version) => {
        const isCurrent = currentVersion === version.version_number
        return (
          <Timeline.Item key={version.id} color={isCurrent ? 'green' : 'blue'}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Space>
                <strong>Версия {version.version_number}</strong>
                <Tag>{new Date(version.created_at).toLocaleString('ru-RU')}</Tag>
                {isCurrent && <Tag color="green">Текущая</Tag>}
              </Space>
              <div>{version.change_description || 'Без описания изменений'}</div>
              <Space wrap>
                {onPreview && (
                  <Button
                    size="small"
                    icon={<EyeOutlined />}
                    onClick={() => onPreview(version.version_number)}
                  >
                    Предпросмотр
                  </Button>
                )}
                <Button
                  size="small"
                  icon={<DownloadOutlined />}
                  onClick={() => onDownload(version.version_number)}
                >
                  Скачать
                </Button>
                {onRevert && !isCurrent && (
                  <Popconfirm
                    title="Откатить документ к этой версии?"
                    onConfirm={() => onRevert(version.version_number)}
                    okText="Да"
                    cancelText="Нет"
                  >
                    <Tooltip title="Создает новую версию с содержимым выбранной">
                      <Button size="small" icon={<RollbackOutlined />}>Откатить</Button>
                    </Tooltip>
                  </Popconfirm>
                )}
              </Space>
            </Space>
          </Timeline.Item>
        )
      })}
    </Timeline>
  )
}

export default VersionHistory
