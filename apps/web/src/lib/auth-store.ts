/**
 * Auth actions and init — ui.timeline-style flow.
 * Single place for login, logout, initAuth; state lives in authSlice.
 */

import apiClient from '@/api/client'
import { authApi } from '@/api/endpoints/auth'
import { tenantsApi } from '@/api/endpoints/tenants'
import { useAuthStore } from '@/store/slices/authSlice'
import { useTenantStore } from '@/store/slices/tenantSlice'
import type { LoginRequest } from '@/api/types'
import type { Tenant } from '@/types/entities'

function useAuthCookies(): boolean {
  return import.meta.env.VITE_AUTH_USE_COOKIES === 'true'
}

export const authActions = {
  async login(credentials: LoginRequest): Promise<void> {
    const { setAuth, setLoading, setError, clearAuth } = useAuthStore.getState()
    setLoading(true)
    setError(null)

    try {
      const response = await authApi.login(credentials)
      if (useAuthCookies()) {
        setAuth(null, response.user_id, response.email)
      } else {
        setAuth(response.access_token, response.user_id, response.email)
      }
      let tenantId = response.tenant_id
      if (!tenantId && credentials.tenant_code) {
        try {
          const { items } = await tenantsApi.list()
          const tenant = items.find(
            (t: Tenant) => t.code?.toLowerCase() === credentials.tenant_code?.toLowerCase()
          )
          if (tenant) tenantId = tenant.id
        } catch (e) {
          console.warn('Could not resolve tenant by code after login:', e)
        }
      }
      if (tenantId) {
        apiClient.setTenantId(tenantId)
        if (typeof window !== 'undefined') {
          localStorage.setItem('current_tenant_id', tenantId)
        }
        try {
          const tenant = await tenantsApi.getById(tenantId)
          useTenantStore.getState().setCurrentTenant(tenant as Tenant)
        } catch (e) {
          console.warn('Could not load tenant details after login:', e)
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

  async logout(): Promise<void> {
    await authApi.logout()
    useAuthStore.getState().clearAuth()
  },

  async initAuth(): Promise<void> {
    if (useAuthCookies()) {
      const valid = await apiClient.validateSession()
      if (typeof window !== 'undefined') {
        const tid =
          localStorage.getItem('tenant_id') ||
          localStorage.getItem('current_tenant_id')
        if (tid) apiClient.setTenantId(tid)
      }
      if (!valid) {
        useAuthStore.getState().clearAuth()
        useAuthStore.getState().setLoading(false)
        return
      }
      const userId = localStorage.getItem('auth_user_id')
      const email = localStorage.getItem('auth_email')
      useAuthStore.getState().setAuth(null, userId, email)
      useAuthStore.getState().setLoading(false)
      return
    }

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
