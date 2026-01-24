/**
 * Authentication Context
 * Provides authentication state and methods. Uses Zustand auth store as source of truth.
 */

import { createContext, useContext, useEffect, ReactNode } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { authApi } from '@/api/endpoints/auth'
import apiClient from '@/api/client'
import { useAuthStore } from '@/store/slices/authSlice'
import { useToast } from './ToastContext'
import type { LoginRequest } from '@/api/types'

interface AuthContextType {
  isAuthenticated: boolean
  isLoading: boolean
  login: (credentials: LoginRequest) => Promise<void>
  logout: () => void
  token: string | null
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const { token, isAuthenticated, isLoading, setAuth, setLoading, clearAuth } = useAuthStore()
  const navigate = useNavigate()
  const { showSuccess } = useToast()

  // Sync store with apiClient/localStorage (store already hydrated from localStorage in authSlice).
  useEffect(() => {
    const storedToken = authApi.getToken()
    if (storedToken) setAuth(storedToken)
    setLoading(false)
  }, [setAuth, setLoading])

  const login = async (credentials: LoginRequest) => {
    try {
      setLoading(true)
      const response = await authApi.login(credentials)
      setAuth(response.access_token)
      if (response.tenant_id) {
        if (typeof window !== 'undefined') {
          localStorage.setItem('current_tenant_id', response.tenant_id)
        }
        apiClient.setTenantId(response.tenant_id)
      }
      showSuccess('Successfully signed in')
      navigate({ to: '/', search: {} })
    } catch (error) {
      clearAuth()
      throw error
    } finally {
      setLoading(false)
    }
  }

  const logout = () => {
    authApi.logout()
    clearAuth()
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
