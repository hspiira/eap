import { createContext, useContext, useEffect, ReactNode } from 'react'
import { useNavigate } from '@tanstack/react-router'
import apiClient from '@/api/client'
import { useAuthStore } from '@/store/slices/authSlice'
import { useToast } from './ToastContext'
import { authActions } from '@/lib/auth-store'
import type { LoginRequest } from '@/api/types'

interface AuthContextType {
  isAuthenticated: boolean
  isLoading: boolean
  login: (credentials: LoginRequest) => Promise<void>
  logout: () => void
  token: string | null
  user_id: string | null
  email: string | null
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const { token, user_id, email, isAuthenticated, isLoading, clearAuth } = useAuthStore()
  const navigate = useNavigate()
  const { showSuccess } = useToast()

  useEffect(() => {
    authActions.initAuth()
  }, [])

  useEffect(() => {
    apiClient.setAuthErrorCallback(() => {
      clearAuth()
      const path =
        typeof window !== 'undefined' ? window.location.pathname : '/'
      const redirectPath =
        path && path !== '/auth/login' && path !== '/auth/signup' ? path : undefined
      navigate({
        to: '/auth/login',
        search: redirectPath ? { redirect: redirectPath } : {},
        replace: true,
      })
    })
    return () => apiClient.setAuthErrorCallback(null)
  }, [clearAuth, navigate])

  const login = async (credentials: LoginRequest) => {
    await authActions.login(credentials)
    showSuccess('Successfully signed in')
    navigate({ to: '/', search: {} })
  }

  const logout = () => {
    authActions.logout()
    showSuccess('Successfully signed out')
    navigate({ to: '/auth/login', search: {} })
  }

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        isLoading,
        login,
        logout,
        token,
        user_id,
        email,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
