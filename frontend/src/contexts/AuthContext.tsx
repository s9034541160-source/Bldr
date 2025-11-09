import React, { createContext, useContext, useEffect, useState } from 'react'
import apiClient from '../services/api'
import { useAuthStore } from '../store/authStore'

interface AuthContextType {
  isAuthenticated: boolean
  user: any | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  loading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, user, login: loginStore, logout: logoutStore } = useAuthStore()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Проверка токена при загрузке
    const token = localStorage.getItem('access_token')
    if (token) {
      // Проверка валидности токена через /auth/me
      apiClient.get('/auth/me')
        .then((response) => {
          loginStore(token, response.data)
        })
        .catch(() => {
          localStorage.removeItem('access_token')
        })
        .finally(() => {
          setLoading(false)
        })
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (username: string, password: string) => {
    const formDataEncoded = new URLSearchParams()
    formDataEncoded.append('username', username)
    formDataEncoded.append('password', password)

    const response = await apiClient.post('/auth/login', formDataEncoded, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })

    const { access_token, refresh_token } = response.data
    
    // Получаем информацию о пользователе
    const userResponse = await apiClient.get('/auth/me', {
      headers: {
        Authorization: `Bearer ${access_token}`,
      },
    })
    const user = userResponse.data
    
    localStorage.setItem('access_token', access_token)
    if (refresh_token) {
      localStorage.setItem('refresh_token', refresh_token)
    }
    loginStore(access_token, user)
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    logoutStore()
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

