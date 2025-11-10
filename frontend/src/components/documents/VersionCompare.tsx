import { useState } from 'react'
import { Card, Space, Select, Button, Alert, Typography, Spin } from 'antd'
import type { DocumentVersion, DocumentComparison } from '../../api/documents'
import { documentsApi } from '../../api/documents'

const { Text, Paragraph } = Typography

interface VersionCompareProps {
  documentId: number
  versions: DocumentVersion[]
}

const VersionCompare = ({ documentId, versions }: VersionCompareProps) => {
  const [baseVersion, setBaseVersion] = useState<number | undefined>(undefined)
  const [targetVersion, setTargetVersion] = useState<number | undefined>(undefined)
  const [loading, setLoading] = useState(false)
  const [comparison, setComparison] = useState<DocumentComparison | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleCompare = async () => {
    if (!baseVersion || !targetVersion) {
      setError('Выберите две разные версии')
      return
    }
    if (baseVersion === targetVersion) {
      setError('Версии должны отличаться')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const result = await documentsApi.compareVersions(documentId, baseVersion, targetVersion)
      setComparison(result)
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Не удалось сравнить версии')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card title="Сравнение версий">
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <Space wrap>
          <Select
            placeholder="Базовая версия"
            value={baseVersion}
            onChange={setBaseVersion}
            style={{ width: 160 }}
            options={versions.map((version) => ({
              label: `Версия ${version.version_number}`,
              value: version.version_number,
            }))}
          />
          <Select
            placeholder="Сравниваемая версия"
            value={targetVersion}
            onChange={setTargetVersion}
            style={{ width: 180 }}
            options={versions.map((version) => ({
              label: `Версия ${version.version_number}`,
              value: version.version_number,
            }))}
          />
          <Button type="primary" onClick={handleCompare} disabled={loading}>
            Сравнить
          </Button>
        </Space>

        {loading && (
          <div style={{ textAlign: 'center', padding: 24 }}>
            <Spin />
          </div>
        )}

        {error && <Alert type="error" showIcon message={error} />}

        {comparison && !loading && (
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Alert
              type={comparison.hash_equal ? 'success' : 'warning'}
              showIcon
              message={comparison.hash_equal ? 'Версии идентичны' : 'Версии отличаются'}
              description={`Разница в размере: ${comparison.size_difference} байт`}
            />
            <Card size="small" title="Информация">
              <Space direction="vertical">
                <Text>Базовая версия: {comparison.base_version.version_number}</Text>
                <Text>Сравниваемая версия: {comparison.target_version.version_number}</Text>
              </Space>
            </Card>
            <Card size="small" title="Diff (первые 200 строк)">
              {comparison.diff_preview.length ? (
                <Paragraph
                  style={{
                    whiteSpace: 'pre-wrap',
                    fontFamily: 'Menlo, monospace',
                    background: '#0d1117',
                    color: '#c9d1d9',
                    padding: 16,
                    borderRadius: 8,
                    maxHeight: 400,
                    overflow: 'auto',
                  }}
                >
                  {comparison.diff_preview.join('\n')}
                </Paragraph>
              ) : (
                <Text type="secondary">Нет текстовых изменений для отображения.</Text>
              )}
            </Card>
          </Space>
        )}
      </Space>
    </Card>
  )
}

export default VersionCompare
