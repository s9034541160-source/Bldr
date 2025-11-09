import { create } from 'zustand'

interface AuthState {
  isAuthenticated: boolean
  user: any | null
  login: (token: string, user: any) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  user: null,
  login: (token: string, user: any) => {
    localStorage.setItem('access_token', token)
    set({ isAuthenticated: true, user })
  },
  logout: () => {
    localStorage.removeItem('access_token')
    set({ isAuthenticated: false, user: null })
  },
}))

