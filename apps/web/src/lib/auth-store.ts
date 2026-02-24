/**
 * Auth actions and init — ui.timeline-style flow.
 * Single place for login, logout, initAuth; state lives in authSlice.
 */

import apiClient from '@/api/client'
import { authApi } from '@/api/endpoints/auth'
import { useAuthStore } from '@/store/slices/authSlice'
import type { LoginRequest } from '@/api/types'

export const authActions = {
  async login(credentials: LoginRequest): Promise<void> {
    const { setAuth, setLoading, setError, clearAuth } = useAuthStore.getState()
    setLoading(true)
    setError(null)

    try {
      const response = await authApi.login(credentials)
      setAuth(response.access_token, response.user_id, response.email)
      if (response.tenant_id) {
        apiClient.setTenantId(response.tenant_id)
        if (typeof window !== 'undefined') {
          localStorage.setItem('current_tenant_id', response.tenant_id)
        }
      }
      useAuthStore.getState().setLoading(false)
    } catch (error) {
      clearAuth()
      const message =
        error instanceof Error ? error.message : 'Login failed'
      setError(message)
      useAuthStore.getState().setLoading(false)
      throw error
    }
  },

  logout(): void {
    authApi.logout()
    useAuthStore.getState().clearAuth()
  },

  async initAuth(): Promise<void> {
    const token = apiClient.getToken()
    if (!token) {
      useAuthStore.getState().setLoading(false)
      return
    }

    if (typeof window !== 'undefined') {
      const tid =
        localStorage.getItem('tenant_id') ||
        localStorage.getItem('current_tenant_id')
      if (tid) apiClient.setTenantId(tid)
    }

    const userId =
      typeof window !== 'undefined' ? localStorage.getItem('auth_user_id') : null
    const email =
      typeof window !== 'undefined' ? localStorage.getItem('auth_email') : null
    useAuthStore.getState().setAuth(token, userId, email)
    useAuthStore.getState().setLoading(false)
  },

  clearError(): void {
    useAuthStore.getState().clearError()
  },
}
