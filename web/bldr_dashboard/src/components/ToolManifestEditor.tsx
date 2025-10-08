import React from 'react';
import { Modal, Form, Input, Select, Switch, Button, Space, InputNumber, message } from 'antd';

const { TextArea } = Input;

export type ToolParam = {
  name: string;
  type: string;
  required?: boolean;
  default?: any;
  description?: string;
  enum?: any[];
  ui?: Record<string, any>;
};

export type ToolManifestLike = {
  name: string;
  title: string;
  description: string;
  category: string;
  ui_placement: string;
  enabled?: boolean;
  system?: boolean;
  params: ToolParam[];
};

const TYPE_OPTIONS = ['string','number','boolean','file','enum','array','object'];
const PLACEMENT_OPTIONS = ['dashboard','tools','service'];

const ToolManifestEditor: React.FC<{
  manifest: ToolManifestLike;
  onSave: (patch: Partial<ToolManifestLike>) => Promise<void>;
  onCancel: () => void;
  open: boolean;
}> = ({ manifest, onSave, onCancel, open }) => {
  const [form] = Form.useForm();

  const initial = {
    title: manifest.title,
    description: manifest.description,
    category: manifest.category,
    ui_placement: manifest.ui_placement,
    enabled: manifest.enabled !== false,
    params: manifest.params || []
  } as any;

  const onFinish = async (values: any) => {
    // Basic validation
    if (!values.title || !values.category) {
      message.error('Title и category обязательны');
      return;
    }
    // Strip invalid param entries
    const params = (values.params || []).filter((p: any) => p && p.name && p.type);
    await onSave({
      title: values.title,
      description: values.description,
      category: values.category,
      ui_placement: values.ui_placement,
      enabled: values.enabled,
      params
    } as any);
  };

  return (
    <Modal title={`Редактор манифеста: ${manifest.name}`} open={open} onCancel={onCancel} footer={null} width={800}>
      <Form form={form} layout="vertical" initialValues={initial} onFinish={onFinish}>
        <Form.Item label="Title" name="title" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item label="Description" name="description">
          <TextArea rows={3} />
        </Form.Item>
        <Form.Item label="Category" name="category" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item label="UI Placement" name="ui_placement" rules={[{ required: true }]}> 
          <Select options={PLACEMENT_OPTIONS.map(p=>({ value:p, label:p }))} />
        </Form.Item>
        <Form.Item label="Enabled" name="enabled" valuePropName="checked">
          <Switch />
        </Form.Item>

        <Form.List name="params">
          {(fields, { add, remove }) => (
            <div>
              <Space style={{ marginBottom: 8 }}>
                <Button type="dashed" onClick={() => add({ type: 'string', required: false })}>+ Добавить параметр</Button>
              </Space>
              {fields.map((field) => (
                <Space key={field.key} style={{ display: 'flex', marginBottom: 8 }} align="start">
                  <Form.Item {...field} name={[field.name, 'name']} rules={[{ required: true, message: 'name' }]}>
                    <Input placeholder="name" style={{ width: 160 }} />
                  </Form.Item>
                  <Form.Item {...field} name={[field.name, 'type']} rules={[{ required: true, message: 'type' }]}>
                    <Select options={TYPE_OPTIONS.map(t=>({ value:t, label:t }))} style={{ width: 140 }} />
                  </Form.Item>
                  <Form.Item {...field} name={[field.name, 'required']} valuePropName="checked">
                    <Switch />
                  </Form.Item>
                  <Form.Item {...field} name={[field.name, 'default']}>
                    <Input placeholder="default" style={{ width: 160 }} />
                  </Form.Item>
                  <Form.Item {...field} name={[field.name, 'description']}>
                    <Input placeholder="description" style={{ width: 220 }} />
                  </Form.Item>
                  <Button danger onClick={() => remove(field.name)}>Удалить</Button>
                </Space>
              ))}
            </div>
          )}
        </Form.List>

        <Space style={{ marginTop: 12 }}>
          <Button onClick={onCancel}>Отмена</Button>
          <Button type="primary" htmlType="submit">Сохранить манифест</Button>
        </Space>
      </Form>
    </Modal>
  );
};

export default ToolManifestEditor;
