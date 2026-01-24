/**
 * Authentication Context
 * Provides authentication state and methods. Uses Zustand auth store as source of truth.
 */

import { createContext, useContext, useEffect, ReactNode } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { authApi } from '@/api/endpoints/auth'
import { useAuthStore } from '@/store/slices/authSlice'
import { useToast } from './ToastContext'
import type { LoginRequest, AuthResponse } from '@/api/types'

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
  const { showSuccess, showError } = useToast()

  useEffect(() => {
    const checkAuth = () => {
      const storedToken = authApi.getToken()
      if (storedToken) {
        setAuth(storedToken)
      }
      setLoading(false)
    }
    checkAuth()
  }, [setAuth, setLoading])

  const login = async (credentials: LoginRequest) => {
    try {
      setLoading(true)
      const response: AuthResponse = await authApi.login(credentials)
      setAuth(response.access_token)
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
