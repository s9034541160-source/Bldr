import React from 'react';
import { Form, Input, Select, Switch, InputNumber, Slider, Space, Typography } from 'antd';

interface ToolConfigProps<T = any> {
  value: T;
  onChange: (next: T) => void;
}

// Generate Letter
export const ToolConfigGenerateLetter: React.FC<ToolConfigProps<any>> = ({ value, onChange }) => {
  return (
    <Form layout="vertical">
      <Form.Item label="Получатель">
        <Input value={value?.recipient} onChange={(e) => onChange({ ...value, recipient: e.target.value })} />
      </Form.Item>
      <Form.Item label="Отправитель">
        <Input value={value?.sender} onChange={(e) => onChange({ ...value, sender: e.target.value })} />
      </Form.Item>
      <Form.Item label="Тема">
        <Input value={value?.subject} onChange={(e) => onChange({ ...value, subject: e.target.value })} />
      </Form.Item>
      <Form.Item label="Шаблон (идентификатор)">
        <Input value={value?.template} onChange={(e) => onChange({ ...value, template: e.target.value })} />
      </Form.Item>
    </Form>
  );
};

// Analyze Tender
export const ToolConfigAnalyzeTender: React.FC<ToolConfigProps<any>> = ({ value, onChange }) => {
  return (
    <Form layout="vertical">
      <Form.Item label="URL тендера">
        <Input value={value?.tender_url} onChange={(e) => onChange({ ...value, tender_url: e.target.value })} />
      </Form.Item>
      <Form.Item label="Тип анализа">
        <Select value={value?.analysis_type} onChange={(v) => onChange({ ...value, analysis_type: v })}>
          <Select.Option value="full">Полный</Select.Option>
          <Select.Option value="quick">Быстрый</Select.Option>
        </Select>
      </Form.Item>
      <Form.Item label="Бюджет (лимит)">
        <InputNumber min={0} style={{ width: '100%' }} value={value?.budget_limit}
          onChange={(v) => onChange({ ...value, budget_limit: v })} />
      </Form.Item>
    </Form>
  );
};

// Analyze Image
export const ToolConfigAnalyzeImage: React.FC<ToolConfigProps<any>> = ({ value, onChange }) => {
  return (
    <Form layout="vertical">
      <Form.Item label="Путь к изображению">
        <Input value={value?.image_path} onChange={(e) => onChange({ ...value, image_path: e.target.value })} />
      </Form.Item>
      <Form.Item label="Тип анализа">
        <Select value={value?.analysis_type} onChange={(v) => onChange({ ...value, analysis_type: v })}>
          <Select.Option value="comprehensive">Комплексный</Select.Option>
          <Select.Option value="objects">Объекты</Select.Option>
          <Select.Option value="ocr">Текст (OCR)</Select.Option>
        </Select>
      </Form.Item>
      <Form.Item label="Искать объекты">
        <Switch checked={!!value?.detect_objects} onChange={(v) => onChange({ ...value, detect_objects: v })} />
      </Form.Item>
    </Form>
  );
};

// Calculate Estimate
export const ToolConfigCalculateEstimate: React.FC<ToolConfigProps<any>> = ({ value, onChange }) => {
  return (
    <Form layout="vertical">
      <Form.Item label="Название проекта">
        <Input value={value?.project_name} onChange={(e) => onChange({ ...value, project_name: e.target.value })} />
      </Form.Item>
      <Form.Item label="Регион">
        <Select value={value?.region} onChange={(v) => onChange({ ...value, region: v })}>
          <Select.Option value="moscow">Москва</Select.Option>
          <Select.Option value="spb">Санкт-Петербург</Select.Option>
          <Select.Option value="other">Другой</Select.Option>
        </Select>
      </Form.Item>
      <Form.Item label="Включить ГЭСН">
        <Switch checked={!!value?.includeGESN} onChange={(v) => onChange({ ...value, includeGESN: v })} />
      </Form.Item>
    </Form>
  );
};

// Auto Budget
export const ToolConfigAutoBudget: React.FC<ToolConfigProps<any>> = ({ value, onChange }) => {
  return (
    <Form layout="vertical">
      <Form.Item label="Название проекта">
        <Input value={value?.project_name} onChange={(e) => onChange({ ...value, project_name: e.target.value })} />
      </Form.Item>
      <Form.Item label="Накладные (%)">
        <InputNumber min={0} max={100} style={{ width: '100%' }} value={value?.overheads_percentage}
          onChange={(v) => onChange({ ...value, overheads_percentage: v })} />
      </Form.Item>
      <Form.Item label="Прибыль (%)">
        <InputNumber min={0} max={100} style={{ width: '100%' }} value={value?.profit_percentage}
          onChange={(v) => onChange({ ...value, profit_percentage: v })} />
      </Form.Item>
    </Form>
  );
};

// Search RAG Database
export const ToolConfigSearchRAG: React.FC<ToolConfigProps<any>> = ({ value, onChange }) => {
  return (
    <Form layout="vertical">
      <Form.Item label="Запрос">
        <Input value={value?.query} onChange={(e) => onChange({ ...value, query: e.target.value })} />
      </Form.Item>
      <Form.Item label="k (результатов)">
        <InputNumber min={1} max={100} style={{ width: '100%' }} value={value?.k}
          onChange={(v) => onChange({ ...value, k: v })} />
      </Form.Item>
      <Form.Item label="Типы документов (через запятую)">
        <Input value={(value?.doc_types || []).join(', ')}
          onChange={(e) => onChange({ ...value, doc_types: e.target.value.split(',').map((s) => s.trim()).filter(Boolean) })} />
      </Form.Item>
    </Form>
  );
};

// Text-to-Speech
export const ToolConfigTextToSpeech: React.FC<ToolConfigProps<any>> = ({ value, onChange }) => {
  return (
    <Form layout="vertical">
      <Form.Item label="Текст для озвучивания">
        <Input.TextArea 
          value={value?.text} 
          onChange={(e) => onChange({ ...value, text: e.target.value })} 
          rows={4}
          placeholder="Введите текст, который нужно преобразовать в речь"
        />
      </Form.Item>
      
      <Form.Item label="Провайдер">
        <Select 
          value={value?.provider || 'silero'} 
          onChange={(v) => onChange({ ...value, provider: v })}
        >
          <Select.Option value="silero">Silero TTS</Select.Option>
          <Select.Option value="edge">Microsoft Edge TTS</Select.Option>
          <Select.Option value="elevenlabs">ElevenLabs</Select.Option>
        </Select>
      </Form.Item>
      
      <Form.Item label="Голос">
        <Input 
          value={value?.voice || 'ru-RU-SvetlanaNeural'} 
          onChange={(e) => onChange({ ...value, voice: e.target.value })} 
          placeholder="Голос для синтеза"
        />
      </Form.Item>
      
      <Form.Item label="Язык">
        <Select 
          value={value?.language || 'ru'} 
          onChange={(v) => onChange({ ...value, language: v })}
        >
          <Select.Option value="ru">Русский</Select.Option>
          <Select.Option value="en">English</Select.Option>
        </Select>
      </Form.Item>
      
      <Form.Item label="Формат">
        <Select 
          value={value?.format || 'mp3'} 
          onChange={(v) => onChange({ ...value, format: v })}
        >
          <Select.Option value="mp3">MP3</Select.Option>
          <Select.Option value="ogg">OGG</Select.Option>
        </Select>
      </Form.Item>
    </Form>
  );
};