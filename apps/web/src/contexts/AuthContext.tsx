import { createContext, useContext, useEffect, ReactNode } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { authApi } from '@/api/endpoints/auth'
import apiClient from '@/api/client'
import { useAuthStore } from '@/store/slices/authSlice'
import { useToast } from './ToastContext'
import { getUserIdFromToken } from '@/utils/jwt'
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
  const { token, user_id, email, isAuthenticated, isLoading, setAuth, setLoading, clearAuth } = useAuthStore()
  const navigate = useNavigate()
  const { showSuccess } = useToast()

  useEffect(() => {
    // Hydrate from localStorage on mount
    if (typeof window !== 'undefined') {
      const storedToken = localStorage.getItem('auth_token')
      const storedUserId = localStorage.getItem('auth_user_id')
      const storedEmail = localStorage.getItem('auth_email')

      if (storedToken) {
        // Prefer stored user_id/email, fallback to JWT extraction for user_id
        const userId = storedUserId || getUserIdFromToken(storedToken)
        setAuth(storedToken, userId, storedEmail)
      }
    }
    setLoading(false)
  }, [setAuth, setLoading])

  useEffect(() => {
    apiClient.setAuthErrorCallback(() => {
      clearAuth()
      navigate({ to: '/auth/login', search: {}, replace: true })
    })
    return () => apiClient.setAuthErrorCallback(null)
  }, [clearAuth, navigate])

  const login = async (credentials: LoginRequest) => {
    try {
      setLoading(true)
      const response = await authApi.login(credentials)
      // Use user_id and email from response (backend provides these)
      setAuth(response.access_token, response.user_id, response.email)
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
