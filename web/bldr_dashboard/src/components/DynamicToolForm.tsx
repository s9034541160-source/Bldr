import React from 'react';
import { Form, Input, Select, Switch, Slider, InputNumber, Upload, Button, Space } from 'antd';

type ToolParam = {
  name: string;
  type: string;
  required?: boolean;
  default?: any;
  description?: string;
  enum?: any[];
  ui?: Record<string, any>;
};

const DynamicToolForm: React.FC<{
  params?: ToolParam[];
  value: Record<string, any>;
  onChange: (v: Record<string, any>) => void;
}> = ({ params, value, onChange }) => {
  // Защита от undefined/null params
  const safeParams = Array.isArray(params) ? params : [];
  const [form] = Form.useForm();

  const handleValuesChange = (_: any, all: any) => {
    onChange(all || {});
  };

  const updateParameter = (key: string, val: any) => {
    const newValue = { ...value, [key]: val };
    onChange(newValue);
  };

  const renderField = (p: ToolParam) => {
    const fieldId = `field-${p.name}`; // !!! ИСПРАВЛЕНИЕ: Добавляем уникальный ID !!!
    const common = { 
      name: p.name, 
      label: p.name, 
      tooltip: p.description,
      htmlFor: fieldId // !!! ИСПРАВЛЕНИЕ: Добавляем htmlFor для label !!!
    } as any;
    const requiredRule = p.required ? [{ required: true, message: `Parameter ${p.name} is required` }] : [];
    const currentValue = value[p.name] !== undefined ? value[p.name] : p.default;
    const ui = p.ui || {};
    
    switch (p.type) {
      case 'string':
        return (
          <Form.Item key={p.name} {...common} rules={requiredRule}>
            <Input 
              id={fieldId} // !!! ИСПРАВЛЕНИЕ: Добавляем id для label for !!!
              value={currentValue} 
              onChange={(e) => updateParameter(p.name, e.target.value)}
              placeholder={ui.placeholder}
              maxLength={ui.maxLength}
              rows={ui.rows}
              style={{
                background: 'rgba(24, 144, 255, 0.1)',
                border: '1px solid rgba(24, 144, 255, 0.3)',
                color: 'white',
                borderRadius: '6px',
                height: '40px'
              }}
            />
          </Form.Item>
        );
      case 'number':
        return (
          <Form.Item key={p.name} {...common} rules={requiredRule}>
            {ui.slider ? (
              <Slider
                id={fieldId} // !!! ИСПРАВЛЕНИЕ: Добавляем id для label for !!!
                min={ui.min || 0}
                max={ui.max || 100}
                step={ui.step || 1}
                value={currentValue}
                onChange={(v) => updateParameter(p.name, v)}
                marks={ui.marks}
              />
            ) : (
              <InputNumber 
                id={fieldId} // !!! ИСПРАВЛЕНИЕ: Добавляем id для label for !!!
                style={{ 
                  width: '100%',
                  background: 'rgba(24, 144, 255, 0.1)',
                  border: '1px solid rgba(24, 144, 255, 0.3)',
                  color: 'white',
                  borderRadius: '6px',
                  height: '40px'
                }} 
                value={currentValue} 
                onChange={(v) => updateParameter(p.name, v)}
                min={ui.min}
                max={ui.max}
                step={ui.step}
              />
            )}
          </Form.Item>
        );
      case 'boolean':
        return (
          <Form.Item key={p.name} {...common} valuePropName="checked">
            <Switch 
              id={fieldId} // !!! ИСПРАВЛЕНИЕ: Добавляем id для label for !!!
              checked={!!currentValue} 
              onChange={(checked) => updateParameter(p.name, checked)}
              style={{
                background: currentValue ? '#1890ff' : 'rgba(255, 255, 255, 0.2)'
              }}
            />
          </Form.Item>
        );
      case 'enum':
        return (
          <Form.Item key={p.name} {...common} rules={requiredRule}>
            <Select 
              id={fieldId} // !!! ИСПРАВЛЕНИЕ: Добавляем id для label for !!!
              options={(p.enum||[]).map(v=>({ value:v.value, label:v.label }))} 
              value={currentValue} 
              onChange={(v) => updateParameter(p.name, v)}
              mode={ui.multiple ? 'multiple' : undefined}
              searchable={ui.searchable}
              style={{
                background: 'rgba(24, 144, 255, 0.1)',
                border: '1px solid rgba(24, 144, 255, 0.3)',
                color: 'white',
                borderRadius: '6px',
                height: '40px'
              }}
            />
          </Form.Item>
        );
      case 'array':
        return (
          <Form.Item key={p.name} {...common} rules={requiredRule}>
            <Select 
              id={fieldId} // !!! ИСПРАВЛЕНИЕ: Добавляем id для label for !!!
              mode="multiple"
              value={currentValue || []}
              onChange={(v) => updateParameter(p.name, v)}
              options={(p.enum||[]).map(v=>({ value:v.value, label:v.label }))}
              searchable={ui.searchable}
              style={{
                background: 'rgba(24, 144, 255, 0.1)',
                border: '1px solid rgba(24, 144, 255, 0.3)',
                color: 'white',
                borderRadius: '6px',
                height: '40px'
              }}
            />
          </Form.Item>
        );
      case 'file':
        return (
          <Form.Item key={p.name} {...common} valuePropName="fileList" getValueFromEvent={(e:any)=>e?.fileList}>
            <Upload 
              id={fieldId} 
              beforeUpload={() => false} 
              multiple={ui.multiple || false}
              directory={ui.directory || false}
              showUploadList={{
                showPreviewIcon: true,
                showRemoveIcon: true,
                showDownloadIcon: true
              }}
              style={{
                width: '100%'
              }}
            >
              <Button 
                style={{
                  width: '100%',
                  height: '40px',
                  background: 'rgba(24, 144, 255, 0.1)',
                  border: '1px solid rgba(24, 144, 255, 0.3)',
                  color: '#1890ff',
                  borderRadius: '6px',
                  fontWeight: '500'
                }}
                icon={<span>📁</span>}
              >
                {ui.multiple ? 'Выбрать файлы' : ui.directory ? 'Выбрать папку' : 'Выбрать файл'}
              </Button>
            </Upload>
          </Form.Item>
        );
      default:
        return <Form.Item key={p.name} {...common}><Input id={fieldId} value={currentValue} onChange={(e) => updateParameter(p.name, e.target.value)} /></Form.Item>;
    }
  };

  // DEBUG: Log the params to see what we're getting
  console.log('[DynamicToolForm] Rendering with params:', safeParams);
  console.log('[DynamicToolForm] Current value:', value);
  console.log('[DynamicToolForm] Params count:', safeParams.length);
  console.log('[DynamicToolForm] Params types:', safeParams.map(p => `${p.name}:${p.type}`));
  
  // Защита от ошибки при сворачивании панели
  if (!safeParams || safeParams.length === 0) {
    return (
      <div style={{ 
        color: '#1890ff', 
        padding: '16px', 
        background: 'rgba(24, 144, 255, 0.1)', 
        border: '1px solid rgba(24, 144, 255, 0.3)',
        borderRadius: '8px',
        textAlign: 'center'
      }}>
        <p>🔧 Инструмент загружается...</p>
      </div>
    );
  }
  
  // Отладочная информация в UI
  if (safeParams.length === 0) {
    return (
      <div style={{ color: '#ff4d4f', padding: '16px', background: '#2a1810', border: '1px solid #ff4d4f' }}>
        <h4>⚠️ No parameters found</h4>
        <p>Params: {JSON.stringify(params)}</p>
        <p>This tool may not have configurable parameters.</p>
      </div>
    );
  }

  return (
    <Form 
      form={form} 
      layout="vertical" 
      initialValues={value} 
      onValuesChange={handleValuesChange}
      style={{
        background: 'transparent',
        color: 'white'
      }}
      labelCol={{ style: { color: 'white', fontWeight: '500' } }}
      wrapperCol={{ style: { color: 'white' } }}
    >
      {safeParams.map(renderField)}
    </Form>
  );
};

export default DynamicToolForm;
