import React, { useEffect, useState } from 'react';
import { Card, Form, Input, Button, Select, Table, message, Space, Tag } from 'antd';
import { apiService } from '../services/api';

const { Option } = Select;

interface UserRow {
  username: string;
  role: string;
}

const UserManagement: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [users, setUsers] = useState<UserRow[]>([]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const list = await apiService.listUsers();
      setUsers(list);
    } catch (e: any) {
      message.error(e?.response?.data?.error || 'Ошибка загрузки пользователей');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const onFinish = async (values: any) => {
    if (values.password !== values.confirm) {
      message.error('Пароли не совпадают');
      return;
    }
    try {
      setLoading(true);
      const res = await apiService.createUser(values.username, values.password, values.role);
      if (res?.status === 'error') {
        throw new Error(res?.error || 'Ошибка создания пользователя');
      }
      message.success('Пользователь создан');
      form.resetFields();
      loadUsers();
    } catch (e: any) {
      message.error(e?.response?.data?.detail || e?.message || 'Ошибка создания пользователя');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Card title="Добавить пользователя" size="small" style={{ marginBottom: 16 }}>
        <Form form={form} layout="inline" onFinish={onFinish}>
          <Form.Item name="username" rules={[{ required: true, message: 'Логин обязателен' }]}>
            <Input placeholder="Логин" />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: 'Пароль обязателен' }, { min: 4, message: 'Минимум 4 символа' }]}>
            <Input.Password placeholder="Пароль" />
          </Form.Item>
          <Form.Item name="confirm" rules={[{ required: true, message: 'Повторите пароль' }]}>
            <Input.Password placeholder="Повторите пароль" />
          </Form.Item>
          <Form.Item name="role" initialValue="user">
            <Select style={{ width: 140 }}>
              <Option value="user">user</Option>
              <Option value="admin">admin</Option>
            </Select>
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              Добавить
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title="Пользователи" size="small">
        <Table
          dataSource={users}
          rowKey="username"
          loading={loading}
          pagination={{ pageSize: 10 }}
          columns={[
            { title: 'Логин', dataIndex: 'username', key: 'username' },
            { title: 'Роль', dataIndex: 'role', key: 'role', render: (r: string) => <Tag color={r === 'admin' ? 'red' : 'blue'}>{r}</Tag> },
          ]}
        />
      </Card>
    </div>
  );
};

export default UserManagement;
