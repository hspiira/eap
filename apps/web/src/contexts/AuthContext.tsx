/**
 * Authentication Context
 * Provides authentication state and methods throughout the application
 */

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { authApi } from '@/api/endpoints/auth'
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
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [token, setToken] = useState<string | null>(null)
  const navigate = useNavigate()
  const { showSuccess, showError } = useToast()

  // Check authentication status on mount
  useEffect(() => {
    const checkAuth = () => {
      const storedToken = authApi.getToken()
      if (storedToken) {
        setToken(storedToken)
        setIsAuthenticated(true)
      }
      setIsLoading(false)
    }

    checkAuth()
  }, [])

  const login = async (credentials: LoginRequest) => {
    try {
      setIsLoading(true)
      const response: AuthResponse = await authApi.login(credentials)
      
      setToken(response.access_token)
      setIsAuthenticated(true)
      showSuccess('Successfully signed in')
      
      // Redirect to dashboard or home after successful login
      navigate({ to: '/', search: {} })
    } catch (error) {
      setIsAuthenticated(false)
      setToken(null)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const logout = () => {
    authApi.logout()
    setToken(null)
    setIsAuthenticated(false)
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
