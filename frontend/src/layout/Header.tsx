import { Layout, Input, Badge, Avatar, Dropdown, MenuProps } from 'antd'
import { BellOutlined, SearchOutlined, UserOutlined } from '@ant-design/icons'
import { useAuth } from '../contexts/AuthContext'
import { useNavigate } from 'react-router-dom'

const { Header: AntHeader } = Layout

const Header = () => {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      label: 'Профиль',
      onClick: () => navigate('/profile'),
    },
    {
      key: 'settings',
      label: 'Настройки',
      onClick: () => navigate('/settings'),
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      label: 'Выход',
      onClick: () => {
        logout()
        navigate('/login')
      },
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
          <Avatar 
            icon={<UserOutlined />} 
            style={{ cursor: 'pointer' }}
            src={user?.avatar}
          >
            {user?.full_name?.[0] || user?.username?.[0]}
          </Avatar>
        </Dropdown>
      </div>
    </AntHeader>
  )
}

export default Header
