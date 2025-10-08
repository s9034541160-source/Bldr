import React, { useState } from 'react';
import { Card, InputNumber, Switch, Button, Input, message, Typography, Divider, Space, Spin, Select } from 'antd';
import { useEffect, useState as useStateReact } from 'react';
import type { AvailableModel, RoleInfo } from '../services/api';
import { apiService } from '../services/api';

const { Text } = Typography;

const VariantEditor: React.FC<{ index: number; value: any; onChange: (v: any) => void }> = ({ index, value, onChange }) => {
  const v = value || {};
  const coord = v.coordinator || {};
  const [roles, setRoles] = useStateReact<RoleInfo[]>([]);
  const [models, setModels] = useStateReact<AvailableModel[]>([]);

  useEffect(() => {
    (async () => {
      try {
        const r = await apiService.listRoles();
        const m = await apiService.listAvailableModels();
        setRoles(r || []);
        setModels(m?.models || []);
      } catch (e) {
        // ignore
      }
    })();
  }, []);
  return (
    <Card size="small" title={`Вариант ${index}`} style={{ marginBottom: 12 }}>
      <Space direction="vertical" style={{ width: '100%' }}>
        <Input placeholder="Название варианта (например, V1)" value={v.name} onChange={(e) => onChange({ ...v, name: e.target.value })} />
        <Text type="secondary">Переопределения координатора (опционально)</Text>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <div>
            <Text type="secondary">Планирование</Text><br />
            <Switch checked={coord.planning_enabled ?? true} onChange={(val) => onChange({ ...v, coordinator: { ...coord, planning_enabled: val } })} />
          </div>
          <div>
            <Text type="secondary">JSON-планы</Text><br />
            <Switch checked={coord.json_mode_enabled ?? true} onChange={(val) => onChange({ ...v, coordinator: { ...coord, json_mode_enabled: val } })} />
          </div>
          <div>
            <Text type="secondary">Макс. итераций</Text><br />
            <InputNumber min={1} max={5} value={coord.max_iterations ?? 2} onChange={(val) => onChange({ ...v, coordinator: { ...coord, max_iterations: val } })} />
          </div>
          <div>
            <Text type="secondary">Fast-path</Text><br />
            <Switch checked={coord.simple_plan_fast_path ?? true} onChange={(val) => onChange({ ...v, coordinator: { ...coord, simple_plan_fast_path: val } })} />
          </div>
        </div>
        <Text type="secondary">Переназначения моделей (интерактивно)</Text>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {roles.map((r) => {
            const cur = (v.models_overrides?.[r.role] || {}) as any;
            const currentModel = cur.model;
            return (
              <Card key={r.role} size="small" title={r.title || r.role}>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                  <Select
                    style={{ minWidth: 260 }}
                    value={currentModel}
                    placeholder="Модель"
                    onChange={(val) => {
                      const mo = { ...(v.models_overrides || {}) };
                      mo[r.role] = { ...(mo[r.role] || {}), model: val };
                      onChange({ ...v, models_overrides: mo });
                    }}
                    showSearch
                    optionFilterProp="children"
                  >
                    {models.map((m) => (
                      <Select.Option key={`${m.id}@${m.base_url}`} value={m.id}>{m.label} — {m.id}</Select.Option>
                    ))}
                  </Select>
                  <Input
                    style={{ minWidth: 260 }}
                    placeholder="base_url"
                    value={cur.base_url}
                    onChange={(e) => {
                      const mo = { ...(v.models_overrides || {}) };
                      mo[r.role] = { ...(mo[r.role] || {}), base_url: e.target.value };
                      onChange({ ...v, models_overrides: mo });
                    }}
                  />
                  <InputNumber
                    style={{ width: 140 }}
                    min={0}
                    max={1}
                    step={0.1}
                    placeholder="temperature"
                    value={cur.temperature}
                    onChange={(val) => {
                      const mo = { ...(v.models_overrides || {}) };
                      mo[r.role] = { ...(mo[r.role] || {}), temperature: val };
                      onChange({ ...v, models_overrides: mo });
                    }}
                  />
                  <InputNumber
                    style={{ width: 160 }}
                    min={256}
                    max={32768}
                    step={128}
                    placeholder="max_tokens"
                    value={cur.max_tokens}
                    onChange={(val) => {
                      const mo = { ...(v.models_overrides || {}) };
                      mo[r.role] = { ...(mo[r.role] || {}), max_tokens: val };
                      onChange({ ...v, models_overrides: mo });
                    }}
                  />
                </div>
              </Card>
            );
          })}
        </div>
        <Text type="secondary">Переназначения моделей (JSON, опционально)</Text>
        <Input.TextArea rows={4} placeholder='{ "coordinator": { "model": "deepseek/..." } }' value={JSON.stringify(v.models_overrides || {}, null, 2)} onChange={(e) => {
          try {
            const obj = JSON.parse(e.target.value || '{}');
            onChange({ ...v, models_overrides: obj });
          } catch {
            onChange({ ...v, models_overrides: {} });
          }
        }} />
      </Space>
    </Card>
  );
};

const AutoTestPanel: React.FC = () => {
  const [v1, setV1] = useState<any>({ name: 'V1', coordinator: { planning_enabled: true, json_mode_enabled: true, max_iterations: 2, simple_plan_fast_path: true } });
  const [v2, setV2] = useState<any>({ name: 'V2', coordinator: { planning_enabled: true, json_mode_enabled: false, max_iterations: 1, simple_plan_fast_path: true } });
  const [v3, setV3] = useState<any>({ name: 'V3', coordinator: { planning_enabled: false, json_mode_enabled: false, max_iterations: 1, simple_plan_fast_path: true } });
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [files, setFiles] = useState<{ image?: { path: string; name?: string }; audio?: { path: string; name?: string }; document?: { path: string; name?: string } }>({});
  const [queriesText, setQueriesText] = useState<string>('');
  const [elapsed, setElapsed] = useState<number>(0);
  const [timerId, setTimerId] = useState<any>(null);

  const onChooseFile = async (e: React.ChangeEvent<HTMLInputElement>, kind: 'image' | 'audio' | 'document') => {
    const f = e.target.files?.[0];
    if (!f) return;
    try {
      const resp = await apiService.uploadAutotestFile(f, kind);
      setFiles((prev) => ({ ...prev, [kind]: { path: resp.path, name: resp.name } }));
      message.success(`Загружено: ${resp.name}`);
    } catch (err) {
      message.error('Не удалось загрузить файл');
    } finally {
      e.target.value = '';
    }
  };

  const formatTime = (sec: number) => {
    const m = Math.floor(sec / 60).toString().padStart(2, '0');
    const s = (sec % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const run = async () => {
    try {
      setRunning(true);
      const variants = [v1, v2, v3].filter((v) => v && v.name);
      const filesPayload: any = {};
      if (files.image?.path) filesPayload.image = files.image.path;
      if (files.audio?.path) filesPayload.audio = files.audio.path;
      if (files.document?.path) filesPayload.document = files.document.path;
      const queries = (queriesText || '').split('\n').map(q => q.trim()).filter(q => q.length > 0);
      setElapsed(0);
      if (timerId) clearInterval(timerId);
      const id = setInterval(() => setElapsed(prev => prev + 1), 1000);
      setTimerId(id);
      const resp = await apiService.runAutoTest(variants, queries.length ? queries : undefined, filesPayload);
      setResults(resp);
      message.success('Автотест завершён');
    } catch (e) {
      message.error('Ошибка автотеста');
    } finally {
      setRunning(false);
      if (timerId) {
        clearInterval(timerId);
        setTimerId(null);
      }
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 12 }}>
        <div>
          <Text type="secondary">Изображение</Text><br />
          <input type="file" accept="image/*" onChange={(e) => onChooseFile(e as any, 'image')} />
          {files.image?.name && <div><Text type="secondary">{files.image.name}</Text></div>}
        </div>
        <div>
          <Text type="secondary">Аудио</Text><br />
          <input type="file" accept="audio/*" onChange={(e) => onChooseFile(e as any, 'audio')} />
          {files.audio?.name && <div><Text type="secondary">{files.audio.name}</Text></div>}
        </div>
        <div>
          <Text type="secondary">Документ</Text><br />
          <input type="file" accept=".pdf,.doc,.docx,.txt,.xlsx,.xls" onChange={(e) => onChooseFile(e as any, 'document')} />
          {files.document?.name && <div><Text type="secondary">{files.document.name}</Text></div>}
        </div>
      </div>

      <Card size="small" style={{ marginBottom: 12 }}>
        <Text type="secondary">Кастомные текстовые запросы (по одному в строке; если пусто — будут дефолтные)</Text>
        <Input.TextArea rows={4} value={queriesText} onChange={(e) => setQueriesText(e.target.value)} placeholder={`Например:\nНайди актуальный СП по земляным работам\nСделай чек-лист технадзора по монолиту`} />
      </Card>

      <Card size="small" style={{ marginBottom: 12 }}>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
          <div><Text>Прошло: {formatTime(elapsed)}</Text></div>
          <div>
            <Text type="secondary">
              Запланировано кейсов: {(queriesText ? queriesText.split('\n').filter(q=>q.trim()).length : 7) + (files.image?1:0) + (files.audio?1:0) + (files.document?1:0)} × 3 вариантов
            </Text>
          </div>
          {running && <Spin />}
        </div>
      </Card>

      <VariantEditor index={1} value={v1} onChange={setV1} />
      <VariantEditor index={2} value={v2} onChange={setV2} />
      <VariantEditor index={3} value={v3} onChange={setV3} />

      <Button type="primary" onClick={run} disabled={running}>Запустить автотест</Button>
      {running && <div style={{ marginTop: 12 }}><Spin /></div>}

      {results && (
        <div style={{ marginTop: 16 }}>
          <Divider />
          <Text strong>Результаты:</Text>
          {(results.results || []).map((vr: any) => (
            <Card key={vr.variant} title={`Вариант: ${vr.variant}`} style={{ marginTop: 12 }}>
              {(vr.items || []).map((it: any, idx: number) => (
                <div key={idx} style={{ marginBottom: 12 }}>
                  <Text>Q: {it.query}</Text>
                  <div style={{ whiteSpace: 'pre-wrap', background: '#fafafa', padding: 8, borderRadius: 4, marginTop: 4 }}>{String(it.answer || '')}</div>
                </div>
              ))}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default AutoTestPanel;
