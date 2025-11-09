import { Layout, Input, Badge, Avatar, Dropdown, MenuProps } from 'antd'
import { BellOutlined, SearchOutlined, UserOutlined } from '@ant-design/icons'

const { Header: AntHeader } = Layout

const Header = () => {
  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      label: 'Профиль',
    },
    {
      key: 'settings',
      label: 'Настройки',
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      label: 'Выход',
    },
  ]

  return (
    <AntHeader style={{ padding: '0 24px', background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      <Input
        placeholder="Поиск..."
        prefix={<SearchOutlined />}
        style={{ width: 300 }}
      />
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <Badge count={5}>
          <BellOutlined style={{ fontSize: 20, cursor: 'pointer' }} />
        </Badge>
        <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
          <Avatar icon={<UserOutlined />} style={{ cursor: 'pointer' }} />
        </Dropdown>
      </div>
    </AntHeader>
  )
}

export default Header

